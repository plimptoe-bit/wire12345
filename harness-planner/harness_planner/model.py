"""Data model for a harness program.

A program is a single JSON file (see schema/program.schema.json) plus the
shop-wide tool inventory CSV. Every record carries a Citation so each number
in a deliverable traces back to a source.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .sources import Citation

# --------------------------------------------------------------------------- #
# small helpers


def _cit(d: dict, key: str = "source") -> Citation:
    return Citation.from_dict(d.get(key))


def _rng(v) -> tuple[float, float] | None:
    """Normalize a [min, max] range from JSON."""
    if v is None:
        return None
    return (float(v[0]), float(v[1]))


# --------------------------------------------------------------------------- #
# program-level records


@dataclass
class Rates:
    technician_rate_per_hour: float = 35.0
    loaded_multiplier: float = 1.6
    productive_hours_per_week: float = 30.0
    weeks_per_year: int = 48
    depreciation_years: float = 3.0
    overhead_per_set: float = 0.0
    scrap_fraction: float = 0.03
    currency: str = "USD"
    source: Citation = field(default_factory=Citation)

    @classmethod
    def from_dict(cls, d: dict) -> "Rates":
        d = dict(d or {})
        src = Citation.from_dict(d.pop("source", None))
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known, source=src) if "source" not in known else cls(**known)


@dataclass
class ProgramMeta:
    name: str
    customer: str = ""
    revision: str = ""
    date: str = ""
    volume_unit: str = "sets/week"
    volumes_per_week: list[float] = field(default_factory=list)
    upper_limit_factors: list[float] = field(default_factory=lambda: [1.5, 2.0])
    horizon_weeks: int = 52
    rates: Rates = field(default_factory=Rates)
    selling_price_per_set: float | None = None
    workmanship_standard: str = "IPC/WHMA-A-620 Class 2"
    notes: str = ""

    def planned_volumes(self) -> list[float]:
        """Customer's planned volumes plus the upper-limit factors on the max."""
        vols = sorted(set(float(v) for v in self.volumes_per_week))
        if vols:
            top = max(vols)
            for f in self.upper_limit_factors:
                vols.append(round(top * f, 2))
        return sorted(set(vols))


# --------------------------------------------------------------------------- #
# parts and documents


@dataclass
class Document:
    id: str
    number: str = ""
    title: str = ""
    revision: str = ""
    rank: int = 6
    url: str | None = None
    url_verified: bool = False
    file: str | None = None
    notes: str = ""


@dataclass
class PriceTier:
    min_qty: float
    unit_price: float


@dataclass
class Part:
    mpn: str
    manufacturer: str = ""
    description: str = ""
    category: str = "accessory"  # terminal|housing|seal|lock|accessory|wire|cable|
    #                              preterminated_assembly|tape|label|heat_shrink|
    #                              consumable|connector_module|tool
    uom: str = "ea"
    package_qty: float = 1
    moq: float = 1
    price_tiers: list[PriceTier] = field(default_factory=list)
    lead_time_weeks: float | None = None
    distributor_links: list[dict] = field(default_factory=list)
    governing_docs: list[str] = field(default_factory=list)
    consigned: bool = False
    attrs: dict = field(default_factory=dict)
    source: Citation = field(default_factory=Citation)

    # ---- typed accessors over attrs (None = unknown) ----------------------- #
    @property
    def wire_range_mm2(self):
        return _rng(self.attrs.get("wire_range_mm2"))

    @property
    def insulation_od_range_mm(self):
        return _rng(self.attrs.get("insulation_od_range_mm"))

    @property
    def seal_range_mm(self):
        return _rng(self.attrs.get("seal_range_mm"))

    @property
    def plating(self):
        return self.attrs.get("plating")

    @property
    def validated_combinations(self) -> list[dict]:
        """[{plating, wire_mm2_range:[lo,hi], citation}] from the product spec."""
        return self.attrs.get("validated_combinations", [])

    @property
    def crimp(self) -> dict:
        """Crimp geometry from the application spec:
        {form, height_mm, height_tol_mm, width_mm, width_tol_mm,
         strip_length_mm, pull_force_min_n}"""
        return self.attrs.get("crimp", {})

    @property
    def cavities(self) -> int | None:
        return self.attrs.get("cavities")

    @property
    def contact_family(self):
        return self.attrs.get("contact_family")

    @property
    def family(self):
        return self.attrs.get("family")

    @property
    def named_tools(self) -> list[str]:
        return self.attrs.get("named_tools", [])

    @property
    def required_accessories(self) -> list[dict]:
        """[{when, mpn, qty_per, citation}] — accessory cascade rules.
        when: always|shielded_termination|sealed_termination|empty_cavity|per_housing
        """
        return self.attrs.get("required_accessories", [])

    @property
    def conductor_mm2(self):
        return self.attrs.get("conductor_mm2")

    @property
    def shield(self):
        return self.attrs.get("shield", "none")  # none|braid|foil|both

    @property
    def coax_group(self):
        return self.attrs.get("coax_group")

    @property
    def temp_rating_c(self):
        return self.attrs.get("temp_rating_c")

    @property
    def variant_group(self):
        """Parts that are insulation-range variants of the same terminal."""
        return self.attrs.get("variant_group")

    @property
    def keying(self):
        return self.attrs.get("keying")

    def price_at(self, qty: float) -> float | None:
        best = None
        for t in sorted(self.price_tiers, key=lambda t: t.min_qty):
            if qty >= t.min_qty:
                best = t.unit_price
        if best is None and self.price_tiers:
            best = sorted(self.price_tiers, key=lambda t: t.min_qty)[0].unit_price
        return best

    @classmethod
    def from_dict(cls, d: dict) -> "Part":
        d = dict(d)
        tiers = [PriceTier(float(t["min_qty"]), float(t["unit_price"]))
                 for t in d.pop("price_tiers", [])]
        src = Citation.from_dict(d.pop("source", None))
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**{**known, "price_tiers": tiers, "source": src})


