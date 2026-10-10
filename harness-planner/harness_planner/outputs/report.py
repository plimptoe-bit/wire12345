"""Management report: hours, percentages, costs, decisions; details go to
appendices (lesson 9). Markdown + PDF (reportlab)."""
from __future__ import annotations

from pathlib import Path

from ..model import ProgramData
from ..rules.findings import Finding
from ..units import fmt_money, fmt_pct
from .costing import CostModel
from .planning import HarnessTimes, capacity, minutes_per_set


def management_summary(prog: ProgramData, cm: CostModel,
                       times: list[HarnessTimes], findings: list[Finding],
                       mvb: dict | None, mg: dict | None) -> str:
    cur = prog.meta.rates.currency
    vols = prog.meta.volumes_per_week
    out = [f"# {prog.meta.name} — management summary", "",
           f"Customer: {prog.meta.customer} · drawing rev {prog.meta.revision} · "
           f"{prog.meta.date}", ""]
    out.append(f"**Volumes** are stated in the customer's unit "
               f"(**{prog.meta.volume_unit}**): planned {vols}, plus "
               f"{prog.meta.upper_limit_factors} upper limits.")
    out.append("")
    mps = minutes_per_set(times, cm.mode)
    out.append(f"- Labor: **{mps / 60:.2f} h per set** "
               f"({cm.mode}; planning estimate ±25%).")
    cap = capacity(prog, times, cm.mode)
    hi = cap[-1]
    out.append(f"- At the {hi.volume:g} {prog.meta.volume_unit} upper limit: "
               f"**{hi.hours_per_week:.0f} h/week, {hi.technicians} "
               f"technician(s)**"
               + ("; second shift needed" if hi.second_shift else "") + ".")
    lo, hi_c = cm.rows[0], cm.rows[-1]
    out.append(f"- Cost per set: **{fmt_money(hi_c.total_per_set, cur)}** at "
               f"{hi_c.volume:g}/wk to **{fmt_money(lo.total_per_set, cur)}** at "
               f"{lo.volume:g}/wk (budgetary ±30%).")
    out.append(f"- One-time (NRE + tooling): **{fmt_money(cm.nre_one_time, cur)}**; "
               f"equipment capital: {fmt_money(cm.equipment_capital, cur)}.")
    if mg:
        g0 = mg["rows"][0]
        out.append(f"- Margin at {fmt_money(mg['selling_price_per_set'], cur)}/set: "
                   f"**{fmt_pct(g0['gm_pct'])}** at {g0['volume']:g}/wk; break-even "
                   f"{mg['breakeven_sets_per_week']} {prog.meta.volume_unit}.")
    if mvb:
        out.append(f"- Make vs buy: **{mvb['recommendation']}** (quote "
                   f"{mvb['supplier']}; gaps estimated and marked).")
    blockers = [f for f in findings if f.severity == "blocker"]
    warns = [f for f in findings if f.severity == "warning"]
    out.append(f"- Findings: **{len(blockers)} blockers** (customer answers "
               f"needed), {len(warns)} warnings. See open-items register.")
    out.append("")
    out.append("## Decisions needed")
    for f in blockers:
        out.append(f"- **{f.id}** {f.message} — proposed default: "
                   f"{f.proposed_default or 'none'}")
    if not blockers:
        out.append("- none — architecture and BOM reconcile clean")
    out.append("")
    out.append("## Assumptions register (top)")
    for a in prog.assumptions:
        out.append(f"- {a.id}: {a.text} [{a.status}]")
    out.append("")
    out.append("Appendices: BOM (bom.csv), termination map, tooling list, "
               "production plan, cost workbook (costing.xlsx), procurement CSVs, "
               "formboards (per harness).")
    return "\n".join(out) + "\n"


def write_pdf(markdown_text: str, path: Path):
    """Render the management summary to a simple PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    story = []
    for line in markdown_text.splitlines():
        line = line.rstrip()
        if not line:
            story.append(Spacer(1, 4 * mm))
        elif line.startswith("# "):
            story.append(Paragraph(_pdf_escape(line[2:]), styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(_pdf_escape(line[3:]), styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + _md_inline(line[2:]),
                                   styles["Normal"]))
        else:
            story.append(Paragraph(_md_inline(line), styles["Normal"]))
    SimpleDocTemplate(str(path), pagesize=A4).build(story)


def _pdf_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_inline(s: str) -> str:
    s = _pdf_escape(s)
    out, bold = [], False
    while "**" in s:
        pre, s = s.split("**", 1)
        out.append(pre)
        out.append("</b>" if bold else "<b>")
        bold = not bold
    out.append(s + ("</b>" if bold else ""))
    return "".join(out)
