"""Cost, make-vs-buy and margin outputs (Part 8).

All money is budgetary (±30%) until quotes are in hand — every table says so.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..model import ProgramData
from ..rules.quantities import demand_per_set
from ..rules.cascade import CascadeAddition, additions_per_set
from ..rules import tooling as tl
from ..units import fmt_money, fmt_pct
from .planning import HarnessTimes, minutes_per_set


@dataclass
class VolumeCost:
    volume: float
    material_per_set: float
    labor_direct_per_set: float
    labor_loaded_per_set: float
    depreciation_per_set: float
    nre_per_set: float
    overhead_per_set: float
    total_per_set: float
    labor_minutes_per_set: float


@dataclass
class CostModel:
    per_set_qty: dict[str, float]
    material_detail: list[dict]
    nre_one_time: float
    nre_detail: list[dict]
    equipment_capital: float
    rows: list[VolumeCost] = field(default_factory=list)
    mode: str = "manual"


def material_per_set(prog: ProgramData, additions: list[CascadeAddition],
                     annual_sets: float) -> tuple[float, list[dict], dict[str, float]]:
    qty = demand_per_set(prog)
    for mpn, q in additions_per_set(prog, additions).items():
        qty[mpn] = qty.get(mpn, 0) + q
    total, detail = 0.0, []
    scrap = prog.meta.rates.scrap_fraction
    for mpn, q in sorted(qty.items()):
        p = prog.part(mpn)
        if not p:
            detail.append({"mpn": mpn, "qty_per_set": q, "unit_price": None,
                           "ext": 0.0, "note": "unknown part — unpriced"})
            continue
        if p.consigned:
            detail.append({"mpn": mpn, "qty_per_set": q, "unit_price": 0.0,
                           "ext": 0.0, "note": "consigned"})
            continue
        price = p.price_at(max(1.0, q * annual_sets))
        if price is None:
            detail.append({"mpn": mpn, "qty_per_set": q, "unit_price": None,
                           "ext": 0.0, "note": "no price on file — open item"})
            continue
        ext = q * price * (1 + scrap)
        total += ext
        detail.append({"mpn": mpn, "qty_per_set": q, "unit_price": price,
                       "ext": round(ext, 4),
                       "note": f"tier at {q * annual_sets:g}/yr, +{scrap:.0%} scrap"})
    return total, detail, qty


def nre(prog: ProgramData, groups: list[tl.GroupReport]) -> tuple[float, list[dict]]:
    """One-time: tooling buys, qualification, setup, programming, training."""
    rate = (prog.meta.rates.technician_rate_per_hour
            * prog.meta.rates.loaded_multiplier)
    items = []
    for g in groups:
        if not g.chosen_path:
            continue
        if g.chosen_path.one_time_cost > 0:
            items.append({"item": f"{g.key}: {g.chosen_path.name}",
                          "cost": g.chosen_path.one_time_cost})
    for e in prog.equipment_options:
        if e.phase == "buy_now" and e.one_time_setup_h:
            items.append({"item": f"setup {e.name}",
                          "cost": e.one_time_setup_h * rate})
    items.append({"item": "formboards + first-article build (assumption A-NRE: 16 h)",
                  "cost": 16 * rate})
    items.append({"item": "training (assumption A-TRAIN: 8 h)", "cost": 8 * rate})
    total = sum(i["cost"] for i in items)
    return total, items


def equipment_capital(prog: ProgramData) -> float:
    return sum((e.cost_low + e.cost_high) / 2 for e in prog.equipment_options
               if e.phase == "buy_now")


def build(prog: ProgramData, times: list[HarnessTimes],
          groups: list[tl.GroupReport], additions: list[CascadeAddition],
          mode: str = "manual") -> CostModel:
    r = prog.meta.rates
    vols = prog.meta.planned_volumes()
    mps = minutes_per_set(times, mode)
    nre_total, nre_detail = nre(prog, groups)
    cap = equipment_capital(prog)
    rows = []
    mat_detail, per_set_qty = [], {}
    for v in vols:
        annual = v * r.weeks_per_year
        mat, mat_detail, per_set_qty = material_per_set(prog, additions, annual)
        labor_direct = mps / 60.0 * r.technician_rate_per_hour
        labor_loaded = labor_direct * r.loaded_multiplier
        depr = (cap / (r.depreciation_years * r.weeks_per_year)) / v if v else 0.0
        nre_per = nre_total / (v * prog.meta.horizon_weeks) if v else 0.0
        total = mat + labor_loaded + depr + nre_per + r.overhead_per_set
        rows.append(VolumeCost(
            volume=v, material_per_set=round(mat, 2),
            labor_direct_per_set=round(labor_direct, 2),
            labor_loaded_per_set=round(labor_loaded, 2),
            depreciation_per_set=round(depr, 2), nre_per_set=round(nre_per, 2),
            overhead_per_set=r.overhead_per_set, total_per_set=round(total, 2),
            labor_minutes_per_set=round(mps, 1)))
    return CostModel(per_set_qty=per_set_qty, material_detail=mat_detail,
                     nre_one_time=round(nre_total, 2), nre_detail=nre_detail,
                     equipment_capital=cap, rows=rows, mode=mode)


# --------------------------------------------------------------------------- #
def make_vs_buy(prog: ProgramData, cm: CostModel) -> dict | None:
    q = prog.supplier_quote
    if not q:
        return None
    quoted = q.get("quoted_per_set")
    covered = {ln.get("mpn") for ln in q.get("lines", [])}
    gaps = []
    gap_cost = 0.0
    for d in cm.material_detail:
        if d["mpn"] not in covered and d["note"] != "consigned":
            gaps.append(d["mpn"])
            gap_cost += d["ext"]
    # reconcile the quote's extended total before using it (lesson 10)
    ext_sum = sum(float(ln.get("unit_price", 0)) * float(ln.get("qty_per_set", 0))
                  for ln in q.get("lines", []))
    buy_per_set = (quoted if quoted is not None else ext_sum) + gap_cost
    rows = []
    for c in cm.rows:
        weekly = (buy_per_set - c.total_per_set) * c.volume
        rows.append({"volume": c.volume, "make_per_set": c.total_per_set,
                     "buy_per_set": round(buy_per_set, 2),
                     "weekly_difference": round(weekly, 2),
                     "annual_difference": round(weekly *
                                                prog.meta.rates.weeks_per_year, 2),
                     "cheaper": "make" if c.total_per_set < buy_per_set else "buy"})
    makes = sum(1 for r in rows if r["cheaper"] == "make")
    rec = ("make in-house" if makes > len(rows) / 2 else "buy outside")
    return {
        "supplier": q.get("supplier", "?"),
        "quoted_per_set": quoted, "quote_lines_ext_sum": round(ext_sum, 2),
        "gap_mpns": gaps, "gap_cost_per_set_estimated": round(gap_cost, 2),
        "coverage_note": q.get("coverage_note", ""),
        "rows": rows, "recommendation": rec,
        "qualitative": ("In-house: ECO turnaround in days not weeks, quality "
                        "ownership, no NCNR exposure on customer changes, capacity "
                        "under our control; headcount and training are ours to carry. "
                        "Outside: frees floor space and technicians, but FAI lead "
                        "time on every revision and margin goes to the supplier."),
    }


def margin(prog: ProgramData, cm: CostModel) -> dict | None:
    price = prog.meta.selling_price_per_set
    if price is None:
        return None
    r = prog.meta.rates
    rows = []
    for c in cm.rows:
        gm = price - c.total_per_set
        rows.append({"volume": c.volume, "cost_per_set": c.total_per_set,
                     "gm_per_set": round(gm, 2),
                     "gm_pct": round(gm / price, 4),
                     "gm_per_year": round(gm * c.volume * r.weeks_per_year, 2)})
    # break-even: weekly fixed (depreciation + NRE amortization) vs unit margin
    weekly_fixed = (cm.equipment_capital / (r.depreciation_years * r.weeks_per_year)
                    + cm.nre_one_time / prog.meta.horizon_weeks)
    c0 = cm.rows[0]
    variable = (c0.material_per_set + c0.labor_loaded_per_set
                + r.overhead_per_set)
    unit_margin = price - variable
    breakeven = weekly_fixed / unit_margin if unit_margin > 0 else None
    sens = []
    for label, d_mat, d_lab in [("base", 0, 0), ("material +15%", 0.15, 0),
                                ("material −15%", -0.15, 0),
                                ("time standards +25%", 0, 0.25),
                                ("time standards −25%", 0, -0.25),
                                ("labor rate +10%", 0, 0.10)]:
        c = cm.rows[0]
        cost = (c.material_per_set * (1 + d_mat)
                + c.labor_loaded_per_set * (1 + d_lab)
                + c.depreciation_per_set + c.nre_per_set + c.overhead_per_set)
        sens.append({"case": label, "cost_per_set": round(cost, 2),
                     "gm_pct": round((price - cost) / price, 4)})
    return {"selling_price_per_set": price, "rows": rows,
            "breakeven_sets_per_week": round(breakeven, 2) if breakeven else None,
            "weekly_fixed": round(weekly_fixed, 2), "sensitivity": sens}


def man_hours(prog: ProgramData, cm: CostModel,
              times: list[HarnessTimes]) -> dict:
    rate = (prog.meta.rates.technician_rate_per_hour
            * prog.meta.rates.loaded_multiplier)
    one_time_h = cm.nre_one_time / rate if rate else 0
    return {"one_time_hours": round(one_time_h, 1),
            "recurring_hours_per_set": round(minutes_per_set(times, cm.mode) / 60, 2)}


# --------------------------------------------------------------------------- #
def markdown(prog: ProgramData, cm: CostModel, mvb: dict | None,
             mg: dict | None, mh: dict) -> str:
    cur = prog.meta.rates.currency
    r = prog.meta.rates
    out = [f"# Cost, make-vs-buy and margin — {prog.meta.name}", "",
           "All prices budgetary (±30%) until quotes are in hand. Labor loading "
           f"multiplier {r.loaded_multiplier}x; depreciation over "
           f"{r.depreciation_years:g} years; NRE amortized over the "
           f"{prog.meta.horizon_weeks}-week horizon.", ""]
    out.append(f"## Cost per set at each volume ({prog.meta.volume_unit}; "
               f"labor mode: {cm.mode})")
    out.append("| Volume | Material | Labor (direct) | Labor (loaded) | "
               "Depreciation | NRE | Overhead | **Total/set** |")
    out.append("|---|---|---|---|---|---|---|---|")
    for c in cm.rows:
        out.append(f"| {c.volume:g} | {fmt_money(c.material_per_set, cur)} | "
                   f"{fmt_money(c.labor_direct_per_set, cur)} | "
                   f"{fmt_money(c.labor_loaded_per_set, cur)} | "
                   f"{fmt_money(c.depreciation_per_set, cur)} | "
                   f"{fmt_money(c.nre_per_set, cur)} | "
                   f"{fmt_money(c.overhead_per_set, cur)} | "
                   f"**{fmt_money(c.total_per_set, cur)}** |")
    out.append("")
    per_harness = {h.drawing_number: h.qty_per_set for h in prog.harnesses}
    out.append(f"Per-harness split of a set: {per_harness} — per-harness cost is "
               "the set cost split by harness labor minutes (appendix of the "
               "spreadsheet).")
    out.append("")
    out.append(f"NRE one-time total: **{fmt_money(cm.nre_one_time, cur)}**; "
               f"equipment capital (buy now): {fmt_money(cm.equipment_capital, cur)}.")
    for i in cm.nre_detail:
        out.append(f"- {i['item']}: {fmt_money(i['cost'], cur)}")
    out.append("")
    out.append(f"## Man-hours\n- One-time: {mh['one_time_hours']} h\n"
               f"- Recurring: {mh['recurring_hours_per_set']} h per set")
    out.append("")
    if mvb:
        out.append(f"## Make vs buy (quote: {mvb['supplier']})")
        if mvb["quoted_per_set"] is not None:
            delta = ""
            if mvb["quote_lines_ext_sum"]:
                delta = (f" — its line items extend to only "
                         f"{fmt_money(mvb['quote_lines_ext_sum'], cur)}, so the "
                         "quoted price carries labor/overhead not itemized; "
                         "reconcile before relying on it (lesson 10)")
            out.append(f"Quoted {fmt_money(mvb['quoted_per_set'], cur)}/set{delta}.")
        if mvb["gap_mpns"]:
            out.append(f"Quote does not cover {len(mvb['gap_mpns'])} part(s) "
                       f"({', '.join(mvb['gap_mpns'])}) — gap estimated at "
                       f"{fmt_money(mvb['gap_cost_per_set_estimated'], cur)}/set "
                       "and **marked as our estimate** (lesson 10). "
                       + mvb.get("coverage_note", ""))
        out.append("")
        out.append("| Volume | Make/set | Buy/set (incl. gap) | Weekly diff "
                   "(buy−make) | Annual diff | Cheaper |")
        out.append("|---|---|---|---|---|---|")
        for row in mvb["rows"]:
            out.append(f"| {row['volume']:g} | {fmt_money(row['make_per_set'], cur)} | "
                       f"{fmt_money(row['buy_per_set'], cur)} | "
                       f"{fmt_money(row['weekly_difference'], cur)} | "
                       f"{fmt_money(row['annual_difference'], cur)} | "
                       f"{row['cheaper']} |")
        out.append("")
        out.append(f"**Recommendation: {mvb['recommendation']}.** "
                   + mvb["qualitative"])
        out.append("")
    if mg:
        out.append(f"## Margin at selling price "
                   f"{fmt_money(mg['selling_price_per_set'], cur)}/set")
        out.append("| Volume | Cost/set | GM/set | GM % | GM/year |")
        out.append("|---|---|---|---|---|")
        for row in mg["rows"]:
            out.append(f"| {row['volume']:g} | {fmt_money(row['cost_per_set'], cur)} | "
                       f"{fmt_money(row['gm_per_set'], cur)} | "
                       f"{fmt_pct(row['gm_pct'])} | "
                       f"{fmt_money(row['gm_per_year'], cur)} |")
        be = mg["breakeven_sets_per_week"]
        out.append("")
        out.append(f"Break-even: **{be if be is not None else 'n/a'} "
                   f"{prog.meta.volume_unit}** against weekly fixed cost "
                   f"{fmt_money(mg['weekly_fixed'], cur)}.")
        out.append("")
        out.append("Sensitivity (at lowest planned volume):")
        out.append("| Case | Cost/set | GM % |")
        out.append("|---|---|---|")
        for s in mg["sensitivity"]:
            out.append(f"| {s['case']} | {fmt_money(s['cost_per_set'], cur)} | "
                       f"{fmt_pct(s['gm_pct'])} |")
    return "\n".join(out) + "\n"