# --------------------------------------------------------------------------- #
# harness topology


@dataclass
class Node:
    id: str
    kind: str = "connector"  # connector|breakout|splice|end|label_point
    housing_mpn: str | None = None
    label: str = ""
    mate_orientation: str = ""  # free text for the formboard nest note


@dataclass
class Segment:
    id: str
    part_mpn: str            # wire or cable MPN (or preterminated assembly MPN)
    from_node: str
    to_node: str
    length_mm: float
    tol_mm: float = 5.0
    source: str = "reel"     # reel|preterminated|cut_half
    circuit: str = ""        # wire ID / circuit name
    color: str = ""
    branch_angle_deg: float | None = None  # from drawing; None = convention
    length_convention: str = ""  # e.g. "connector face to connector face"
    citation: Citation = field(default_factory=Citation)

    @classmethod
    def from_dict(cls, d: dict) -> "Segment":
        d = dict(d)
        cit = Citation.from_dict(d.pop("citation", None) or d.pop("source_cit", None))
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**{**known, "citation": cit})


@dataclass
class Termination:
    id: str
    node: str
    segment: str
    end: str = "A"            # A = from_node end, B = to_node end
    ttype: str = "crimp_open_barrel"
    # crimp_open_barrel|crimp_closed_barrel|crimp_hex|solder_cup|solder_sleeve|
    # idc|screw|weld|preterminated|shield_termination
    terminal_mpn: str | None = None
    housing_mpn: str | None = None
    cavity: str | None = None
    sealed: bool = False
    shielded: bool = False
    accessories: list[str] = field(default_factory=list)  # MPNs from drawing
    process_params: dict = field(default_factory=dict)
    citation: Citation = field(default_factory=Citation)

    @classmethod
    def from_dict(cls, d: dict) -> "Termination":
        d = dict(d)
        cit = Citation.from_dict(d.pop("citation", None))
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**{**known, "citation": cit})


