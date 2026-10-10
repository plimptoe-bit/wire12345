"""Ingestion pipeline (procedure Part 5, steps 1–3).

    file inventory -> rasterize/OCR -> drawing reading (human/agent)
      -> architecture table  [CHECKPOINT: CONFIRM_ARCHITECTURE]
      -> volume units        [CHECKPOINT: CONFIRM_VOLUME_UNITS]
      -> BOM reconciliation  [CHECKPOINT: RESOLVE_BLOCKERS]

The pipeline writes numbered intermediate artifacts into <program>/work/ so
every interpretation step is visible and reviewable. Drawing reading itself is
not automated away: the rasterized pages are produced for the analyst (human
or agent) to read, and what they conclude is entered into program.json; the
architecture table is then *generated back* from program.json so the owner
confirms what the data model actually says, not what the analyst meant to say.
"""
from __future__ import annotations

from pathlib import Path

from ..model import ProgramData
from .. import rules
from ..rules.findings import findings_to_markdown
from .checkpoints import Checkpoints, ARCHITECTURE, VOLUME_UNITS, BLOCKERS
from .inventory import inventory_package, inventory_markdown, rasterize_pdfs


def architecture_table(prog: ProgramData) -> str:
    """The end-to-end segment table the owner confirms before anything else."""
    out = ["# Harness architecture — confirm before any costing", ""]
    out.append(f"Program: **{prog.meta.name}** rev {prog.meta.revision} — "
               f"volumes planned: {prog.meta.volumes_per_week} "
               f"**{prog.meta.volume_unit}** (plus upper limits "
               f"{prog.meta.upper_limit_factors}); please confirm the unit.")
    out.append("")
    for h in prog.harnesses:
        out.append(f"## {h.drawing_number} rev {h.revision} — {h.name or h.family} "
                   f"(x{h.qty_per_set:g} per set)")
        if h.length_convention:
            out.append(f"Dimension convention applied: *{h.length_convention}*")
        out.append("")
        out.append("| Segment | From (end A) | Conductor / construction | Shield | "
                   "Length | To (end B) | Source |")
        out.append("|---|---|---|---|---|---|---|")
        for s in h.segments:
            part = prog.part(s.part_mpn)
            a, b = h.node(s.from_node), h.node(s.to_node)

            def endtxt(n):
                base = f"{n.id} ({n.kind}"
                if n.housing_mpn:
                    base += f" {n.housing_mpn}"
                return base + ")"

            cons = "?"
            if part:
                if part.category == "preterminated_assembly":
                    cons = f"pre-terminated assembly {part.mpn}"
                else:
                    bits = []
                    if part.conductor_mm2:
                        bits.append(f"{part.conductor_mm2} mm²")
                    if part.attrs.get("pairs"):
                        bits.append(f"{part.attrs['pairs']} pair")
                    if part.attrs.get("insulation_od_mm"):
                        bits.append(f"OD {part.attrs['insulation_od_mm']} mm")
                    cons = f"{part.mpn}: " + ", ".join(bits) if bits else part.mpn
            out.append(f"| {s.id} {s.circuit} | {endtxt(a)} | {cons} | "
                       f"{part.shield if part else '?'} | {s.length_mm:g} ±"
                       f"{s.tol_mm:g} mm | {endtxt(b)} | {s.source} |")
        out.append("")
        # what sits at each connector
        out.append("| Node | Housing | Cavities used | Terminations |")
        out.append("|---|---|---|---|")
        for n in h.nodes:
            if n.kind != "connector":
                continue
            terms = h.terminations_at(n.id)
            cavs = ", ".join(sorted(t.cavity or "?" for t in terms)) or "—"
            tt = ", ".join(f"{t.id}:{t.ttype}" for t in terms) or "—"
            out.append(f"| {n.id} ({n.label or '—'}) | {n.housing_mpn or '—'} | "
                       f"{cavs} | {tt} |")
        out.append("")
    out.append("> **Checkpoint CONFIRM_ARCHITECTURE** — owner: reply with corrections "
               "or 'confirmed'. Most errors come from misreading what a called-out "
               "part actually is (lessons 1–2).")
    return "\n".join(out) + "\n"


def run_pipeline(program_dir: str | Path, package_dir: str | Path | None = None,
                 rasterize: bool = True) -> dict:
    """Run ingestion steps; returns paths of artifacts written."""
    program_dir = Path(program_dir)
    work = program_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}

    # step 1-2: package inventory + rasterization (if a raw package exists)
    package_dir = Path(package_dir) if package_dir else program_dir / "package"
    if package_dir.exists():
        recs = inventory_package(package_dir)
        f = work / "01_file_inventory.md"
        f.write_text("# File inventory\n\n" + inventory_markdown(recs))
        artifacts["file_inventory"] = str(f)
        if rasterize:
            made = rasterize_pdfs(package_dir, work / "02_raster")
            artifacts["raster_pages"] = f"{len(made)} page(s) in {work / '02_raster'}"

    # step 3: architecture table from the data model (checkpoint artifact)
    prog = ProgramData.load(program_dir)
    f = work / "03_architecture_table.md"
    f.write_text(architecture_table(prog))
    artifacts["architecture_table"] = str(f)

    # step 4: reconciliation + compatibility findings
    findings, additions, _ = rules.run_all(prog)
    f = work / "04_findings.md"
    body = ["# Findings (reconciliation, cascade, compatibility)", "",
            findings_to_markdown(findings), "",
            "## Spec-cascaded additions", "",
            "| Harness | Part | Qty/harness | Required by | Rule | Source | Status |",
            "|---|---|---|---|---|---|---|"]
    for a in additions:
        body.append(f"| {a.harness} | {a.mpn} | {a.qty_per_harness:g} | "
                    f"{a.required_by} | {a.when} | {a.citation.short()} | {a.note} |")
    f.write_text("\n".join(body) + "\n")
    artifacts["findings"] = str(f)

    # checkpoint status
    cps = Checkpoints.load(program_dir)
    f = work / "05_checkpoints.md"
    f.write_text("# Checkpoints\n\n" + cps.summary_markdown() +
                 "\nGates: costing requires " +
                 f"{ARCHITECTURE} + {VOLUME_UNITS}; procurement additionally "
                 f"requires {BLOCKERS}.\n")
    artifacts["checkpoints"] = str(f)
    return artifacts
