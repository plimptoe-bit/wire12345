"""Accessory cascade (procedure Part 5, step 6; lesson 2).

Specs cascade to parts the drawing omits: seals, wedgelocks/TPAs, blind plugs,
boots, shield barrels, fixation elements, ferrules, heat-shrink. Rules live on
the part records as `required_accessories`:

    {"when": "always|shielded_termination|sealed_termination|empty_cavity|per_housing",
     "mpn": "...", "qty_per": 1, "citation": {...}}

taken from the application spec's component table, with the citation carried
into every output row.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..model import ProgramData
from ..sources import Citation
from .findings import Finding


@dataclass
class CascadeAddition:
    harness: str
    mpn: str
    qty_per_harness: float
    trigger: str              # termination/node id that required it
    when: str
    required_by: str          # part whose spec requires it
    citation: Citation = field(default_factory=Citation)
    on_customer_bom: bool = False
    note: str = "added — not on customer BOM"


def _rules_for(part) -> list[dict]:
    return part.required_accessories if part else []


def compute_additions(prog: ProgramData) -> list[CascadeAddition]:
    adds: list[CascadeAddition] = []
    for h in prog.harnesses:
        # per-termination rules from the terminal and the housing specs
        for t in h.terminations:
            # parts already explicit on the drawing at this joint, including a
            # shield part modeled as the termination's own terminal
            already = set(t.accessories) | ({t.terminal_mpn} if t.terminal_mpn
                                            else set())
            for src_part in (prog.part(t.terminal_mpn), prog.part(t.housing_mpn)):
                for rule in _rules_for(src_part):
                    when = rule.get("when", "always")
                    hit = (
                        when == "always"
                        or (when == "shielded_termination" and t.shielded)
                        or (when == "sealed_termination" and t.sealed)
                    )
                    if hit and rule["mpn"] not in already:
                        adds.append(CascadeAddition(
                            harness=h.drawing_number, mpn=rule["mpn"],
                            qty_per_harness=rule.get("qty_per", 1),
                            trigger=t.id, when=when, required_by=src_part.mpn,
                            citation=Citation.from_dict(rule.get("citation")),
                        ))
        # per-housing rules: wedgelocks/TPAs, blind plugs for empty cavities
        for n in h.nodes:
            hous = prog.part(n.housing_mpn) if n.kind == "connector" else None
            if not hous:
                continue
            used = {t.cavity for t in h.terminations_at(n.id) if t.cavity}
            listed = set()
            for t in h.terminations_at(n.id):
                listed |= set(t.accessories)
            empty = max(0, (hous.cavities or 0) - len(used))
            for rule in _rules_for(hous):
                when = rule.get("when", "always")
                if when == "per_housing" and rule["mpn"] not in listed:
                    adds.append(CascadeAddition(
                        harness=h.drawing_number, mpn=rule["mpn"],
                        qty_per_harness=rule.get("qty_per", 1),
                        trigger=n.id, when=when, required_by=hous.mpn,
                        citation=Citation.from_dict(rule.get("citation")),
                    ))
                elif when == "empty_cavity" and empty > 0:
                    adds.append(CascadeAddition(
                        harness=h.drawing_number, mpn=rule["mpn"],
                        qty_per_harness=empty * rule.get("qty_per", 1),
                        trigger=n.id, when=when, required_by=hous.mpn,
                        citation=Citation.from_dict(rule.get("citation")),
                    ))
    return _merge(adds)


def _merge(adds: list[CascadeAddition]) -> list[CascadeAddition]:
    merged: dict[tuple, CascadeAddition] = {}
    for a in adds:
        key = (a.harness, a.mpn, a.when, a.required_by)
        if key in merged:
            merged[key].qty_per_harness += a.qty_per_harness
            merged[key].trigger += "," + a.trigger
        else:
            merged[key] = a
    return list(merged.values())


def check_against_bom(prog: ProgramData, adds: list[CascadeAddition]) -> list[Finding]:
    """Flag spec-required accessories missing from the customer BOM (lesson 2)."""
    out: list[Finding] = []
    bom_mpns = {b.mpn_as_written for b in prog.customer_bom}
    i = 0
    for a in adds:
        a.on_customer_bom = a.mpn in bom_mpns
        if a.on_customer_bom:
            a.note = "spec-required; present on customer BOM"
            continue
        i += 1
        out.append(Finding(
            id=f"CAS{i:03d}", severity="warning", check="accessory_cascade",
            harness=a.harness, ref=a.trigger, lesson="lesson-2",
            message=(f"Spec for {a.required_by} requires {a.mpn} "
                     f"(x{a.qty_per_harness:g} per harness, rule '{a.when}') — "
                     "not on customer BOM; added to our BOM"),
            citations=[a.citation],
            proposed_default="Add to BOM and notify customer of the quantity impact.",
        ))
    return out


def additions_per_set(prog: ProgramData, adds: list[CascadeAddition]) -> dict[str, float]:
    per_set: dict[str, float] = {}
    for a in adds:
        h = prog.harness(a.harness)
        per_set[a.mpn] = per_set.get(a.mpn, 0) + a.qty_per_harness * h.qty_per_set
    return per_set