@dataclass
class Harness:
    drawing_number: str
    revision: str = ""
    family: str = "general"   # ethernet|power|coax_solder|general ...
    name: str = ""
    qty_per_set: float = 1
    overall_length_mm: float | None = None
    test_requirements: str = ""
    labels: list[dict] = field(default_factory=list)
    # labels: [{text, segment, from_node, offset_mm}]
    tapes: list[dict] = field(default_factory=list)
    # tapes: [{mpn, segment, from_mm, to_mm, kind, note}]
    nodes: list[Node] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    terminations: list[Termination] = field(default_factory=list)
    length_convention: str = ""
    citation: Citation = field(default_factory=Citation)

    def node(self, nid: str) -> Node:
        for n in self.nodes:
            if n.id == nid:
                return n
        raise KeyError(f"{self.drawing_number}: node {nid} not found")

    def segment(self, sid: str) -> Segment:
        for s in self.segments:
            if s.id == sid:
                return s
        raise KeyError(f"{self.drawing_number}: segment {sid} not found")

    def terminations_at(self, node_id: str) -> list[Termination]:
        return [t for t in self.terminations if t.node == node_id]

    @classmethod
    def from_dict(cls, d: dict) -> "Harness":
        d = dict(d)
        nodes = [Node(**{k: v for k, v in n.items() if k in Node.__dataclass_fields__})
                 for n in d.pop("nodes", [])]
        segs = [Segment.from_dict(s) for s in d.pop("segments", [])]
        terms = [Termination.from_dict(t) for t in d.pop("terminations", [])]
        cit = Citation.from_dict(d.pop("citation", None))
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**{**known, "nodes": nodes, "segments": segs,
                      "terminations": terms, "citation": cit})


# --------------------------------------------------------------------------- #
# customer BOM, assumptions, open items


@dataclass
class BomLine:
    line: str
    mpn_as_written: str
    description_as_written: str = ""
    qty: float = 0
    basis: str = "per_harness"  # per_harness|per_set
    harness: str | None = None  # drawing number, when per_harness
    uom: str = "ea"
    notes: str = ""
    citation: Citation = field(default_factory=Citation)

    @classmethod
    def from_dict(cls, d: dict) -> "BomLine":
        d = dict(d)
        cit = Citation.from_dict(d.pop("citation", None))
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**{**known, "citation": cit})


@dataclass
class Assumption:
    id: str
    text: str
    value: Any = None
    impact: str = ""
    owner: str = "shop"
    status: str = "open"  # open|confirmed|superseded
    source: Citation = field(default_factory=Citation)


@dataclass
class OpenItem:
    id: str
    question: str
    impact: str = ""
    proposed_default: str = ""
    owner: str = "customer"
    status: str = "open"   # open|answered|closed
    answer: str = ""
    refs: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# process / equipment


@dataclass
class ProcessStep:
    id: str
    station: str
    family: str = "*"        # harness family this applies to, * = all
    description: str = ""
    minutes_per_harness_manual: float = 0.0
    minutes_per_harness_semiauto: float | None = None
    equipment_option: str | None = None  # id of EquipmentOption enabling semiauto
    basis: str = ""          # how the estimate was built
    source: Citation = field(default_factory=Citation)


@dataclass
class EquipmentOption:
    id: str
    name: str
    eq_class: str = ""
    cost_low: float = 0.0
    cost_high: float = 0.0
    rate_per_hour: float | None = None   # units/hour where it is the bottleneck
    one_time_setup_h: float = 0.0
    changeover_min: float = 0.0
    service_interval: str = ""
    calibration_cost_per_year: float = 0.0
    life_years: float = 5.0
    phase: str = "optional"  # buy_now|at_volume|optional|excluded
    phase_reason: str = ""
    replaces_station: str | None = None  # station whose manual time it reduces
    time_factor: float = 1.0             # station minutes multiplier when used
    lead_time_weeks: float = 0.0
    source: Citation = field(default_factory=Citation)


# --------------------------------------------------------------------------- #
# whole program


