"""Regression tests: the Part 7 lessons, run against the previous program's
(synthetic) data. Each test asserts the engine catches the specific failure
class that bit us last time."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness_planner import rules                                    # noqa: E402
from harness_planner.inventory import Inventory                      # noqa: E402
from harness_planner.model import ProgramData                        # noqa: E402
from harness_planner.rules import compatibility, reconcile, tooling  # noqa: E402

FIX = ROOT / "data" / "fixtures"


@pytest.fixture(scope="module")
def prev():
    compatibility.reset_counter()
    reconcile.reset_counter()
    return ProgramData.load(FIX / "previous_program")


@pytest.fixture(scope="module")
def inv():
    return Inventory.load(ROOT / "data" / "tool_inventory.csv")


@pytest.fixture(scope="module")
def results(prev, inv):
    findings, additions, groups = rules.run_all(prev, inv)
    return findings, additions, groups


def by_lesson(findings, tag):
    return [f for f in findings if f.lesson == tag]


# --------------------------------------------------------------------------- #
def test_lesson1_preterminated_assembly_detected(results):
    """A connector call-out that is actually a factory-terminated assembly."""
    findings, _, _ = results
    hits = by_lesson(findings, "lesson-1")
    assert any("factory-terminated" in f.message for f in hits), hits
    # and the never-needed loose contacts are called out
    assert any("TERM-NANO-ETH" in f.message and "not needed" in f.message
               for f in hits), hits
    assert all(f.severity == "blocker" for f in hits)


def test_lesson2_cascade_adds_missing_accessories(results):
    """Shield barrel + fixation element required by spec, absent from BOM."""
    findings, additions, _ = results
    added = {a.mpn for a in additions if not a.on_customer_bom}
    assert "SHLD-BRL-01" in added
    assert "FIXEL-01" in added
    hits = by_lesson(findings, "lesson-2")
    assert any("SHLD-BRL-01" in f.message for f in hits)
    assert any("FIXEL-01" in f.message for f in hits)
    # every cascade addition carries a spec citation
    for a in additions:
        assert a.citation.doc or a.citation.note, a
    # a spec-required part that IS on the BOM is marked as present, not added
    tpa = [a for a in additions if a.mpn == "TPA-NANO-4"]
    assert tpa and all(a.on_customer_bom for a in tpa)


def test_lesson3_contact_count_mismatch(results):
    """3 inserts x 2 contacts = 6 needed; BOM lists 2."""
    findings, _, _ = results
    hits = [f for f in by_lesson(findings, "lesson-3")
            if "TERM-PIN-N22" in f.message]
    assert hits, "contact count mismatch not caught"
    f = hits[0]
    assert f.severity == "blocker"
    assert "6" in f.message and "2" in f.message


def test_lesson4_wire_range_and_plating(results):
    """0.96 mm2 wire into a 0.5-0.75 receptacle; Ni pin on 0.34 mm2 wire that
    the product spec validates only with Au."""
    findings, _, _ = results
    hits = by_lesson(findings, "lesson-4")
    assert any(f.check == "wire_range" and "RCPT-GC-075" in f.message
               for f in hits), hits
    assert any(f.check == "plating_validation" and "TERM-PIN-N22" in f.message
               for f in hits), hits


def test_lesson5_insulation_od_variant(prev, results):
    """Measured OD 1.73-1.78 puts the wire in a different insulation variant."""
    findings, _, _ = results
    hits = by_lesson(findings, "lesson-5")
    assert any("W-M22" in f.message and "TERM-NANO-050" in f.message
               for f in hits), hits
    # and the engine can propose the correct sibling variant
    term = prev.part("TERM-NANO-050")
    wire = prev.part("W-M22")
    variant = compatibility.suggest_variant(prev, term, wire)
    assert variant is not None and variant.mpn == "TERM-NANO-050-B"


def test_lesson6_tool_restriction_surfaced_not_mandated(results):
    """'Repair and samples only' is presented as guidance with the risk named,
    not as a hard stop."""
    findings, _, groups = results
    restr = [f for f in findings if f.check == "tooling_restriction"]
    assert any("repair and samples only" in f.message for f in restr), restr
    assert all(f.severity == "warning" for f in restr)
    # the tool is still the chosen cheapest path
    nano = next(g for g in groups if g.key == "TERM-NANO-050")
    assert nano.chosen_path and "FIX-HT-0640" in nano.chosen_path.name


def test_lesson11_inventory_match_ranked_with_qualification(results):
    """Owner policy: a tool is compatible if it forms the crimp to spec height
    and width; rank matches and generate the qualification protocol."""
    _, _, groups = results
    gc = next(g for g in groups if g.key == "RCPT-GC-075")
    verdicts = {m.tool.mpn: m.verdict for m in gc.matches}
    assert verdicts.get("FIX-HT-F2") == "qualify"
    assert gc.qualification_needed
    mat = next(g for g in groups if g.key == "TERM-MAT-CONT")
    assert any(m.verdict == "qualify" and m.tool.mpn == "FIX-HT-0640"
               for m in mat.matches)
    # exact family match ranks first for the DTM contact
    dtm = next(g for g in groups if g.key == "TERM-DTM-16")
    assert dtm.matches and dtm.matches[0].tool.mpn == "FIX-4IND-16"
    assert dtm.matches[0].verdict == "exact"
    # no inventory match for the machined M12 pin -> buy the named tool
    m12 = next(g for g in groups if g.key == "TERM-PIN-N22")
    assert all(m.verdict == "no" for m in m12.matches)
    assert m12.chosen_path and "TOOL-M12-HAND" in m12.chosen_path.name


def test_preterminated_housings_not_double_counted(prev):
    """Housings on factory-terminated ends come with the assembly."""
    from harness_planner.rules.quantities import demand_per_set
    per_set = demand_per_set(prev)
    assert per_set.get("CONN-MAT-HDR", 0) == 0
    assert per_set.get("PTA-ETH-2M") == 2  # 1 whole + 2 x half


def test_qualification_protocol_contents(prev, inv, results):
    _, _, groups = results
    gc = next(g for g in groups if g.key == "RCPT-GC-075")
    tool = inv.get("FIX-HT-F2")
    text = tooling.qualification_protocol(prev, gc, tool)
    assert "10 samples" in text
    assert "3 cross-sections" in text
    assert "Pull test" in text
    assert "customer deviation" in text
    assert "1.9" in text  # spec crimp height carried into the sheet


# --------------------------------------------------------------------------- #
# solder/coax sample


@pytest.fixture(scope="module")
def golf():
    return ProgramData.load(FIX / "golf_coax")


def test_golf_coax_group_mismatch(golf, inv):
    findings, _, _ = rules.run_all(golf, inv)
    assert any(f.check == "coax_cable_group" and "BNC-STR-58" in f.message
               for f in findings)


def test_golf_solder_temp_rating(golf, inv):
    findings, _, _ = rules.run_all(golf, inv)
    assert any(f.check == "solder_temp_rating" and "W-HOOK-22" in f.message
               for f in findings)


def test_golf_moq_flag(golf, inv):
    findings, _, _ = rules.run_all(golf, inv)
    assert any(f.check == "moq_vs_need" and "BNC-STR-58" in f.message
               for f in findings)


def test_golf_hex_tooling_from_inventory(golf, inv):
    _, _, groups = rules.run_all(golf, inv)
    pin = next(g for g in groups if g.key == "PIN-SMA-174")
    assert any(m.tool.mpn == "FIX-HEX-02" and m.verdict in ("exact", "qualify")
               for m in pin.matches)


def test_golf_placeholder_bom_line(golf, inv):
    findings, _, _ = rules.run_all(golf, inv)
    assert any(f.check == "bom_reconcile" and "tape, see drawing" in f.message
               for f in findings)
