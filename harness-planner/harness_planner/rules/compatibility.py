"""Pairwise compatibility checks (procedure Part 5, step 5).

Every failure is a Finding with the governing document cited — never a silent
fix. Checks run per termination, plus program-level MOQ checks.
"""
from __future__ import annotations

from ..model import Part, ProgramData
from ..sources import Citation
from .findings import Finding
from .quantities import demand_per_set

_counter = 0


def _fid() -> str:
    global _counter
    _counter += 1
    return f"F{_counter:03d}"


def reset_counter():
    global _counter
    _counter = 0


def _in(v: float, rng: tuple[float, float] | None, tol: float = 1e-9):
    if rng is None:
        return None  # unknown
    return rng[0] - tol <= v <= rng[1] + tol


def _wire_od(part: Part) -> tuple[float, float] | None:
    r = part.insulation_od_range_mm
    if r:
        return r
    od = part.attrs.get("insulation_od_mm")
    return (od, od) if od else None


def _part_cit(part: Part | None) -> list[Citation]:
    return [part.source] if part else []


def check_all(prog: ProgramData) -> list[Finding]:
    out: list[Finding] = []
    for h in prog.harnesses:
        for t in h.terminations:
            seg = h.segment(t.segment)
            wire = prog.part(seg.part_mpn)
            term = prog.part(t.terminal_mpn)
            hous = prog.part(t.housing_mpn)
            ctx = dict(harness=h.drawing_number, ref=t.id)

            if wire is None:
                continue
            # pre-terminated segments carry no loose-piece termination checks
            if t.ttype == "preterminated":
                continue

            out += _check_wire_vs_terminal(t, wire, term, ctx)
            out += _check_seal(t, wire, term, hous, ctx, prog)
            out += _check_family_keying(t, term, hous, ctx)
            out += _check_shield(t, wire, prog, ctx)
            out += _check_coax(t, wire, hous, ctx)
            out += _check_solder(t, wire, hous, term, ctx)
    out = _dedupe(out)
    out += _check_moq(prog)
    return out


def _dedupe(findings: list[Finding]) -> list[Finding]:
    """The same part pairing fails identically on every termination that uses
    it; collapse to one finding listing all affected termination ids."""
    merged: dict[tuple, Finding] = {}
    for f in findings:
        key = (f.check, f.harness, f.message)
        if key in merged:
            m = merged[key]
            if f.ref and f.ref not in (m.ref or ""):
                m.ref = f"{m.ref},{f.ref}"
        else:
            merged[key] = f
    return list(merged.values())


# --------------------------------------------------------------------------- #
def _check_wire_vs_terminal(t, wire: Part, term: Part | None, ctx) -> list[Finding]:
    out = []
    if term is None:
        return out
    cond = wire.conductor_mm2
    wr = term.wire_range_mm2
    if cond is not None and wr is not None and not _in(cond, wr):
        out.append(Finding(
            id=_fid(), severity="blocker", check="wire_range",
            message=(f"Conductor {cond} mm² of {wire.mpn} is outside terminal "
                     f"{term.mpn} wire range {wr[0]}–{wr[1]} mm²"),
            citations=[term.source, wire.source], lesson="lesson-4",
            proposed_default=("Ask customer to substitute a terminal validated for "
                              f"{cond} mm², or change the wire; do not build as drawn."),
            **ctx))

    # plating validated only for certain wire sizes (product spec)
    combos = term.validated_combinations if term else []
    if cond is not None and combos:
        plating = term.plating
        ok = any(
            (c.get("plating") in (None, plating))
            and _in(cond, (c["wire_mm2_range"][0], c["wire_mm2_range"][1]))
            for c in combos)
        if not ok:
            out.append(Finding(
                id=_fid(), severity="blocker", check="plating_validation",
                message=(f"Terminal {term.mpn} ({plating} plating) is not validated "
                         f"for {cond} mm² wire per its product spec; validated "
                         f"combinations: {combos}"),
                citations=[term.source, wire.source], lesson="lesson-4",
                proposed_default=("Use the plating variant the spec validates for this "
                                  "wire size (customer drawing change)."),
                **ctx))

    # insulation OD vs terminal insulation-crimp range (variant selection)
    wod = _wire_od(wire)
    ir = term.insulation_od_range_mm if term else None
    if wod is not None and ir is not None:
        if not (_in(wod[0], ir) and _in(wod[1], ir)):
            out.append(Finding(
                id=_fid(), severity="blocker", check="insulation_od",
                message=(f"Wire {wire.mpn} insulation OD {wod[0]}–{wod[1]} mm is outside "
                         f"terminal {term.mpn} insulation range {ir[0]}–{ir[1]} mm"),
                citations=[term.source, wire.source], lesson="lesson-5",
                proposed_default="Select the insulation-range variant of the same terminal "
                                 "(see variant suggestion finding).",
                **ctx))
    return out


def suggest_variant(prog: ProgramData, term: Part, wire: Part) -> Part | None:
    """Find a sibling in the same variant_group whose insulation range fits."""
    wod = _wire_od(wire)
    if not (term and term.variant_group and wod):
        return None
    for p in prog.parts.values():
        if p.mpn == term.mpn or p.variant_group != term.variant_group:
            continue
        ir = p.insulation_od_range_mm
        if ir and _in(wod[0], ir) and _in(wod[1], ir):
            return p
    return None