class ProgramData:
    """A loaded program: meta + parts + harnesses + BOM + process data."""

    def __init__(self, raw: dict, path: Path | None = None):
        self.path = path
        self.raw = raw
        p = raw["program"]
        rates = Rates.from_dict(p.get("rates", {}))
        self.meta = ProgramMeta(
            name=p["name"], customer=p.get("customer", ""),
            revision=p.get("revision", ""), date=p.get("date", ""),
            volume_unit=p.get("volume_unit", "sets/week"),
            volumes_per_week=p.get("volumes_per_week", []),
            upper_limit_factors=p.get("upper_limit_factors", [1.5, 2.0]),
            horizon_weeks=p.get("horizon_weeks", 52),
            rates=rates,
            selling_price_per_set=p.get("selling_price_per_set"),
            workmanship_standard=p.get("workmanship_standard",
                                       "IPC/WHMA-A-620 Class 2"),
            notes=p.get("notes", ""),
        )
        self.documents: dict[str, Document] = {
            d["id"]: Document(**{k: v for k, v in d.items()
                                 if k in Document.__dataclass_fields__})
            for d in raw.get("documents", [])
        }
        self.parts: dict[str, Part] = {
            d["mpn"]: Part.from_dict(d) for d in raw.get("parts", [])
        }
        self.harnesses: list[Harness] = [
            Harness.from_dict(h) for h in raw.get("harnesses", [])
        ]
        self.customer_bom: list[BomLine] = [
            BomLine.from_dict(b) for b in raw.get("customer_bom", [])
        ]
        self.assumptions: list[Assumption] = [
            Assumption(**{**{k: v for k, v in a.items()
                             if k in Assumption.__dataclass_fields__ and k != "source"},
                          "source": Citation.from_dict(a.get("source"))})
            for a in raw.get("assumptions", [])
        ]
        self.open_items: list[OpenItem] = [
            OpenItem(**{k: v for k, v in o.items()
                        if k in OpenItem.__dataclass_fields__})
            for o in raw.get("open_items", [])
        ]
        self.process_steps: list[ProcessStep] = [
            ProcessStep(**{**{k: v for k, v in s.items()
                              if k in ProcessStep.__dataclass_fields__ and k != "source"},
                           "source": Citation.from_dict(s.get("source"))})
            for s in raw.get("process_steps", [])
        ]
        self.equipment_options: list[EquipmentOption] = [
            EquipmentOption(**{**{k: v for k, v in e.items()
                                  if k in EquipmentOption.__dataclass_fields__
                                  and k != "source"},
                               "source": Citation.from_dict(e.get("source"))})
            for e in raw.get("equipment_options", [])
        ]
        self.supplier_quote: dict | None = raw.get("supplier_quote")

    # ------------------------------------------------------------------ #
    def part(self, mpn: str | None) -> Part | None:
        if mpn is None:
            return None
        return self.parts.get(mpn)

    def harness(self, drawing_number: str) -> Harness:
        for h in self.harnesses:
            if h.drawing_number == drawing_number:
                return h
        raise KeyError(drawing_number)

    def doc(self, doc_id: str) -> Document | None:
        return self.documents.get(doc_id)

    def doc_ref(self, doc_id: str) -> str:
        d = self.documents.get(doc_id)
        if not d:
            return doc_id
        return f"{d.number or d.id} {d.revision}".strip()

    # ------------------------------------------------------------------ #
    @classmethod
    def load(cls, path: str | Path) -> "ProgramData":
        path = Path(path)
        if path.is_dir():
            path = path / "program.json"
        raw = json.loads(path.read_text())
        validate_program(raw)
        return cls(raw, path=path)

    def save(self, path: str | Path | None = None):
        path = Path(path or self.path)
        path.write_text(json.dumps(self.raw, indent=2))


# --------------------------------------------------------------------------- #
# schema validation


def validate_program(raw: dict):
    import jsonschema

    schema_path = Path(__file__).parent / "schema" / "program.schema.json"
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(raw, schema)

    # Referential integrity beyond what JSON Schema covers.
    errors: list[str] = []
    mpns = {p["mpn"] for p in raw.get("parts", [])}
    for h in raw.get("harnesses", []):
        hd = h.get("drawing_number", "?")
        node_ids = {n["id"] for n in h.get("nodes", [])}
        seg_ids = set()
        for s in h.get("segments", []):
            seg_ids.add(s["id"])
            for key in ("from_node", "to_node"):
                if s[key] not in node_ids:
                    errors.append(f"{hd}: segment {s['id']} references missing node {s[key]}")
            if s["part_mpn"] not in mpns:
                errors.append(f"{hd}: segment {s['id']} references unknown part {s['part_mpn']}")
        for t in h.get("terminations", []):
            if t["node"] not in node_ids:
                errors.append(f"{hd}: termination {t['id']} references missing node {t['node']}")
            if t["segment"] not in seg_ids:
                errors.append(f"{hd}: termination {t['id']} references missing segment {t['segment']}")
            for key in ("terminal_mpn", "housing_mpn"):
                v = t.get(key)
                if v and v not in mpns:
                    errors.append(f"{hd}: termination {t['id']} references unknown part {v}")
    if errors:
        raise ValueError("program data failed referential checks:\n  " +
                         "\n  ".join(errors))
