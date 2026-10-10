"""Quantity rollup: what the harness structure actually consumes.

This is the single place quantities are computed from, so the BOM, the
reconciliation and procurement all agree. Origins:
  structure  — implied by nodes/segments/terminations on the drawing
  cascade    — required by a spec but absent from the drawing (rules.cascade)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..model import Harness, ProgramData
from ..sources import Citation


@dataclass
class DemandLine:
    mpn: str
    harness: str            # drawing number
    qty_per_harness: float
    uom: str = "ea"
    origin: str = "structure"   # structure|cascade
    detail: str = ""            # what generated it
    citation: Citation = field(default_factory=Citation)


def _seg_wire_qty(seg, part) -> float:
    """Quantity consumed by one segment, in the part's UoM."""
    if part and part.category == "preterminated_assembly":
        return 0.5 if seg.source == "cut_half" else 1.0
    if part and part.uom == "m":
        return seg.length_mm / 1000.0
    return 1.0


def demand_for_harness(prog: ProgramData, h: Harness) -> list[DemandLine]:
    lines: list[DemandLine] = []

    def add(mpn, qty, detail, citation=None, uom=None):
        part = prog.part(mpn)
        lines.append(DemandLine(
            mpn=mpn, harness=h.drawing_number, qty_per_harness=qty,
            uom=uom or (part.uom if part else "ea"),
            origin="structure", detail=detail,
            citation=citation or (part.source if part else Citation()),
        ))

    # housings: one per connector node with a housing part — except nodes whose
    # terminations are all factory pre-terminated: that housing arrives on the
    # bought assembly and must not be counted again (lesson 1)
    for n in h.nodes:
        if n.kind == "connector" and n.housing_mpn:
            terms = h.terminations_at(n.id)
            if terms and all(t.ttype == "preterminated" for t in terms):
                continue
            add(n.housing_mpn, 1, f"connector node {n.id}", h.citation)

    # segments: wire/cable length or pre-terminated assemblies
    for s in h.segments:
        part = prog.part(s.part_mpn)
        add(s.part_mpn, _seg_wire_qty(s, part),
            f"segment {s.id} ({s.length_mm:.0f} mm, source={s.source})",
            s.citation)

    # terminations: terminals + drawing-listed accessories
    for t in h.terminations:
        if t.terminal_mpn:
            add(t.terminal_mpn, 1, f"termination {t.id}", t.citation)
        for acc in t.accessories:
            add(acc, 1, f"accessory on termination {t.id}", t.citation)

    # tapes / labels listed on the drawing
    for tp in h.tapes:
        if tp.get("mpn"):
            qty = tp.get("qty")
            if qty is None:
                span = abs(float(tp.get("to_mm", 0)) - float(tp.get("from_mm", 0)))
                part = prog.part(tp["mpn"])
                qty = span / 1000.0 if (part and part.uom == "m") else 1
            add(tp["mpn"], qty, f"tape {tp.get('kind', '')} on {tp.get('segment', '?')}")
    for lb in h.labels:
        if lb.get("mpn"):
            add(lb["mpn"], lb.get("qty", 1), f"label '{lb.get('text', '')}'")

    return _merge(lines)


def _merge(lines: list[DemandLine]) -> list[DemandLine]:
    merged: dict[tuple, DemandLine] = {}
    for ln in lines:
        key = (ln.mpn, ln.harness, ln.origin)
        if key in merged:
            m = merged[key]
            m.qty_per_harness += ln.qty_per_harness
            if ln.detail and ln.detail not in m.detail:
                m.detail += "; " + ln.detail
        else:
            merged[key] = DemandLine(**{**ln.__dict__})
    return list(merged.values())


def demand_for_program(prog: ProgramData) -> list[DemandLine]:
    out: list[DemandLine] = []
    for h in prog.harnesses:
        out += demand_for_harness(prog, h)
    return out


def demand_per_set(prog: ProgramData) -> dict[str, float]:
    """mpn -> qty per set (structure origin only)."""
    per_set: dict[str, float] = {}
    for h in prog.harnesses:
        for ln in demand_for_harness(prog, h):
            per_set[ln.mpn] = per_set.get(ln.mpn, 0) + ln.qty_per_harness * h.qty_per_set
    return per_set
