"""Shop tool inventory: a persistent CSV table that run mode updates.

Columns mirror the Tool entity. The file lives outside any single program so
every program sees the same shop state. Run-mode update process:

  * new purchase        -> Inventory.add(tool)
  * weekly cycle counts -> Inventory.add_cycles(mpn, cycles)
  * calibration done    -> Inventory.set_certified(mpn, date)

The CSV is the source of truth; keep it in git so changes are reviewable.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field, fields
from datetime import date
from pathlib import Path

from .sources import Citation

CSV_COLUMNS = [
    "mpn", "manufacturer", "tool_class", "description",
    "crimp_form", "nest_sizes",
    "height_min_mm", "height_max_mm", "width_min_mm", "width_max_mm",
    "wire_min_mm2", "wire_max_mm2", "insulation_min_mm", "insulation_max_mm",
    "feed_type", "terminal_families",
    "certification_status", "certification_date", "calibration_interval_months",
    "cycle_count", "cycle_life", "location", "cost", "in_inventory",
    "restrictions", "source_doc",
]

TOOL_CLASSES = [
    "hand_crimp", "die_set", "frame", "applicator", "press", "stripper",
    "coax_stripper", "solder_station", "solder_tip", "hex_die", "tester",
    "gauge", "fixture", "other",
]


@dataclass
class Tool:
    mpn: str
    manufacturer: str = ""
    tool_class: str = "hand_crimp"
    description: str = ""
    crimp_form: str = ""          # F|B|closed|hex|4-indent|wrap|solder|n/a
    nest_sizes: str = ""          # free text, e.g. "0.64 NanoMQS; h=0.78/w=0.95"
    height_min_mm: float | None = None
    height_max_mm: float | None = None
    width_min_mm: float | None = None
    width_max_mm: float | None = None
    wire_min_mm2: float | None = None
    wire_max_mm2: float | None = None
    insulation_min_mm: float | None = None
    insulation_max_mm: float | None = None
    feed_type: str = "loose"      # loose|reel|n/a
    terminal_families: str = ""   # ';'-separated family names the vendor names
    certification_status: str = "uncertified"  # certified|due|uncertified
    certification_date: str = ""
    calibration_interval_months: float | None = 12
    cycle_count: int = 0
    cycle_life: int | None = None
    location: str = ""
    cost: float | None = None
    in_inventory: bool = True
    restrictions: str = ""        # e.g. "repair and samples only (408-xxxx)"
    source_doc: str = ""

    def to_row(self) -> dict:
        row = {}
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, bool):
                v = "yes" if v else "no"
            row[f.name] = "" if v is None else v
        return row

    @classmethod
    def from_row(cls, row: dict) -> "Tool":
        def num(key):
            v = row.get(key, "")
            return float(v) if str(v).strip() != "" else None

        def integer(key, default=None):
            v = row.get(key, "")
            return int(float(v)) if str(v).strip() != "" else default

        return cls(
            mpn=row["mpn"].strip(),
            manufacturer=row.get("manufacturer", ""),
            tool_class=row.get("tool_class", "hand_crimp"),
            description=row.get("description", ""),
            crimp_form=row.get("crimp_form", ""),
            nest_sizes=row.get("nest_sizes", ""),
            height_min_mm=num("height_min_mm"), height_max_mm=num("height_max_mm"),
            width_min_mm=num("width_min_mm"), width_max_mm=num("width_max_mm"),
            wire_min_mm2=num("wire_min_mm2"), wire_max_mm2=num("wire_max_mm2"),
            insulation_min_mm=num("insulation_min_mm"),
            insulation_max_mm=num("insulation_max_mm"),
            feed_type=row.get("feed_type", "loose"),
            terminal_families=row.get("terminal_families", ""),
            certification_status=row.get("certification_status", "uncertified"),
            certification_date=row.get("certification_date", ""),
            calibration_interval_months=num("calibration_interval_months"),
            cycle_count=integer("cycle_count", 0) or 0,
            cycle_life=integer("cycle_life"),
            location=row.get("location", ""),
            cost=num("cost"),
            in_inventory=str(row.get("in_inventory", "yes")).lower()
            in ("yes", "true", "1"),
            restrictions=row.get("restrictions", ""),
            source_doc=row.get("source_doc", ""),
        )


class Inventory:
    def __init__(self, tools: list[Tool], path: Path | None = None):
        self.tools = tools
        self.path = path

    @classmethod
    def load(cls, path: str | Path) -> "Inventory":
        path = Path(path)
        tools = []
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if row.get("mpn", "").strip():
                    tools.append(Tool.from_row(row))
        return cls(tools, path=path)

    def save(self, path: str | Path | None = None):
        path = Path(path or self.path)
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            w.writeheader()
            for t in self.tools:
                w.writerow(t.to_row())

    # ---- run-mode update process ------------------------------------- #
    def get(self, mpn: str) -> Tool | None:
        for t in self.tools:
            if t.mpn == mpn:
                return t
        return None

    def add(self, tool: Tool):
        if self.get(tool.mpn):
            raise ValueError(f"tool {tool.mpn} already in inventory")
        self.tools.append(tool)

    def add_cycles(self, mpn: str, cycles: int):
        t = self.get(mpn)
        if not t:
            raise KeyError(mpn)
        t.cycle_count += int(cycles)

    def set_certified(self, mpn: str, on: str | date | None = None):
        t = self.get(mpn)
        if not t:
            raise KeyError(mpn)
        t.certification_status = "certified"
        t.certification_date = str(on or date.today())

    def owned(self) -> list[Tool]:
        return [t for t in self.tools if t.in_inventory]
