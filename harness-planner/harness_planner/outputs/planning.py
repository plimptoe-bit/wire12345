"""Production planning (Part 8): line plan, time standards, capacity and
labor, equipment list and trade-offs, lead time, maintenance plan.

Time standards are synthesized from the harness structure when the program
provides none; they are planning estimates (assumption A-TIME) until measured.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from ..inventory import Inventory
from ..model import EquipmentOption, ProgramData
from ..rules import tooling as tl
from ..units import fmt_money, fmt_pct

STATIONS = [
    ("cut_strip", "Cutting / stripping"),
    ("cable_prep", "Cable preparation (shield / coax prep)"),
    ("crimp_solder", "Crimp / solder"),
    ("assembly", "Connector assembly"),
    ("layout", "Layout / tape / label"),
    ("test_pack", "Test / inspect / pack"),
]

# planning-estimate unit times, minutes — assumption A-TIME (±25% sensitivity
# is carried in the margin output)
T = {
    "cut_strip_per_segment": 0.8,
    "cut_strip_per_segment_machine": 0.25,
    "shield_prep_per_term": 2.5,
    "coax_prep_per_term": 1.5,
    "crimp_hand_per_term": tl.HAND_CRIMP_MIN,
    "crimp_press_per_term": tl.PRESS_CRIMP_MIN,
    "solder_per_term": tl.SOLDER_JOINT_MIN,
    "insert_per_term": 0.5,
    "accessory_fit": 0.3,
    "per_connector_close": 0.5,
    "layout_per_500mm": 1.0,
    "per_tape": 0.8,
    "per_label": 0.5,
    "test_base": 2.0,
    "test_per_term": 0.1,
    "test_shielded_link": 3.0,
    "max_technicians_per_shift": 4,
}


@dataclass
class HarnessTimes:
    drawing_number: str
    family: str
    qty_per_set: float
    manual: dict[str, float] = field(default_factory=dict)     # station -> min
    semiauto: dict[str, float] = field(default_factory=dict)

    def total(self, mode: str) -> float:
        return sum((self.manual if mode == "manual" else self.semiauto).values())


def synthesize_times(prog: ProgramData) -> list[HarnessTimes]:
    out = []
    for h in prog.harnesses:
        ht = HarnessTimes(h.drawing_number, h.family, h.qty_per_set)
        reel_segs = [s for s in h.segments if s.source == "reel"]
        terms = [t for t in h.terminations if t.ttype != "preterminated"]
        crimps = [t for t in terms if t.ttype.startswith("crimp")]
        solders = [t for t in terms if t.ttype.startswith("solder")]
        shielded = [t for t in terms if t.shielded]
        coax = [t for t in terms
                if (p := prog.part(h.segment(t.segment).part_mpn)) and p.coax_group]
        conn_nodes = [n for n in h.nodes if n.kind == "connector"]
        acc_count = sum(len(t.accessories) for t in h.terminations)
        seg_len = sum(s.length_mm for s in h.segments)

        ht.manual["cut_strip"] = len(reel_segs) * T["cut_strip_per_segment"]
        ht.semiauto["cut_strip"] = len(reel_segs) * T["cut_strip_per_segment_machine"]
        prep = (len(shielded) * T["shield_prep_per_term"]
                + len(coax) * T["coax_prep_per_term"])
        ht.manual["cable_prep"] = ht.semiauto["cable_prep"] = prep
        ht.manual["crimp_solder"] = (len(crimps) * T["crimp_hand_per_term"]
                                     + len(solders) * T["solder_per_term"])
        ht.semiauto["crimp_solder"] = (len(crimps) * T["crimp_press_per_term"]
                                       + len(solders) * T["solder_per_term"])
        asm = (len(terms) * T["insert_per_term"] + acc_count * T["accessory_fit"]
               + len(conn_nodes) * T["per_connector_close"])
        ht.manual["assembly"] = ht.semiauto["assembly"] = asm
        lay = (seg_len / 500.0 * T["layout_per_500mm"]
               + len(h.tapes) * T["per_tape"] + len(h.labels) * T["per_label"])
        ht.manual["layout"] = ht.semiauto["layout"] = lay
        test = (T["test_base"] + len(terms) * T["test_per_term"]
                + (T["test_shielded_link"] if shielded else 0))
        ht.manual["test_pack"] = ht.semiauto["test_pack"] = test
        for k in ht.manual:
            ht.manual[k] = round(ht.manual[k], 2)
            ht.semiauto[k] = round(ht.semiauto[k], 2)
        out.append(ht)
    return out


def minutes_per_set(times: list[HarnessTimes], mode: str) -> float:
    return sum(ht.total(mode) * ht.qty_per_set for ht in times)


def station_minutes_per_set(times: list[HarnessTimes], mode: str) -> dict[str, float]:
    agg: dict[str, float] = {}
    for ht in times:
        d = ht.manual if mode == "manual" else ht.semiauto
        for k, v in d.items():
            agg[k] = agg.get(k, 0) + v * ht.qty_per_set
    return agg


# --------------------------------------------------------------------------- #
@dataclass
class CapacityRow:
    volume: float
    hours_per_week: float
    technicians: int
    bottleneck: str
    second_shift: bool


def capacity(prog: ProgramData, times: list[HarnessTimes], mode: str,
             groups: list[tl.GroupReport] | None = None) -> list[CapacityRow]:
    rows = []
    mps = minutes_per_set(times, mode)
    ph = prog.meta.rates.productive_hours_per_week
    for v in prog.meta.planned_volumes():
        hours = v * mps / 60.0
        techs = max(1, math.ceil(hours / ph))
        # bottleneck: the single largest station load vs one technician-station
        st = station_minutes_per_set(times, mode)
        worst = max(st, key=st.get)
        worst_hours = st[worst] * v / 60.0
        bn = f"{dict(STATIONS)[worst]} ({worst_hours:.1f} h/wk)"
        if groups:
            press_cycles = sum(g.cycles_per_week_at_max for g in groups
                               if g.chosen_path and "applicator" in g.chosen_path.name)
            if press_cycles:
                bn += f"; press {press_cycles:g} cycles/wk"
        rows.append(CapacityRow(
            volume=v, hours_per_week=round(hours, 1), technicians=techs,
            bottleneck=bn,
            second_shift=techs > T["max_technicians_per_shift"]))
    return rows


# --------------------------------------------------------------------------- #
def tradeoffs(prog: ProgramData, times: list[HarnessTimes]) -> list[dict]:
    """Payback of each equipment option at each volume."""
    out = []
    rate = (prog.meta.rates.technician_rate_per_hour
            * prog.meta.rates.loaded_multiplier)
    st_manual = station_minutes_per_set(times, "manual")
    for eq in prog.equipment_options:
        if not eq.replaces_station or eq.phase == "excluded":
            continue
        manual_min = st_manual.get(eq.replaces_station, 0)
        saved_min_per_set = manual_min * (1 - eq.time_factor)
        cost_mid = (eq.cost_low + eq.cost_high) / 2
        row = {"option": eq.name, "id": eq.id, "cost_mid": cost_mid,
               "saved_min_per_set": round(saved_min_per_set, 2), "paybacks": {}}
        for v in prog.meta.planned_volumes():
            weekly_saving = saved_min_per_set * v / 60.0 * rate
            row["paybacks"][v] = (round(cost_mid / weekly_saving, 1)
                                  if weekly_saving > 0 else None)
        beats = [v for v, w in row["paybacks"].items()
                 if w is not None and w <= prog.meta.horizon_weeks]
        row["pays_back_within_horizon_at"] = min(beats) if beats else None
        out.append(row)
    return out


# --------------------------------------------------------------------------- #
def lead_time(prog: ProgramData, groups: list[tl.GroupReport]) -> dict:
    purchased = [p for p in prog.parts.values()
                 if not p.consigned and p.lead_time_weeks is not None]
    longest = max(purchased, key=lambda p: p.lead_time_weeks, default=None)
    material_wk = longest.lead_time_weeks if longest else 0
    tool_wk = 0.0
    for g in groups:
        if g.chosen_path and g.chosen_path.name.startswith("buy"):
            mpn = g.chosen_path.name.split()[-1]
            p = prog.part(mpn)
            if p and p.lead_time_weeks:
                tool_wk = max(tool_wk, p.lead_time_weeks)
    eq_wk = max((e.lead_time_weeks for e in prog.equipment_options
                 if e.phase == "buy_now"), default=0.0)
    tool_wk = max(tool_wk, eq_wk)
    fai_wk, training_wk = 2.0, 1.0  # assumptions A-FAI, A-TRAIN
    critical = max(material_wk, tool_wk) + fai_wk + training_wk
    return {
        "longest_lead_part": longest.mpn if longest else "n/a",
        "material_weeks": material_wk,
        "tooling_weeks": tool_wk,
        "fai_qualification_weeks": fai_wk,
        "training_weeks": training_wk,
        "critical_path_weeks": critical,
        "note": ("FAI/qualification and training run after the longer of material "
                 "and tooling arrival; values are assumptions until scheduled."),
    }


# --------------------------------------------------------------------------- #
def maintenance_rows(prog: ProgramData, groups: list[tl.GroupReport],
                     inv: Inventory) -> list[dict]:
    used: dict[str, float] = {}
    for g in groups:
        if g.chosen_path and "existing tool" in g.chosen_path.name:
            mpn = g.chosen_path.name.split()[2]
            used[mpn] = used.get(mpn, 0) + g.cycles_per_week_at_max
    rows = []
    for mpn, weekly in sorted(used.items()):
        t = inv.get(mpn)
        if not t:
            continue
        cal_cost = 120.0  # assumption A-CAL: per-event external calibration
        per_year = (12 / t.calibration_interval_months * cal_cost
                    if t.calibration_interval_months else 0)
        rows.append({
            "tool": t.mpn, "class": t.tool_class,
            "calibration_interval_months": t.calibration_interval_months,
            "pm": "clean + inspect dies weekly; lubricate per instruction sheet",
            "consumables": "n/a" if t.tool_class != "solder_station"
            else "tips, flux, solder",
            "spares": "die set / nest" if t.tool_class in
            ("hand_crimp", "die_set", "applicator") else "—",
            "certified_by": "external lab (crimp height gauge traceable)",
            "cycles_added_per_week": round(weekly, 1),
            "cost_per_year": round(per_year, 2),
        })
    return rows


# --------------------------------------------------------------------------- #
def markdown(prog: ProgramData, times: list[HarnessTimes],
             groups: list[tl.GroupReport], inv: Inventory) -> str:
    cur = prog.meta.rates.currency
    r = prog.meta.rates
    out = [f"# Production plan — {prog.meta.name}", ""]

    out.append("## Line plan")
    fams = {h.family for h in prog.harnesses}
    out.append("Flow: incoming material → " +
               " → ".join(name for _, name in STATIONS) +
               " → ship. One-piece flow at prototype volume; a WIP buffer of one "
               "set between crimp and assembly; rework loops back to the failing "
               "station with a red tag and re-test.")
    out.append(f"Families on program: {', '.join(sorted(fams))}. Floor space: one "
               "bench per station plus formboard tables (assumption A-FLOOR: "
               "~6 m² per station).")
    out.append("")

    out.append("## Time standards (planning estimates — assumption A-TIME, "
               "±25% until measured)")
    out.append("")
    out.append("| Harness | Family | " +
               " | ".join(name for _, name in STATIONS) +
               " | Total manual (min) | Total semi-auto (min) |")
    out.append("|---|---|" + "---|" * (len(STATIONS) + 2))
    for ht in times:
        cells = " | ".join(f"{ht.manual.get(k, 0):g}/{ht.semiauto.get(k, 0):g}"
                           for k, _ in STATIONS)
        out.append(f"| {ht.drawing_number} | {ht.family} | {cells} | "
                   f"{ht.total('manual'):.1f} | {ht.total('semiauto'):.1f} |")
    out.append("")
    mps_m = minutes_per_set(times, "manual")
    mps_s = minutes_per_set(times, "semiauto")
    out.append(f"Minutes per **set**: {mps_m:.1f} manual / {mps_s:.1f} semi-auto "
               "(cells show manual/semi-auto).")
    st = station_minutes_per_set(times, "manual")
    tot = sum(st.values()) or 1
    out.append("Share of labor by station (manual): " +
               ", ".join(f"{dict(STATIONS)[k]} {fmt_pct(v / tot)}"
                         for k, v in sorted(st.items(), key=lambda kv: -kv[1])))
    out.append("")

    out.append("## Capacity and labor")
    out.append(f"Productive hours: {r.productive_hours_per_week:g} h/wk per "
               f"technician (program input); second shift above "
               f"{T['max_technicians_per_shift']} technicians (assumption A-SHIFT).")
    out.append("")
    out.append(f"| Volume ({prog.meta.volume_unit}) | Hours/week (manual) | "
               "Technicians | Bottleneck | Second shift? |")
    out.append("|---|---|---|---|---|")
    for row in capacity(prog, times, "manual", groups):
        out.append(f"| {row.volume:g} | {row.hours_per_week} | {row.technicians} | "
                   f"{row.bottleneck} | {'YES' if row.second_shift else 'no'} |")
    out.append("")

    out.append("## Equipment list")
    out.append("| Equipment | Cost low–high | Rate | Setup (h) | Changeover (min) | "
               "Service | Calib. cost/yr | Life (yr) | Phase | Reason |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for e in prog.equipment_options:
        rate_txt = f"{e.rate_per_hour:g}/h" if e.rate_per_hour else "—"
        out.append(f"| {e.name} | {fmt_money(e.cost_low, cur)}–"
                   f"{fmt_money(e.cost_high, cur)} | {rate_txt} | "
                   f"{e.one_time_setup_h:g} | {e.changeover_min:g} | "
                   f"{e.service_interval or '—'} | "
                   f"{fmt_money(e.calibration_cost_per_year, cur)} | "
                   f"{e.life_years:g} | {e.phase} | {e.phase_reason or '—'} |")
    out.append("")

    out.append("## Equipment trade-offs (payback in weeks)")
    tr = tradeoffs(prog, times)
    if tr:
        vols = prog.meta.planned_volumes()
        out.append("| Option | Cost (mid) | Min saved/set | " +
                   " | ".join(f"@{v:g}" for v in vols) + " | Pays back in horizon at |")
        out.append("|---|---|---|" + "---|" * (len(vols) + 1))
        for t in tr:
            cells = " | ".join(str(t["paybacks"][v]) if t["paybacks"][v] else "—"
                               for v in vols)
            at = t["pays_back_within_horizon_at"]
            out.append(f"| {t['option']} | {fmt_money(t['cost_mid'], cur)} | "
                       f"{t['saved_min_per_set']} | {cells} | "
                       f"{f'{at:g} {prog.meta.volume_unit}' if at else 'not in horizon'} |")
    else:
        out.append("No parameterized options on file.")
    out.append("")

    out.append("## Lead time to first shipment")
    lt = lead_time(prog, groups)
    out.append(f"- Longest-lead material: {lt['longest_lead_part']} "
               f"({lt['material_weeks']:g} wk)")
    out.append(f"- Tooling delivery: {lt['tooling_weeks']:g} wk")
    out.append(f"- First article + qualification: {lt['fai_qualification_weeks']:g} wk "
               "(assumption A-FAI)")
    out.append(f"- Training: {lt['training_weeks']:g} wk (assumption A-TRAIN)")
    out.append(f"- **Critical path: {lt['critical_path_weeks']:g} weeks** — "
               f"{lt['note']}")
    out.append("")

    out.append("## Maintenance plan")
    rows = maintenance_rows(prog, groups, inv)
    if rows:
        out.append("| Tool | Class | Calib. interval (mo) | PM | Consumables | "
                   "Spares | Certified by | Cycles/wk added | Cost/yr |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for m in rows:
            out.append(f"| {m['tool']} | {m['class']} | "
                       f"{m['calibration_interval_months'] or '—'} | {m['pm']} | "
                       f"{m['consumables']} | {m['spares']} | {m['certified_by']} | "
                       f"{m['cycles_added_per_week']} | "
                       f"{fmt_money(m['cost_per_year'], cur)} |")
        out.append("")
        out.append("Calibration cost per event is assumption A-CAL "
                   f"({fmt_money(120, cur)}) until quoted.")
    else:
        out.append("No owned tools selected yet (all paths are purchases).")
    return "\n".join(out) + "\n"
