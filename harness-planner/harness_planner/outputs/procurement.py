"""Procurement output (Part 9).

One ordering table plus distributor import CSVs (Octopart BOM tool, DigiKey
myLists, Mouser BOM tool). URL policy: every link must come from a search
result or a document — a part without a verified URL is listed with
"URL not verified", never a fabricated link.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from ..model import ProgramData
from ..rules.quantities import demand_per_set
from ..rules.cascade import CascadeAddition, additions_per_set
from ..rules import tooling as tl
from .bom import order_qty


@dataclass
class OrderLine:
    mpn: str
    manufacturer: str
    description: str
    qty: float
    uom: str
    unit_price: float | None
    tier_note: str
    ext_price: float | None
    lead_time_weeks: float | None
    distributor: str
    url: str
    bucket: str   # purchased|consigned|in_inventory|tooling


def build_order(prog: ProgramData, additions: list[CascadeAddition],
                groups: list[tl.GroupReport] | None = None,
                weeks_of_material: float = 8.0) -> list[OrderLine]:
    """Order for `weeks_of_material` weeks at the max planned volume."""
    vols = prog.meta.planned_volumes()
    weekly_sets = max(vols) if vols else 0
    scrap = prog.meta.rates.scrap_fraction
    qty_per_set = demand_per_set(prog)
    for mpn, q in additions_per_set(prog, additions).items():
        qty_per_set[mpn] = qty_per_set.get(mpn, 0) + q

    lines: list[OrderLine] = []
    for mpn, qps in sorted(qty_per_set.items()):
        p = prog.part(mpn)
        if not p:
            lines.append(OrderLine(mpn, "?", "unresolved BOM item", 0, "ea", None,
                                   "", None, None, "—", "URL not verified",
                                   "purchased"))
            continue
        need = qps * weekly_sets * weeks_of_material
        oq = order_qty(need, p.moq, p.package_qty, scrap)
        price = p.price_at(oq)
        link = next((l for l in p.distributor_links
                     if l.get("url") and l.get("url_verified")), None)
        any_link = link or next((l for l in p.distributor_links
                                 if l.get("distributor")), None)
        bucket = ("consigned" if p.consigned else "purchased")
        lines.append(OrderLine(
            mpn=p.mpn, manufacturer=p.manufacturer, description=p.description,
            qty=round(oq, 2), uom=p.uom, unit_price=price,
            tier_note=f"tier ≥{oq:g}; budgetary ±30%" if price is not None
            else "no price on file",
            ext_price=round(oq * price, 2) if price is not None else None,
            lead_time_weeks=p.lead_time_weeks,
            distributor=(any_link or {}).get("distributor", "—"),
            url=(link or {}).get("url") or "URL not verified",
            bucket=bucket))
    # tools to buy, separated from materials
    for g in groups or []:
        if g.chosen_path and g.chosen_path.name.startswith("buy"):
            mpn = g.chosen_path.name.split()[-1]
            p = prog.part(mpn)
            lines.append(OrderLine(
                mpn=mpn, manufacturer=p.manufacturer if p else "",
                description=(p.description if p else f"named tool for {g.key}"),
                qty=1, uom="ea", unit_price=p.price_at(1) if p else None,
                tier_note="budgetary ±30%" if p and p.price_at(1) is not None
                else "quote needed",
                ext_price=p.price_at(1) if p else None,
                lead_time_weeks=p.lead_time_weeks if p else None,
                distributor="—", url="URL not verified", bucket="tooling"))
    return lines


# --------------------------------------------------------------------------- #
def write_order_csv(lines: list[OrderLine], path: Path):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "mpn", "manufacturer", "description", "qty", "uom",
                    "unit_price", "price_note", "ext_price", "lead_time_weeks",
                    "distributor", "url"])
        for ln in sorted(lines, key=lambda l: (l.bucket, l.mpn)):
            w.writerow([ln.bucket, ln.mpn, ln.manufacturer, ln.description,
                        ln.qty, ln.uom,
                        "" if ln.unit_price is None else ln.unit_price,
                        ln.tier_note,
                        "" if ln.ext_price is None else ln.ext_price,
                        "" if ln.lead_time_weeks is None else ln.lead_time_weeks,
                        ln.distributor, ln.url])


def write_octopart_csv(lines: list[OrderLine], path: Path):
    """Octopart BOM tool accepts MPN/Manufacturer/Qty columns."""
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["MPN", "Manufacturer", "Qty", "Reference"])
        for ln in lines:
            if ln.bucket == "purchased":
                w.writerow([ln.mpn, ln.manufacturer, _int_qty(ln), ln.description])


def write_digikey_csv(lines: list[OrderLine], path: Path):
    """DigiKey myLists upload: MPN + Quantity + Customer Reference."""
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Manufacturer Part Number", "Quantity", "Customer Reference"])
        for ln in lines:
            if ln.bucket == "purchased":
                w.writerow([ln.mpn, _int_qty(ln), ln.description[:48]])


def write_mouser_csv(lines: list[OrderLine], path: Path):
    """Mouser BOM tool upload: Mfr Part Number + Quantity + Description."""
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Mfr Part Number", "Quantity 1", "Description",
                    "Customer Part Number"])
        for ln in lines:
            if ln.bucket == "purchased":
                w.writerow([ln.mpn, _int_qty(ln), ln.description[:60], ""])


def _int_qty(ln: OrderLine) -> int:
    import math
    return max(1, math.ceil(ln.qty))


def markdown(prog: ProgramData, lines: list[OrderLine],
             weeks_of_material: float) -> str:
    cur = prog.meta.rates.currency
    out = [f"# Procurement — {prog.meta.name}", "",
           f"Order horizon: {weeks_of_material:g} weeks of material at the maximum "
           f"planned volume ({max(prog.meta.planned_volumes()):g} "
           f"{prog.meta.volume_unit}), MOQ/package rounding and "
           f"{prog.meta.rates.scrap_fraction:.0%} scrap applied. Prices are "
           "budgetary (±30%) until quoted.", ""]
    for bucket, title in [("purchased", "Purchased material"),
                          ("consigned", "Consigned (customer-supplied)"),
                          ("in_inventory", "From our inventory"),
                          ("tooling", "Tools and equipment (separate order)")]:
        rows = [l for l in lines if l.bucket == bucket]
        if not rows:
            continue
        out.append(f"## {title}")
        out.append("| MPN | Manufacturer | Description | Qty | UoM | Unit price | "
                   "Ext | Lead (wk) | Distributor | URL |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        total = 0.0
        for ln in rows:
            up = f"{ln.unit_price:.4f}" if ln.unit_price is not None else "—"
            ext = f"{ln.ext_price:,.2f}" if ln.ext_price is not None else "—"
            total += ln.ext_price or 0
            out.append(f"| {ln.mpn} | {ln.manufacturer} | {ln.description} | "
                       f"{ln.qty:g} | {ln.uom} | {up} | {ext} | "
                       f"{ln.lead_time_weeks if ln.lead_time_weeks is not None else '—'} | "
                       f"{ln.distributor} | {ln.url} |")
        out.append(f"\n**Bucket total: {cur} {total:,.2f}** (unpriced lines "
                   "excluded — they are open items)\n")
    out.append("## How to order")
    out.append("- `procurement_octopart.csv` → upload to Octopart's BOM tool to "
               "compare distributors and push to carts.")
    out.append("- `procurement_digikey.csv` → DigiKey myLists upload "
               "(shareable list).")
    out.append("- `procurement_mouser.csv` → Mouser BOM tool / Project Manager "
               "upload.")
    out.append("")
    out.append("Upload-page URLs are found by search in run mode and recorded here "
               "only when verified; none are fabricated. If DigiKey/Mouser/Nexar "
               "API keys are configured, the cart can be built programmatically "
               "instead.")
    return "\n".join(out) + "\n"
