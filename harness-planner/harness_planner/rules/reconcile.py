"""Reconciliation checks (procedure Part 5, steps 2–3; lessons 1 and 3).

Counts come from the harness structure (rules.quantities); the customer BOM is
compared against them. Any mismatch is an open item, never a silent fix.
"""
from __future__ import annotations

from ..model import ProgramData
from .findings import Finding
from .quantities import demand_per_set
from .cascade import CascadeAddition, additions_per_set

_counter = 0


def _fid(prefix="R") -> str:
    global _counter
    _counter += 1
    return f"{prefix}{_counter:03d}"


def reset_counter():
    global _counter
    _counter = 0


# --------------------------------------------------------------------------- #
# Lesson 1: a connector call-out may be a pre-terminated assembly


def check_preterminated(prog: ProgramData) -> list[Finding]:
    out: list[Finding] = []
    contacts_checked: set[str] = set()  # one contacts check per assembly
    for b in prog.customer_bom:
        p = prog.part(b.mpn_as_written)
        if not p or p.category != "preterminated_assembly":
            continue
        desc = (b.description_as_written or "").lower()
        called_connector = any(w in desc for w in ("connector", "plug", "header",
                                                   "receptacle")) \
            and not any(w in desc for w in ("assembly", "cable", "jumper", "pigtail"))
        if called_connector:
            out.append(Finding(
                id=_fid(), severity="blocker", check="preterminated_assembly",
                ref=b.line, lesson="lesson-1",
                message=(f"BOM line {b.line} calls {p.mpn} a connector "
                         f"(\"{b.description_as_written}\") but the manufacturer "
                         f"document shows it is a factory-terminated cable assembly"),
                citations=[p.source],
                proposed_default=("Treat as a bought assembly (cut in half where the "
                                  "drawing uses one end); drop the loose contacts and "
                                  "bulk wire listed for it."),
            ))
        # loose contacts/wire listed although the assembly already carries them
        if p.mpn in contacts_checked:
            continue
        contacts_checked.add(p.mpn)
        ends = p.attrs.get("ends", [])
        end_families = set()
        for e in ends:
            ep = prog.part(e)
            if ep and (ep.contact_family or ep.family):
                end_families.add(ep.contact_family or ep.family)
        if not end_families:
            continue
        per_set = demand_per_set(prog)
        for b2 in prog.customer_bom:
            p2 = prog.part(b2.mpn_as_written)
            if not p2 or p2.category != "terminal":
                continue
            fam = p2.contact_family or p2.family
            if fam in end_families and per_set.get(p2.mpn, 0) == 0:
                out.append(Finding(
                    id=_fid(), severity="blocker", check="preterminated_assembly",
                    ref=b2.line, lesson="lesson-1",
                    message=(f"BOM line {b2.line} lists loose contacts {p2.mpn} "
                             f"(family {fam}) but every {fam} termination on the "
                             f"program comes factory-terminated on {p.mpn} — "
                             "contacts are not needed"),
                    citations=[p.source, p2.source],
                    proposed_default="Remove the contacts (and their wire) from the buy.",
                ))
    return out


# --------------------------------------------------------------------------- #
# Cavity fill: count cavities, name what fills each one


def check_cavity_fill(prog: ProgramData) -> list[Finding]:
    out: list[Finding] = []
    for h in prog.harnesses:
        for n in h.nodes:
            hous = prog.part(n.housing_mpn) if n.kind == "connector" else None
            if not hous or hous.cavities is None:
                continue
            terms = h.terminations_at(n.id)
            if terms and all(t.ttype == "preterminated" for t in terms):
                continue  # factory-terminated end: cavity fill is the supplier's
            cavs = [t.cavity for t in terms if t.cavity]
            dup = {c for c in cavs if cavs.count(c) > 1}
            if dup:
                out.append(Finding(
                    id=_fid(), severity="blocker", check="cavity_fill",
                    harness=h.drawing_number, ref=n.id,
                    message=(f"Cavities {sorted(dup)} of {hous.mpn} at {n.id} are "
                             "assigned to more than one termination"),
                    citations=[h.citation],
                    proposed_default="Re-read the wire table; confirm cavity map.",
                ))
            used = len(set(cavs))
            if used > hous.cavities:
                out.append(Finding(
                    id=_fid(), severity="blocker", check="cavity_fill",
                    harness=h.drawing_number, ref=n.id,
                    message=(f"{used} cavities used at {n.id} but housing {hous.mpn} "
                             f"has only {hous.cavities}"),
                    citations=[hous.source, h.citation],
                    proposed_default="Confirm housing variant / cavity count.",
                ))
            empty = hous.cavities - used
            plugs_required = any(r.get("when") == "empty_cavity"
                                 for r in hous.required_accessories)
            if empty > 0 and not plugs_required:
                sealed_housing = hous.seal_range_mm is not None or \
                    hous.attrs.get("sealed", False)
                out.append(Finding(
                    id=_fid(), severity="warning" if sealed_housing else "info",
                    check="cavity_fill",
                    harness=h.drawing_number, ref=n.id,
                    message=(f"{empty} empty cavities at {n.id} ({hous.mpn}); "
                             "no blind-plug rule found in the spec extract"
                             + (" — sealed housing, plugs likely required"
                                if sealed_housing else "")),
                    citations=[hous.source],
                    proposed_default="Check the application spec for cavity plugs.",
                ))
    return out


