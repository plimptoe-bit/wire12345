import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness_planner.model import ProgramData, validate_program  # noqa: E402

FIX = ROOT / "data" / "fixtures"


def test_load_both_fixtures_validate():
    prev = ProgramData.load(FIX / "previous_program")
    golf = ProgramData.load(FIX / "golf_coax")
    assert len(prev.harnesses) == 7
    assert len(golf.harnesses) == 2
    assert prev.meta.planned_volumes() == [10, 30, 50, 75, 100]
    assert golf.meta.planned_volumes() == [5, 15, 22.5, 30]


def test_sources_tagged():
    prev = ProgramData.load(FIX / "previous_program")
    term = prev.part("TERM-NANO-050")
    assert term.source.rank == 1
    assert "SYN-APPSPEC-1001" in term.source.short()
    assert "Rev B" in term.source.short()


def test_referential_integrity_enforced():
    raw = json.loads((FIX / "previous_program" / "program.json").read_text())
    bad = copy.deepcopy(raw)
    bad["harnesses"][0]["segments"][0]["to_node"] = "NOPE"
    with pytest.raises(ValueError, match="missing node NOPE"):
        validate_program(bad)
    bad2 = copy.deepcopy(raw)
    bad2["harnesses"][0]["terminations"][0]["terminal_mpn"] = "NOT-A-PART"
    with pytest.raises(ValueError, match="unknown part NOT-A-PART"):
        validate_program(bad2)


def test_price_tiers():
    prev = ProgramData.load(FIX / "previous_program")
    p = prev.part("TERM-NANO-050")
    assert p.price_at(10) == 0.09
    assert p.price_at(5000) == 0.06


def test_roundtrip_save(tmp_path):
    prev = ProgramData.load(FIX / "previous_program")
    prev.save(tmp_path / "program.json")
    again = ProgramData.load(tmp_path / "program.json")
    assert len(again.parts) == len(prev.parts)
