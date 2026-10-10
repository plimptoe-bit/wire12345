"""GUI backend and demo-packer tests."""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness_planner.gui import Backend  # noqa: E402

FIX = ROOT / "data" / "fixtures"
INV = ROOT / "data" / "tool_inventory.csv"


@pytest.fixture()
def backend(tmp_path):
    shutil.copytree(FIX / "previous_program", tmp_path / "previous_program")
    return Backend([tmp_path], inventory=INV)


def test_list_programs(backend):
    progs = backend.list_programs()
    assert progs[0]["name"] == "ETHDTM-2025"
    assert progs[0]["checkpoints"]["CONFIRM_ARCHITECTURE"]["status"] == "confirmed"
    assert len(progs[0]["harnesses"]) == 7


def test_check_and_generate_and_files(backend):
    chk = backend.check("previous_program")
    assert any(f["severity"] == "blocker" for f in chk["findings"])
    assert any(a["mpn"] == "SHLD-BRL-01" for a in chk["additions"])
    res = backend.generate("previous_program")
    assert any("costing" in p for p in res["produced"])
    files = backend.list_files("previous_program")
    names = {f["name"] for f in files}
    assert "bom.csv" in names
    assert any(n.startswith("formboards/") for n in names)


def test_confirm_requires_name(backend):
    with pytest.raises(ValueError):
        backend.confirm("previous_program", "VALIDATE_FIRST_BOARD", by="  ")
    cps = backend.confirm("previous_program", "VALIDATE_FIRST_BOARD",
                          by="tester", notes="measured OK")
    assert cps["VALIDATE_FIRST_BOARD"]["status"] == "confirmed"


def test_no_path_traversal(backend):
    backend.generate("previous_program")
    with pytest.raises(KeyError):
        backend.file_path("previous_program", "../../tool_inventory.csv")
    with pytest.raises(KeyError):
        backend.file_path("nope", "bom.csv")


def test_unknown_checkpoint_rejected(backend):
    with pytest.raises(KeyError):
        backend.confirm("previous_program", "NOT_A_CHECKPOINT", by="x")


def test_demo_build(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import build_demo
    out = build_demo.build(tmp_path / "demo.html")
    text = out.read_text()
    assert "/*__DEMO_DATA__*/null" not in text
    assert "ETHDTM-2025" in text and "GOLF-RF-2025" in text
    assert "SHLD-BRL-01" in text            # findings packed in
    assert out.stat().st_size < 16 * 1024 * 1024
    # no live </script> smuggled in from packed content
    body = text.split('<script id="demo-data">', 1)[1]
    payload = body.split("</script>", 1)[0]
    assert "</script" not in payload.replace("<\\/script", "")