def _check_seal(t, wire: Part, term, hous, ctx, prog) -> list[Finding]:
    out = []
    if not t.sealed:
        return out
    wod = _wire_od(wire)
    sr = None
    src = []
    # seal range may sit on the housing or on a seal part in accessories
    if hous and hous.seal_range_mm:
        sr, src = hous.seal_range_mm, [hous.source]
    for acc in t.accessories:
        p = prog.part(acc)
        if p and p.category == "seal" and p.seal_range_mm:
            sr, src = p.seal_range_mm, [p.source]
    if wod is not None and sr is not None and not (_in(wod[0], sr) and _in(wod[1], sr)):
        out.append(Finding(
            id=_fid(), severity="blocker", check="seal_range",
            message=(f"Wire {wire.mpn} insulation OD {wod[0]}–{wod[1]} mm is outside the "
                     f"sealing range {sr[0]}–{sr[1]} mm at sealed termination"),
            citations=src + [wire.source],
            proposed_default="Use the seal size for this OD, or confirm an unsealed build.",
            **ctx))
    if wod is None and sr is not None:
        out.append(Finding(
            id=_fid(), severity="warning", check="seal_range",
            message=f"Sealed termination but wire {wire.mpn} insulation OD is unknown — "
                    "get the OD from the wire datasheet (lesson 5)",
            citations=[wire.source], proposed_default="Request wire datasheet.", **ctx))
    return out


def _check_family_keying(t, term: Part | None, hous: Part | None, ctx) -> list[Finding]:
    out = []
    if term and hous:
        tf, hf = term.contact_family or term.family, hous.contact_family
        if tf and hf and tf != hf:
            out.append(Finding(
                id=_fid(), severity="blocker", check="contact_family",
                message=(f"Contact {term.mpn} (family {tf}) does not match housing "
                         f"{hous.mpn} (accepts {hf})"),
                citations=[term.source, hous.source],
                proposed_default="Confirm the correct contact series from the housing "
                                 "customer drawing.", **ctx))
    return out


def _check_shield(t, wire: Part, prog: ProgramData, ctx) -> list[Finding]:
    out = []
    # a pre-terminated assembly carries its cable's shield attribute
    shield = wire.shield
    if t.shielded and shield in (None, "none"):
        out.append(Finding(
            id=_fid(), severity="blocker", check="shield_construction",
            message=(f"Termination requires a shield termination but cable "
                     f"{wire.mpn} has no shield"),
            citations=[wire.source],
            proposed_default="Confirm cable construction from datasheet.", **ctx))
    # a shield termination part must support the cable's shield type
    for acc in t.accessories:
        p = prog.part(acc)
        if p and p.attrs.get("shield_types"):
            if shield not in p.attrs["shield_types"]:
                out.append(Finding(
                    id=_fid(), severity="blocker", check="shield_construction",
                    message=(f"Shield part {p.mpn} supports {p.attrs['shield_types']} "
                             f"but cable {wire.mpn} shield is '{shield}'"),
                    citations=[p.source, wire.source],
                    proposed_default="Verify the shield part against the cable "
                                     "construction in the application spec.", **ctx))
    return out


def _check_coax(t, wire: Part, hous: Part | None, ctx) -> list[Finding]:
    out = []
    grp = wire.coax_group
    for part in (hous,):
        if part is None:
            continue
        groups = part.attrs.get("cable_groups")
        if grp and groups and grp not in groups:
            out.append(Finding(
                id=_fid(), severity="blocker", check="coax_cable_group",
                message=(f"Coax cable {wire.mpn} (group {grp}) is not in connector "
                         f"{part.mpn} cable groups {groups}"),
                citations=[part.source, wire.source],
                proposed_default="Select the connector variant for this cable group.",
                **ctx))
    return out


def _check_solder(t, wire: Part, hous: Part | None, term: Part | None, ctx) -> list[Finding]:
    out = []
    if t.ttype not in ("solder_cup", "solder_sleeve"):
        return out
    target = term or hous
    if target:
        cup = target.attrs.get("solder_cup_max_mm2")
        if cup is not None and wire.conductor_mm2 and wire.conductor_mm2 > cup:
            out.append(Finding(
                id=_fid(), severity="blocker", check="solder_cup_size",
                message=(f"Conductor {wire.conductor_mm2} mm² exceeds solder cup "
                         f"capacity {cup} mm² of {target.mpn}"),
                citations=[target.source, wire.source],
                proposed_default="Reduce wire size or change connector variant.", **ctx))
        min_temp = target.attrs.get("min_wire_temp_rating_c")
        if (min_temp is not None and wire.temp_rating_c is not None
                and wire.temp_rating_c < min_temp):
            out.append(Finding(
                id=_fid(), severity="blocker", check="solder_temp_rating",
                message=(f"Wire {wire.mpn} insulation rated {wire.temp_rating_c} °C is "
                         f"below the {min_temp} °C minimum for soldering to {target.mpn}"),
                citations=[target.source, wire.source],
                proposed_default="Use higher-temperature insulation or crimp variant.",
                **ctx))
    return out


def _check_moq(prog: ProgramData) -> list[Finding]:
    out = []
    per_set = demand_per_set(prog)
    vols = prog.meta.planned_volumes()
    max_weekly = max(vols) if vols else 0
    horizon_need = {m: q * max_weekly * prog.meta.horizon_weeks
                    for m, q in per_set.items()}
    for mpn, need in horizon_need.items():
        p = prog.part(mpn)
        if not p or p.consigned:
            continue
        if p.moq and need > 0 and p.moq > 4 * need:
            out.append(Finding(
                id=_fid(), severity="info", check="moq_vs_need",
                message=(f"{mpn}: MOQ {p.moq:g} {p.uom} is more than 4x the horizon "
                         f"need of {need:g} {p.uom} — excess stock / NCNR risk"),
                citations=[p.source],
                proposed_default="Quote broker/cut-tape options or ask customer to consign.",
                ref=mpn))
    return out
