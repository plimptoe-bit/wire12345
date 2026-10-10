"""Tooling list output (Part 6): named tooling, ranked inventory matches with
evidence, cheapest compliant path, restrictions, qualification sheets."""
from __future__ import annotations

from pathlib import Path

from ..inventory import Inventory
from ..model import ProgramData
from ..rules import tooling
from ..units import fmt_money


def markdown(prog: ProgramData, groups: list[tooling.GroupReport],
             inv: Inventory) -> str:
    cur = prog.meta.rates.currency
    out = [f"# Tooling list — {prog.meta.name}", "",
           "Policy: a tool is compatible if it forms the crimp/joint to the "
           "spec's geometry and passes the spec's inspection and pull test. The "
           "manufacturer's named tool is the default, not a requirement, at this "
           "volume (owner policy, lesson 11).", ""]
    for g in groups:
        out.append(f"## {g.key} — {g.description}")
        r = g.requirement
        geo = []
        if r.height_mm is not None:
            geo.append(f"height {r.height_mm}±{r.height_tol_mm} mm")
        if r.width_mm is not None:
            geo.append(f"width {r.width_mm}±{r.width_tol_mm} mm")
        if r.hex_mm is not None:
            geo.append(f"hex {r.hex_mm} mm")
        if r.wire_mm2 is not None:
            geo.append(f"wire {r.wire_mm2} mm²")
        out.append(f"- Joint: {g.ttype}, form **{r.form or 'n/a'}**"
                   + (", " + ", ".join(geo) if geo else "")
                   + f" — spec {r.citation.short()}")
        out.append(f"- Used on: {', '.join(g.harnesses)}; "
                   f"{g.terminations_per_set:g} terminations/set; "
                   f"{g.cycles_per_week_at_max:g} cycles/week at max volume")
        named = ", ".join(g.named_tools) if g.named_tools else \
            "none on file — pull the application spec tooling table"
        out.append(f"- Spec's named tooling: {named} {g.named_tool_citation.short()}")
        out.append("- Inventory match:")
        if not g.matches:
            out.append("  - none")
        for m in g.matches:
            verdict = {"exact": "**exact**", "qualify":
                       "**within tolerance — qualify**", "no": "no"}[m.verdict]
            out.append(f"  - {m.tool.mpn} ({m.tool.description}): {verdict} — "
                       f"{m.evidence}")
        if g.paths:
            out.append("- Paths (one-time cost + labor min/termination):")
            for p in g.paths:
                mark = " ← **cheapest compliant path**" if p is g.chosen_path else ""
                out.append(f"  - {p.name}: {fmt_money(p.one_time_cost, cur)} one-time, "
                           f"{p.per_termination_min:g} min/term ({p.note}){mark}")
        if g.qualification_needed:
            out.append("- Qualification required before production — see "
                       f"`qualification_{_safe(g.key)}.md`")
        for restr in g.restrictions:
            out.append(f"- ⚠ Restriction: {restr}")
        out.append("")
    flags = tooling.inventory_health(groups, inv)
    out.append("## Tool inventory health (chosen tools)")
    out += [f"- {f}" for f in flags] or ["- no flags"]
    out.append("")
    out.append("Cycle-time values are planning estimates (assumption A-TOOL-T) "
               "until measured.")
    return "\n".join(out) + "\n"


def _safe(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)


def write_all(prog: ProgramData, groups: list[tooling.GroupReport],
              inv: Inventory, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tooling_list.md").write_text(markdown(prog, groups, inv))
    for g in groups:
        if not g.qualification_needed or not g.chosen_path:
            continue
        if "existing tool" not in g.chosen_path.name:
            continue
        mpn = g.chosen_path.name.split()[2]
        tool = inv.get(mpn)
        if tool:
            (out_dir / f"qualification_{_safe(g.key)}.md").write_text(
                tooling.qualification_protocol(prog, g, tool))