# --------------------------------------------------------------------------- #
# BOM quantities vs structure (lesson 3)


def check_bom_quantities(prog: ProgramData,
                         adds: list[CascadeAddition] | None = None) -> list[Finding]:
    out: list[Finding] = []
    expected = demand_per_set(prog)
    for mpn, q in additions_per_set(prog, adds or []).items():
        expected[mpn] = expected.get(mpn, 0) + q

    # normalize the customer BOM to per-set quantities
    bom_per_set: dict[str, float] = {}
    for b in prog.customer_bom:
        qty = b.qty
        if b.basis == "per_harness":
            try:
                qty *= prog.harness(b.harness).qty_per_set if b.harness else 1
            except KeyError:
                out.append(Finding(
                    id=_fid(), severity="warning", check="bom_reconcile", ref=b.line,
                    message=f"BOM line {b.line} references unknown harness {b.harness}",
                    citations=[b.citation],
                    proposed_default="Ask customer which harness the line belongs to."))
        bom_per_set[b.mpn_as_written] = bom_per_set.get(b.mpn_as_written, 0) + qty

    # unresolved placeholders ("tape, see drawing")
    for b in prog.customer_bom:
        if b.mpn_as_written not in prog.parts:
            out.append(Finding(
                id=_fid(), severity="warning", check="bom_reconcile", ref=b.line,
                message=(f"BOM line {b.line} '{b.mpn_as_written}' "
                         f"({b.description_as_written}) does not resolve to a known "
                         "part — placeholder or typo"),
                citations=[b.citation],
                proposed_default="Ask customer for the exact MPN; carry as consumable "
                                 "allowance meanwhile."))

    all_mpns = set(expected) | (set(bom_per_set) & set(prog.parts))
    for mpn in sorted(all_mpns):
        part = prog.part(mpn)
        exp, bom = expected.get(mpn, 0.0), bom_per_set.get(mpn, 0.0)
        if part and part.uom == "m":
            if bom and abs(exp - bom) / max(exp, bom) > 0.10:
                out.append(Finding(
                    id=_fid(), severity="warning", check="bom_reconcile", ref=mpn,
                    message=(f"{mpn}: drawing geometry needs {exp:.2f} m per set, "
                             f"customer BOM lists {bom:.2f} m"),
                    citations=[part.source],
                    proposed_default="Use geometry-derived length plus scrap; flag to "
                                     "customer."))
            continue
        if abs(exp - bom) > 1e-6:
            sev = "blocker" if (part and part.category in
                                ("terminal", "housing", "preterminated_assembly",
                                 "connector_module")) else "warning"
            lesson = "lesson-3" if (part and part.category in
                                    ("terminal", "connector_module")) else None
            if bom == 0:
                msg = (f"{mpn}: structure + specs need {exp:g} per set but the part "
                       "is not on the customer BOM")
            elif exp == 0:
                msg = (f"{mpn}: customer BOM lists {bom:g} per set but the harness "
                       "structure consumes none — spares, error, or a second "
                       "termination the drawing doesn't show")
            else:
                msg = (f"{mpn}: customer BOM lists {bom:g} per set, harness structure "
                       f"needs {exp:g}")
            out.append(Finding(
                id=_fid(), severity=sev, check="bom_reconcile", ref=mpn, lesson=lesson,
                message=msg,
                citations=[part.source] if part else [],
                proposed_default=("Plan to the structure-derived count; confirm the "
                                  "difference with the customer before ordering."),
            ))
    return out
