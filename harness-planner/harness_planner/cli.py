"""Command-line entry points.

    python -m harness_planner ingest  <program_dir> [--package DIR]
    python -m harness_planner check   <program_dir> [--inventory CSV]
    python -m harness_planner confirm <program_dir> <CHECKPOINT> --by NAME [--notes T]
    python -m harness_planner generate <program_dir> [--inventory CSV] [--out DIR]
                                       [--skip-pdf]
    python -m harness_planner update-cycles <program_dir> --inventory CSV --weeks N

`generate` writes every deliverable the checkpoints allow; cost/procurement
outputs are withheld until the architecture and volume units are confirmed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import rules
from .ingest import Checkpoints, CheckpointPending, run_pipeline
from .ingest.pipeline import architecture_table
from .inventory import Inventory
from .model import ProgramData
from .rules.findings import findings_to_markdown
from .outputs import (bom, costing, formboard, planning, procurement, report,
                      spreadsheet, termination_map, tooling_list)


def _default_inventory(program_dir: Path) -> Path:
    for cand in (program_dir / "tool_inventory.csv",
                 program_dir.parent.parent / "tool_inventory.csv",
                 Path(__file__).resolve().parent.parent / "data" /
                 "tool_inventory.csv"):
        if cand.exists():
            return cand
    raise SystemExit("no tool_inventory.csv found — pass --inventory")


def cmd_ingest(args):
    artifacts = run_pipeline(args.program_dir, args.package)
    for k, v in artifacts.items():
        print(f"{k}: {v}")
    print("\nNext: review work/03_architecture_table.md with the owner, then "
          "`confirm CONFIRM_ARCHITECTURE` and `confirm CONFIRM_VOLUME_UNITS`.")


def cmd_check(args):
    prog = ProgramData.load(args.program_dir)
    inv = Inventory.load(args.inventory or _default_inventory(Path(args.program_dir)))
    findings, additions, _ = rules.run_all(prog, inv)
    print(findings_to_markdown(findings))
    blockers = sum(1 for f in findings if f.severity == "blocker")
    print(f"{len(findings)} finding(s), {blockers} blocker(s), "
          f"{len(additions)} cascade addition(s).")
    return 1 if blockers else 0


def cmd_confirm(args):
    cps = Checkpoints.load(args.program_dir)
    cps.confirm(args.checkpoint, by=args.by, notes=args.notes or "")
    print(cps.summary_markdown())


def generate_all(program_dir: Path, inventory_path: Path | None = None,
                 out_dir: Path | None = None, skip_pdf: bool = False) -> dict:
    """Produce every deliverable the checkpoints allow.

    Returns {"out_dir", "produced", "withheld"} so both the CLI and the GUI
    can drive it.
    """
    program_dir = Path(program_dir)
    out_dir = Path(out_dir) if out_dir else program_dir / "deliverables"
    out_dir.mkdir(parents=True, exist_ok=True)
    prog = ProgramData.load(program_dir)
    inv = Inventory.load(inventory_path or _default_inventory(program_dir))
    cps = Checkpoints.load(program_dir)

    findings, additions, groups = rules.run_all(prog, inv)

    # always-produced interpretation outputs
    (out_dir / "architecture.md").write_text(architecture_table(prog))
    (out_dir / "findings.md").write_text(
        "# Findings\n\n" + findings_to_markdown(findings))
    tiers = bom.build_tiers(prog, additions)
    bom.write_bom_csv(prog, tiers, out_dir / "bom.csv")
    (out_dir / "bom.md").write_text(bom.bom_markdown(prog, tiers))
    termination_map.write_csv(prog, out_dir / "termination_map.csv")
    (out_dir / "termination_map.md").write_text(termination_map.markdown(prog))
    tooling_list.write_all(prog, groups, inv, out_dir)

    # formboards: generated always; marked draft until first-board validation
    draft = None
    if not cps.is_confirmed("VALIDATE_FIRST_BOARD"):
        draft = ("DRAFT — overlay not released: build and measure one harness "
                 "on the first board before release (VALIDATE_FIRST_BOARD)")
    formboard.write_all(prog, out_dir / "formboards", pdf=not skip_pdf,
                        draft_note=draft)

    produced = ["architecture.md", "findings.md", "bom.csv/md",
                "termination_map.csv/md", "tooling_list.md", "formboards/"]
    withheld = []

    # cost-gated outputs
    times = planning.synthesize_times(prog)
    try:
        cps.require("costing")
        cm = costing.build(prog, times, groups, additions)
        mvb = costing.make_vs_buy(prog, cm)
        mg = costing.margin(prog, cm)
        mh = costing.man_hours(prog, cm, times)
        (out_dir / "production_plan.md").write_text(
            planning.markdown(prog, times, groups, inv))
        (out_dir / "costing.md").write_text(
            costing.markdown(prog, cm, mvb, mg, mh))
        spreadsheet.build_workbook(prog, cm, times, out_dir / "costing.xlsx")
        summary = report.management_summary(prog, cm, times, findings, mvb, mg)
        (out_dir / "management_summary.md").write_text(summary)
        if not skip_pdf:
            report.write_pdf(summary, out_dir / "management_summary.pdf")
        produced += ["production_plan.md", "costing.md", "costing.xlsx",
                     "management_summary.md/pdf"]
    except CheckpointPending as e:
        withheld.append(f"costing outputs — {e}")
        cm = None

    try:
        cps.require("procurement")
        lines = procurement.build_order(prog, additions, groups)
        procurement.write_order_csv(lines, out_dir / "procurement_order.csv")
        procurement.write_octopart_csv(lines, out_dir / "procurement_octopart.csv")
        procurement.write_digikey_csv(lines, out_dir / "procurement_digikey.csv")
        procurement.write_mouser_csv(lines, out_dir / "procurement_mouser.csv")
        (out_dir / "procurement.md").write_text(
            procurement.markdown(prog, lines, 8.0))
        produced += ["procurement_order.csv + distributor CSVs", "procurement.md"]
    except CheckpointPending as e:
        withheld.append(f"procurement outputs — {e}")

    return {"out_dir": str(out_dir), "produced": produced, "withheld": withheld}


def cmd_generate(args):
    program_dir = Path(args.program_dir)
    result = generate_all(
        program_dir,
        inventory_path=Path(args.inventory) if args.inventory else None,
        out_dir=Path(args.out) if args.out else None,
        skip_pdf=args.skip_pdf)
    print(f"Deliverables in {result['out_dir']}:")
    for p in result["produced"]:
        print(f"  + {p}")
    for wmsg in result["withheld"]:
        print(f"  WITHHELD: {wmsg}")
    return 0


def cmd_gui(args):
    from . import gui
    roots = args.roots or []
    if not roots:
        here = Path.cwd()
        pkg_fixtures = Path(__file__).resolve().parent.parent / "data" / "fixtures"
        roots = [str(p) for p in (here, pkg_fixtures) if p.exists()]
    gui.main(roots, args.inventory, args.port,
             open_browser=not args.no_browser)
    return 0


def cmd_update_cycles(args):
    """Run-mode inventory upkeep: add one week's cycles for this program."""
    prog = ProgramData.load(args.program_dir)
    inv_path = args.inventory or _default_inventory(Path(args.program_dir))
    inv = Inventory.load(inv_path)
    groups = rules.tooling.match_program(prog, inv)
    for g in groups:
        if g.chosen_path and "existing tool" in g.chosen_path.name:
            mpn = g.chosen_path.name.split()[2]
            weekly = g.terminations_per_set * (args.sets_per_week or
                                               max(prog.meta.volumes_per_week))
            inv.add_cycles(mpn, int(weekly * args.weeks))
            print(f"{mpn}: +{int(weekly * args.weeks)} cycles")
    inv.save()
    print(f"inventory updated: {inv_path}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="harness_planner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ingest")
    p.add_argument("program_dir")
    p.add_argument("--package", default=None)
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("check")
    p.add_argument("program_dir")
    p.add_argument("--inventory", default=None)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("confirm")
    p.add_argument("program_dir")
    p.add_argument("checkpoint")
    p.add_argument("--by", required=True)
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_confirm)

    p = sub.add_parser("generate")
    p.add_argument("program_dir")
    p.add_argument("--inventory", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--skip-pdf", action="store_true")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("gui", help="clickable Windows XP-style interface")
    p.add_argument("roots", nargs="*", default=None,
                   help="directories to scan for programs (default: "
                        "data/fixtures and the current directory)")
    p.add_argument("--inventory", default=None)
    p.add_argument("--port", type=int, default=8321)
    p.add_argument("--no-browser", action="store_true")
    p.set_defaults(func=cmd_gui)

    p = sub.add_parser("update-cycles")
    p.add_argument("program_dir")
    p.add_argument("--inventory", default=None)
    p.add_argument("--weeks", type=float, default=1.0)
    p.add_argument("--sets-per-week", type=float, default=None)
    p.set_defaults(func=cmd_update_cycles)

    args = ap.parse_args(argv)
    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
