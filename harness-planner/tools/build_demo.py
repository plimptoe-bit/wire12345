"""Pack the GUI and the example outputs into one double-clickable HTML file.

    python3 tools/build_demo.py            # writes ../HarnessPlannerXP.html

The result is the same page the `gui` command serves, with the example
programs' generated deliverables embedded (demo mode): open it in any browser
with no install. Binary PDFs are left out (the SVG boards are shown instead);
the costing workbooks ride along base64-encoded so they can be saved when the
file is opened locally.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness_planner import rules                      # noqa: E402
from harness_planner.gui import _group_for             # noqa: E402
from harness_planner.inventory import Inventory        # noqa: E402
from harness_planner.ingest import Checkpoints         # noqa: E402
from harness_planner.ingest.checkpoints import ALL     # noqa: E402
from harness_planner.model import ProgramData          # noqa: E402

TEXT_EXT = {".md", ".csv", ".svg", ".txt", ".json"}
B64_EXT = {".xlsx"}
SKIP_EXT = {".pdf", ".png"}

PROGRAMS = [
    ("previous_program", ROOT / "data/fixtures/previous_program",
     ROOT / "examples/previous_program"),
    ("golf_coax", ROOT / "data/fixtures/golf_coax",
     ROOT / "examples/golf_coax"),
]


def pack_files(examples_dir: Path) -> list[dict]:
    out = []
    for f in sorted(examples_dir.rglob("*")):
        if not f.is_file() or f.suffix in SKIP_EXT:
            continue
        rel = str(f.relative_to(examples_dir))
        entry = {
            "path": rel, "name": rel, "group": _group_for(rel),
            "ext": f.suffix.lstrip("."),
            "size_kb": round(f.stat().st_size / 1024, 1),
        }
        if f.suffix in TEXT_EXT:
            entry["content"] = f.read_text()
        elif f.suffix in B64_EXT:
            entry["b64"] = base64.b64encode(f.read_bytes()).decode()
        else:
            continue
        out.append(entry)
    return out


def pack_program(pid: str, fixture_dir: Path, examples_dir: Path,
                 inv: Inventory) -> dict:
    prog = ProgramData.load(fixture_dir)
    cps = Checkpoints.load(fixture_dir)
    findings, additions, _ = rules.run_all(prog, inv)
    return {
        "id": pid,
        "name": prog.meta.name,
        "customer": prog.meta.customer,
        "revision": prog.meta.revision,
        "date": prog.meta.date,
        "volume_unit": prog.meta.volume_unit,
        "volumes": prog.meta.volumes_per_week,
        "planned_volumes": prog.meta.planned_volumes(),
        "harnesses": [{"drawing": h.drawing_number, "rev": h.revision,
                       "name": h.name or h.family, "qty_per_set": h.qty_per_set}
                      for h in prog.harnesses],
        "checkpoints": {c: cps.data.get(c, {}) for c in ALL},
        "check": {
            "findings": [{
                "id": f.id, "severity": f.severity, "check": f.check,
                "harness": f.harness, "ref": f.ref, "message": f.message,
                "source": f.cite(), "proposed_default": f.proposed_default,
            } for f in findings],
            "additions": [{
                "harness": a.harness, "mpn": a.mpn,
                "qty_per_harness": a.qty_per_harness,
                "required_by": a.required_by, "when": a.when,
                "source": a.citation.short(), "note": a.note,
            } for a in additions],
        },
        "files": pack_files(examples_dir),
    }


def build(out_path: Path | None = None) -> Path:
    out_path = out_path or ROOT / "HarnessPlannerXP.html"
    inv = Inventory.load(ROOT / "data" / "tool_inventory.csv")
    data = {"programs": [pack_program(pid, fx, ex, inv)
                         for pid, fx, ex in PROGRAMS if ex.exists()]}
    page = (ROOT / "harness_planner" / "gui" / "index.html").read_text()
    marker = "/*__DEMO_DATA__*/null"
    if marker not in page:
        raise SystemExit("demo marker not found in gui/index.html")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace(marker, blob)
    out_path.write_text(page)
    size = out_path.stat().st_size / 1024
    print(f"wrote {out_path} ({size:,.0f} KB, "
          f"{len(data['programs'])} program(s))")
    return out_path


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
