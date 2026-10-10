"""Multi-tier BOM generator (procedure Part 5, step 7).

Levels: 0 set, 1 harness, 2 segment/assembly, 3 parts. Quantities per harness,
per set and per planned volume, with MOQ rounding, scrap allowance, consigned
vs purchased, and the source of every quantity.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

from ..model import ProgramData
from ..rules.quantities import demand_for_harness
from ..rules.cascade import CascadeAddition
from ..sources import Citation


@dataclass
class TierLine:
    level: int
    parent: str
    item: str
    description: str
    category: str
    qty_per_parent: float
    qty_per_set: float
    uom: str
    origin: str             # structure|cascade|drawing
    consigned: bool = False
    moq: float | None = None
    citation: Citation = field(default_factory=Citation)


def build_tiers(prog: ProgramData,
                additions: list[CascadeAddition]) -> list[TierLine]:
    lines: list[TierLine] = [TierLine(
        0, "", f"SET {prog.meta.name}", "harness set", "set", 1, 1, "set",
        "structure")]
    for h in prog.harnesses:
        lines.append(TierLine(
            1, f"SET {prog.meta.name}", h.drawing_number,
            h.name or h.family, "harness", h.qty_per_set, h.qty_per_set, "ea",
            "structure", citation=h.citation))
        # level 2: segments / assemblies
        for s in h.segments:
            part = prog.part(s.part_mpn)
            desc = (f"segment {s.circuit or s.id}: {s.length_mm:g} mm of "
                    f"{s.part_mpn} ({s.source})")
            lines.append(TierLine(
                2, h.drawing_number, f"{h.drawing_number}/{s.id}", desc,
                "segment", 1, h.qty_per_set, "ea", "structure",
                citation=s.citation))
        # level 3: parts from structure
        for d in demand_for_harness(prog, h):
            part = prog.part(d.mpn)
            lines.append(TierLine(
                3, h.drawing_number, d.mpn,
                part.description if part else "(unknown part)",
                part.category if part else "?",
                d.qty_per_harness, d.qty_per_harness * h.qty_per_set, d.uom,
                "structure", consigned=bool(part and part.consigned),
                moq=part.moq if part else None, citation=d.citation))
        # level 3: cascade additions for this harness
        for a in additions:
            if a.harness != h.drawing_number:
                continue
            part = prog.part(a.mpn)
            lines.append(TierLine(
                3, h.drawing_number, a.mpn,
                (part.description if part else "") + f" [{a.note}]",
                part.category if part else "?",
                a.qty_per_harness, a.qty_per_harness * h.qty_per_set,
                part.uom if part else "ea", "cascade",
                consigned=bool(part and part.consigned),
                moq=part.moq if part else None, citation=a.citation))
    return lines


def order_qty(qty: float, moq: float | None, package_qty: float | None,
              scrap_fraction: float) -> float:
    """Apply scrap allowance, then package and MOQ rounding."""
    q = qty * (1 + scrap_fraction)
    if package_qty and package_qty > 1:
        q = math.ceil(q / package_qty) * package_qty
    if moq:
        q = max(q, moq)
    return q


def write_bom_csv(prog: ProgramData, lines: list[TierLine], path: Path):
    vols = prog.meta.planned_volumes()
    scrap = prog.meta.rates.scrap_fraction
    cols = (["level", "parent", "item", "description", "category",
             "qty_per_parent", "qty_per_set", "uom", "origin", "consigned",
             "moq", "source"]
            + [f"weekly_qty_at_{v:g}_sets" for v in vols]
            + [f"weekly_order_qty_at_{v:g}_sets_incl_{scrap:.0%}_scrap" for v in vols])
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for ln in lines:
            part = prog.part(ln.item) if ln.level == 3 else None
            weekly = [ln.qty_per_set * v for v in vols]
            orders = [order_qty(q, ln.moq, part.package_qty if part else None, scrap)
                      if ln.level == 3 and not ln.consigned else ""
                      for q in weekly]
            w.writerow([ln.level, ln.parent, ln.item, ln.description, ln.category,
                        f"{ln.qty_per_parent:g}", f"{ln.qty_per_set:g}", ln.uom,
                        ln.origin, "yes" if ln.consigned else "no",
                        ln.moq if ln.moq else "", ln.citation.short()]
                       + [f"{q:g}" for q in weekly]
                       + [f"{o:g}" if o != "" else "" for o in orders])


def bom_markdown(prog: ProgramData, lines: list[TierLine]) -> str:
    out = [f"# Multi-tier BOM — {prog.meta.name} rev {prog.meta.revision}", ""]
    out.append(f"Volumes planned ({prog.meta.volume_unit}): "
               f"{prog.meta.planned_volumes()} — includes "
               f"{prog.meta.upper_limit_factors} upper limits. Scrap allowance "
               f"{prog.meta.rates.scrap_fraction:.0%} (assumption).")
    out.append("")
    out.append("| L | Item | Description | Qty/parent | Qty/set | UoM | Origin | "
               "Consigned | Source |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for ln in lines:
        indent = "&nbsp;&nbsp;" * ln.level
        out.append(f"| {ln.level} | {indent}{ln.item} | {ln.description} | "
                   f"{ln.qty_per_parent:g} | {ln.qty_per_set:g} | {ln.uom} | "
                   f"{ln.origin} | {'yes' if ln.consigned else 'no'} | "
                   f"{ln.citation.short()} |")
    return "\n".join(out) + "\n"
