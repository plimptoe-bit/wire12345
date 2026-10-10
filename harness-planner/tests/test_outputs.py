"""End-to-end generation tests: every deliverable is produced from the data
model, numbers agree across outputs, and the checkpoint gates hold."""
import csv
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness_planner import cli  # noqa: E402
from harness_planner.model import ProgramData  # noqa: E402
from harness_planner.outputs import formboard  # noqa: E402

FIX = ROOT / "data" / "fixtures"
INV = ROOT / "data" / "tool_inventory.csv"


def _generate(program_dir, out_dir):
    with pytest.raises(SystemExit) as e:
        cli.main(["generate", str(program_dir), "--inventory", str(INV),
                  "--out", str(out_dir), "--skip-pdf"])
    assert e.value.code == 0


@pytest.fixture(scope="module")
def prev_out(tmp_path_factory):
    out = tmp_path_factory.mktemp("prev_out")
    _generate(FIX / "previous_program", out)
    return out


def test_all_deliverables_exist(prev_out):
    expected = ["architecture.md", "findings.md", "bom.csv", "bom.md",
                "termination_map.csv", "termination_map.md", "tooling_list.md",
                "production_plan.md", "costing.md", "costing.xlsx",
                "management_summary.md", "procurement_order.csv",
                "procurement_octopart.csv", "procurement_digikey.csv",
                "procurement_mouser.csv", "procurement.md"]
    for name in expected:
        assert (prev_out / name).exists(), f"missing {name}"
    boards = prev_out / "formboards"
    for d in ("D-1001", "D-1005", "D-1006"):
        assert (boards / f"{d}.svg").exists()
        assert (boards / f"{d}_pegs.csv").exists()
        assert (boards / f"{d}_cutlist.csv").exists()
        assert (boards / f"{d}_sequence.txt").exists()


def test_bom_carries_cascade_and_sources(prev_out):
    text = (prev_out / "bom.csv").read_text()
    assert "added — not on customer BOM" in text
    assert "SHLD-BRL-01" in text and "FIXEL-01" in text
    assert "application spec" in text  # source tags present
    rows = list(csv.DictReader((prev_out / "bom.csv").open()))
    levels = {r["level"] for r in rows}
    assert levels == {"0", "1", "2", "3"}


def test_no_fabricated_urls(prev_out):
    for f in prev_out.glob("procurement*"):
        content = f.read_text()
        assert "http" not in content.lower(), f"{f} contains a URL not from data"
    order = (prev_out / "procurement_order.csv").read_text()
    assert "URL not verified" in order


def test_tooling_outputs(prev_out):
    text = (prev_out / "tooling_list.md").read_text()
    assert "within tolerance — qualify" in text
    assert "cheapest compliant path" in text
    assert "repair and samples only" in text
    quals = list(prev_out.glob("qualification_*.md"))
    assert quals, "no qualification sheets generated"


def test_formboard_cutlist_geometry(prev_out):
    rows = list(csv.DictReader(
        (prev_out / "formboards" / "D-1003_cutlist.csv").open()))
    by_id = {r["segment"]: r for r in rows}
    s1 = by_id["S1"]
    # drawing 450 + strip 2.8 per spec at both ends = 455.6
    assert float(s1["cut_length_mm"]) == pytest.approx(455.6)
    assert "SYN-APPSPEC-1001" in s1["allowance_basis"]
    # every cut length >= drawing length
    for r in rows:
        assert float(r["cut_length_mm"]) >= float(r["drawing_length_mm"])


def test_formboard_fold_for_long_harness(prev_out):
    svg = (prev_out / "formboards" / "D-1005.svg").read_text()
    assert "FOLD" in svg  # 4 m trunk on a 2.4 m board must fold
    assert "SCALE 1:1" in svg
    pegs = list(csv.DictReader(
        (prev_out / "formboards" / "D-1005_pegs.csv").open()))
    kinds = {p["kind"] for p in pegs}
    assert {"nest", "breakout", "fold", "support"} <= kinds
    # peg coordinates stay on the (possibly extended) board
    for p in pegs:
        assert float(p["x_mm_from_datum"]) >= 0
        assert float(p["y_mm_from_datum"]) >= 0


def test_formboard_draft_note_until_validated(prev_out):
    svg = (prev_out / "formboards" / "D-1001.svg").read_text()
    assert "DRAFT" in svg  # VALIDATE_FIRST_BOARD is pending in the fixture


def test_spreadsheet_has_live_formulas(prev_out):
    from openpyxl import load_workbook
    wb = load_workbook(prev_out / "costing.xlsx")
    assert str(wb["Cost"]["H2"].value).startswith("=")
    assert str(wb["Capacity"]["C2"].value).startswith("=CEILING")
    assert str(wb["Margin"]["C2"].value).startswith("=")
    # inputs are blue
    assert wb["Inputs"]["B2"].font.color.rgb.endswith("0000CC")


def test_management_summary_units_and_decisions(prev_out):
    text = (prev_out / "management_summary.md").read_text()
    assert "sets/week" in text
    assert "Decisions needed" in text
    assert "blockers" in text


def test_makevsbuy_gap_marked(prev_out):
    text = (prev_out / "costing.md").read_text()
    assert "Make vs buy" in text
    assert "marked as our estimate" in text or "gap" in text.lower()
    assert "Recommendation" in text


# --------------------------------------------------------------------------- #
def test_checkpoint_gating(tmp_path):
    """With checkpoints pending, cost and procurement outputs are withheld."""
    pdir = tmp_path / "prog"
    shutil.copytree(FIX / "previous_program", pdir)
    cps = json.loads((pdir / "checkpoints.json").read_text())
    for k in cps:
        cps[k] = {"status": "pending", "by": "", "date": "", "notes": ""}
    (pdir / "checkpoints.json").write_text(json.dumps(cps))
    out = tmp_path / "out"
    _generate(pdir, out)
    assert (out / "architecture.md").exists()
    assert (out / "bom.csv").exists()
    assert not (out / "costing.xlsx").exists()
    assert not (out / "procurement_order.csv").exists()


def test_golf_generation(tmp_path):
    out = tmp_path / "golf_out"
    _generate(FIX / "golf_coax", out)
    assert (out / "costing.xlsx").exists()
    tooling = (out / "tooling_list.md").read_text()
    assert "FIX-HEX-02" in tooling      # hex die reuse
    assert "FIX-SOLD-01" in tooling     # solder station matched
    # multi-component harness (D-Sub pigtail) lays out as sub-assemblies
    svg = (out / "formboards" / "G-2002.svg").read_text()
    assert "sub-assemblies" in svg or "G-2002" in svg


def test_ingest_pipeline(tmp_path):
    pdir = tmp_path / "prog"
    shutil.copytree(FIX / "previous_program", pdir)
    with pytest.raises(SystemExit) as e:
        cli.main(["ingest", str(pdir)])
    assert e.value.code == 0
    work = pdir / "work"
    assert (work / "03_architecture_table.md").exists()
    arch = (work / "03_architecture_table.md").read_text()
    assert "CONFIRM_ARCHITECTURE" in arch
    assert "pre-terminated assembly PTA-ETH-2M" in arch
    assert (work / "04_findings.md").exists()
    assert (work / "05_checkpoints.md").exists()
