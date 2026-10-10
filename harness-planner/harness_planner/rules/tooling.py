"""Tooling reuse engine (Part 6).

Policy: buy as few tools as possible. A tool is compatible when it forms the
crimp (or joint) to the geometry the terminal spec requires and the result
passes the spec's inspection and pull test. The manufacturer's named tool is
the default, not a requirement, at prototype/low-rate volume (lesson 11).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from ..model import Part, ProgramData
from ..inventory import Inventory, Tool
from ..sources import Citation
from .findings import Finding

# planning-estimate cycle times (minutes per termination) — assumption A-TOOL-T
HAND_CRIMP_MIN = 1.5
PRESS_CRIMP_MIN = 0.25
SOLDER_JOINT_MIN = 3.0
QUALIFICATION_HOURS = 4.0  # per tool/terminal pair: 10 samples + 3 sections + pull

FORM_FOR_TTYPE = {
    "crimp_open_barrel": "F",
    "crimp_closed_barrel": "closed",
    "crimp_hex": "hex",
    "solder_cup": "solder",
    "solder_sleeve": "solder",
}


@dataclass
class Requirement:
    form: str = ""
    height_mm: float | None = None
    height_tol_mm: float | None = None
    width_mm: float | None = None
    width_tol_mm: float | None = None
    wire_mm2: float | None = None
    insulation_od_mm: float | None = None
    strip_length_mm: float | None = None
    pull_force_min_n: float | None = None
    hex_mm: float | None = None
    family: str = ""
    citation: Citation = field(default_factory=Citation)


@dataclass
class ToolMatch:
    tool: Tool
    verdict: str          # exact | qualify | no
    evidence: str
    closeness: float = 9e9


@dataclass
class PathOption:
    name: str
    one_time_cost: float
    per_termination_min: float
    note: str = ""


@dataclass
class GroupReport:
    key: str
    description: str
    ttype: str
    requirement: Requirement
    named_tools: list[str]
    named_tool_citation: Citation
    terminations_per_set: float
    harnesses: list[str]
    matches: list[ToolMatch] = field(default_factory=list)
    paths: list[PathOption] = field(default_factory=list)
    chosen_path: PathOption | None = None
    qualification_needed: bool = False
    restrictions: list[str] = field(default_factory=list)
    cycles_per_week_at_max: float = 0.0


# --------------------------------------------------------------------------- #
def _requirement_for(prog: ProgramData, term: Part | None, wire: Part | None,
                     t) -> Requirement:
    r = Requirement()
    r.form = FORM_FOR_TTYPE.get(t.ttype, "")
    if term:
        c = term.crimp
        r.form = c.get("form", r.form)
        r.height_mm = c.get("height_mm")
        r.height_tol_mm = c.get("height_tol_mm", 0.05)
        r.width_mm = c.get("width_mm")
        r.width_tol_mm = c.get("width_tol_mm", 0.05)
        r.strip_length_mm = c.get("strip_length_mm")
        r.pull_force_min_n = c.get("pull_force_min_n")
        r.family = term.contact_family or term.family or ""
        r.citation = term.source
    pp = t.process_params or {}
    r.hex_mm = pp.get("hex_mm", r.hex_mm)
    r.height_mm = pp.get("crimp_height_mm", r.height_mm)
    if wire:
        r.wire_mm2 = wire.conductor_mm2
        od = wire.attrs.get("insulation_od_mm")
        rng = wire.insulation_od_range_mm
        r.insulation_od_mm = od or (sum(rng) / 2 if rng else None)
    return r


def _group_key(t, term: Part | None) -> str:
    return term.mpn if term else f"{t.ttype}:{t.housing_mpn or t.terminal_mpn or '-'}"


def build_groups(prog: ProgramData) -> list[GroupReport]:
    groups: dict[str, GroupReport] = {}
    for h in prog.harnesses:
        for t in h.terminations:
            if t.ttype == "preterminated":
                continue
            term = prog.part(t.terminal_mpn)
            wire = prog.part(h.segment(t.segment).part_mpn)
            key = _group_key(t, term)
            g = groups.get(key)
            if g is None:
                req = _requirement_for(prog, term, wire, t)
                g = GroupReport(
                    key=key,
                    description=(term.description if term else t.ttype),
                    ttype=t.ttype, requirement=req,
                    named_tools=(term.named_tools if term else []),
                    named_tool_citation=(term.source if term else Citation()),
                    terminations_per_set=0.0, harnesses=[],
                )
                groups[key] = g
            g.terminations_per_set += h.qty_per_set
            if h.drawing_number not in g.harnesses:
                g.harnesses.append(h.drawing_number)
    return list(groups.values())


# --------------------------------------------------------------------------- #
def _within(v: float, lo: float | None, hi: float | None) -> bool | None:
    if lo is None and hi is None:
        return None
    if lo is not None and v < lo - 1e-9:
        return False
    if hi is not None and v > hi + 1e-9:
        return False
    return True


# a bare press or frame is only a carrier — it matches via an applicator/die,
# never by itself
_CRIMP_CLASSES = {"hand_crimp", "die_set", "applicator", "hex_die"}
_SOLDER_CLASSES = {"solder_station", "solder_tip"}


def match_tool(req: Requirement, ttype: str, tool: Tool) -> ToolMatch | None:
    """Score one inventory tool against a requirement. None = wrong class."""
    is_solder = ttype in ("solder_cup", "solder_sleeve")
    if is_solder:
        if tool.tool_class not in _SOLDER_CLASSES:
            return None
        return ToolMatch(tool, "exact",
                         f"solder joint: {tool.mpn} ({tool.description}) — tip/iron "
                         "selection per joint size; no crimp geometry applies",
                         closeness=0)
    if tool.tool_class not in _CRIMP_CLASSES:
        return None

    ev: list[str] = []
    # crimp form must match
    if req.form and tool.crimp_form and tool.crimp_form.lower() != req.form.lower():
        return ToolMatch(tool, "no",
                         f"form mismatch: tool forms '{tool.crimp_form}', spec requires "
                         f"'{req.form}' {req.citation.short()}")
    # wire range
    if req.wire_mm2 is not None:
        w = _within(req.wire_mm2, tool.wire_min_mm2, tool.wire_max_mm2)
        if w is False:
            return ToolMatch(tool, "no",
                             f"wire {req.wire_mm2} mm² outside tool range "
                             f"{tool.wire_min_mm2}–{tool.wire_max_mm2} mm²")
        if w:
            ev.append(f"wire {req.wire_mm2} mm² in tool range "
                      f"{tool.wire_min_mm2}–{tool.wire_max_mm2} mm²")
    # hex nest (coax ferrule)
    if req.hex_mm is not None:
        hw = _within(req.hex_mm, tool.width_min_mm, tool.width_max_mm)
        if hw is False:
            return ToolMatch(tool, "no",
                             f"hex {req.hex_mm} mm outside die range "
                             f"{tool.width_min_mm}–{tool.width_max_mm} mm")
        if hw:
            ev.append(f"hex {req.hex_mm} mm within die range")
    # crimp height / width windows
    verdict = "qualify"
    closeness = 9e9
    if req.height_mm is not None:
        hh = _within(req.height_mm, tool.height_min_mm, tool.height_max_mm)
        if hh is False:
            return ToolMatch(tool, "no",
                             f"required height {req.height_mm} mm outside tool "
                             f"achievable {tool.height_min_mm}–{tool.height_max_mm} mm "
                             f"(tool datasheet vs {req.citation.short()})")
        if hh:
            mid = ((tool.height_min_mm or req.height_mm) +
                   (tool.height_max_mm or req.height_mm)) / 2
            closeness = abs(mid - req.height_mm)
            ev.append(f"height {req.height_mm}±{req.height_tol_mm or 0} mm within "
                      f"achievable {tool.height_min_mm}–{tool.height_max_mm} mm")
        else:
            ev.append("tool datasheet lists no height range — measure before use")
    if req.width_mm is not None:
        ww = _within(req.width_mm, tool.width_min_mm, tool.width_max_mm)
        if ww is False:
            return ToolMatch(tool, "no",
                             f"required width {req.width_mm} mm outside tool "
                             f"{tool.width_min_mm}–{tool.width_max_mm} mm")
        if ww:
            ev.append(f"width {req.width_mm} mm within tool range")
    # insulation crimp
    if req.insulation_od_mm is not None and tool.insulation_min_mm is not None:
        iw = _within(req.insulation_od_mm, tool.insulation_min_mm,
                     tool.insulation_max_mm)
        if iw is False:
            return ToolMatch(tool, "no",
                             f"insulation OD {req.insulation_od_mm} mm outside tool "
                             f"{tool.insulation_min_mm}–{tool.insulation_max_mm} mm")
        ev.append("insulation crimp within range")

    # vendor names the family -> exact; otherwise within-tolerance -> qualify
    fams = [f.strip().lower() for f in tool.terminal_families.split(";") if f.strip()]
    if req.family and req.family.lower() in fams:
        verdict = "exact"
        closeness = 0.0
        ev.insert(0, f"vendor lists terminal family '{req.family}' for this tool "
                     f"({tool.source_doc or 'tool datasheet'})")
    return ToolMatch(tool, verdict, "; ".join(ev) or "class/geometry plausible — "
                     "no dimensional data on file", closeness)


def rank_matches(req: Requirement, ttype: str, inv: Inventory) -> list[ToolMatch]:
    matches = []
    for tool in inv.owned():
        m = match_tool(req, ttype, tool)
        if m is not None:
            matches.append(m)
    order = {"exact": 0, "qualify": 1, "no": 2}
    matches.sort(key=lambda m: (order[m.verdict], m.closeness))
    return matches


# --------------------------------------------------------------------------- #
def _named_tool_cost(prog: ProgramData, g: GroupReport, inv: Inventory) -> float | None:
    for mpn in g.named_tools:
        t = inv.get(mpn)
        if t and t.cost is not None:
            return t.cost
        p = prog.part(mpn)
        if p:
            price = p.price_at(1)
            if price is not None:
                return price
    return None


def build_paths(prog: ProgramData, g: GroupReport, inv: Inventory) -> list[PathOption]:
    rate = prog.meta.rates.technician_rate_per_hour * prog.meta.rates.loaded_multiplier
    qual_cost = QUALIFICATION_HOURS * rate
    is_solder = g.ttype in ("solder_cup", "solder_sleeve")
    per_min = SOLDER_JOINT_MIN if is_solder else HAND_CRIMP_MIN
    paths: list[PathOption] = []

    usable = [m for m in g.matches if m.verdict in ("exact", "qualify")]
    for m in usable[:2]:
        if m.verdict == "exact":
            paths.append(PathOption(
                name=f"existing tool {m.tool.mpn} (exact)",
                one_time_cost=0.0, per_termination_min=per_min,
                note=m.evidence))
        else:
            paths.append(PathOption(
                name=f"existing tool {m.tool.mpn} (qualify)",
                one_time_cost=qual_cost, per_termination_min=per_min,
                note=f"qualification {QUALIFICATION_HOURS} h loaded; {m.evidence}"))
    named_cost = _named_tool_cost(prog, g, inv)
    if g.named_tools:
        paths.append(PathOption(
            name=f"buy named tool {g.named_tools[0]}",
            one_time_cost=named_cost if named_cost is not None else 0.0,
            per_termination_min=per_min,
            note=("budgetary price on file" if named_cost is not None else
                  "price unverified — quote needed before decision")))
    # applicator + press path when a press is owned and an applicator is named
    press = next((t for t in inv.owned() if t.tool_class == "press"), None)
    applicator_mpns = [m for m in g.named_tools
                       if (ap := prog.part(m)) and ap.attrs.get("tool_class") == "applicator"]
    if press and applicator_mpns and not is_solder:
        ap = prog.part(applicator_mpns[0])
        paths.append(PathOption(
            name=f"applicator {ap.mpn} on existing press {press.mpn}",
            one_time_cost=ap.price_at(1) or 0.0,
            per_termination_min=PRESS_CRIMP_MIN,
            note="reel-fed; cycle time planning estimate"))
    return paths


def choose_path(prog: ProgramData, g: GroupReport) -> PathOption | None:
    """Cheapest compliant path over the horizon at the max planned volume."""
    if not g.paths:
        return None
    vols = prog.meta.planned_volumes()
    weekly = (max(vols) if vols else 0) * g.terminations_per_set
    horizon = prog.meta.horizon_weeks
    rate = prog.meta.rates.technician_rate_per_hour * prog.meta.rates.loaded_multiplier

    def total(p: PathOption) -> float:
        labor = weekly * horizon * p.per_termination_min / 60.0 * rate
        return p.one_time_cost + labor

    return min(g.paths, key=total)


# --------------------------------------------------------------------------- #
def match_program(prog: ProgramData, inv: Inventory,
                  today: date | None = None) -> list[GroupReport]:
    today = today or date.today()
    vols = prog.meta.planned_volumes()
    max_weekly_sets = max(vols) if vols else 0
    groups = build_groups(prog)
    for g in groups:
        g.matches = rank_matches(g.requirement, g.ttype, inv)
        g.paths = build_paths(prog, g, inv)
        g.chosen_path = choose_path(prog, g)
        g.cycles_per_week_at_max = g.terminations_per_set * max_weekly_sets
        if g.chosen_path and "existing tool" in g.chosen_path.name:
            tool_mpn = g.chosen_path.name.split()[2]
            tool = inv.get(tool_mpn)
            if tool:
                if tool.restrictions:
                    g.restrictions.append(
                        f"{tool.mpn}: {tool.restrictions} — manufacturer guidance, "
                        "to be waived or followed at owner's decision; risk: joint "
                        "formed outside the vendor's stated use case, mitigated by "
                        "the qualification protocol and first-piece checks")
            g.qualification_needed = "qualify" in g.chosen_path.name
        if g.chosen_path and g.named_tools:
            named = {m.lower() for m in g.named_tools}
            chosen_tool = g.chosen_path.name.split()[2] if \
                g.chosen_path.name.startswith(("existing", "buy")) else ""
            if chosen_tool and chosen_tool.lower() not in named and \
                    "buy named" not in g.chosen_path.name:
                g.qualification_needed = True
    return groups


def findings_from_report(prog: ProgramData, groups: list[GroupReport],
                         today: date | None = None) -> list[Finding]:
    today = today or date.today()
    out: list[Finding] = []
    i = 0

    def fid():
        nonlocal i
        i += 1
        return f"T{i:03d}"

    for g in groups:
        if not g.paths:
            out.append(Finding(
                id=fid(), severity="blocker", check="tooling_path",
                ref=g.key,
                message=(f"No compliant tooling path found for {g.key} "
                         f"({g.description}) — no inventory match and no named tool "
                         "on file"),
                citations=[g.named_tool_citation],
                proposed_default="Pull the application spec tooling table; quote the "
                                 "named hand tool."))
            continue
        for r in g.restrictions:
            out.append(Finding(
                id=fid(), severity="warning", check="tooling_restriction",
                ref=g.key, message=r, citations=[g.named_tool_citation],
                proposed_default="Owner decision: accept with documented deviation at "
                                 "prototype volume (lesson 6)."))
        if g.qualification_needed:
            out.append(Finding(
                id=fid(), severity="info", check="tooling_qualification",
                ref=g.key,
                message=(f"{g.key}: chosen path '{g.chosen_path.name}' uses a non-named "
                         "tool — run the qualification protocol before production"),
                citations=[g.named_tool_citation],
                proposed_default="Schedule qualification during first-article build."))
    # inventory health: calibration and cycle life (uses chosen tools only)
    return out


def inventory_health(groups: list[GroupReport], inv: Inventory,
                     today: date | None = None, weeks_ahead: int = 26) -> list[str]:
    """Human-readable flags for tools nearing recalibration or end of life."""
    today = today or date.today()
    flags = []
    use: dict[str, float] = {}
    for g in groups:
        if g.chosen_path and "existing tool" in g.chosen_path.name:
            mpn = g.chosen_path.name.split()[2]
            use[mpn] = use.get(mpn, 0) + g.cycles_per_week_at_max
    for mpn, weekly in use.items():
        t = inv.get(mpn)
        if not t:
            continue
        if t.cycle_life:
            projected = t.cycle_count + weekly * weeks_ahead
            if projected > t.cycle_life:
                flags.append(
                    f"{t.mpn}: projected {projected:,.0f} cycles in {weeks_ahead} weeks "
                    f"exceeds cycle life {t.cycle_life:,} — plan replacement/refurb")
        if t.certification_date and t.calibration_interval_months:
            try:
                cert = date.fromisoformat(t.certification_date)
                due = cert + timedelta(days=30.4 * t.calibration_interval_months)
                if due < today + timedelta(weeks=8):
                    flags.append(f"{t.mpn}: calibration due {due.isoformat()} "
                                 f"(interval {t.calibration_interval_months:g} months)")
            except ValueError:
                flags.append(f"{t.mpn}: unparseable certification date "
                             f"'{t.certification_date}'")
        elif t.certification_status != "certified":
            flags.append(f"{t.mpn}: not certified — certify before first article")
    return flags


# --------------------------------------------------------------------------- #
def qualification_protocol(prog: ProgramData, g: GroupReport, tool: Tool) -> str:
    """Tool qualification sheet for using a non-named tool (Part 6)."""
    r = g.requirement
    round_crimp = r.form.lower() in ("closed", "round", "hex", "4-indent")
    lines = [
        f"# Tool qualification sheet — {tool.mpn} for {g.key}",
        "",
        f"- Terminal / joint: {g.key} ({g.description})",
        f"- Governing spec: {r.citation.short()}",
        f"- Tool: {tool.mpn} ({tool.manufacturer}) — {tool.description}",
        f"- Tool restrictions on file: {tool.restrictions or 'none'}",
        f"- Harnesses affected: {', '.join(g.harnesses)}",
        "",
        "## Acceptance targets (from the application spec)",
        f"- Crimp form: {r.form or 'n/a'}",
        f"- Crimp height: {r.height_mm} ± {r.height_tol_mm} mm" if r.height_mm else
        "- Crimp height: n/a",
        f"- Crimp width: {r.width_mm} ± {r.width_tol_mm} mm" if r.width_mm else
        "- Crimp width: n/a",
        f"- Pull force: ≥ {r.pull_force_min_n} N" if r.pull_force_min_n else
        "- Pull force: per spec table (fill in)",
        f"- Strip length: {r.strip_length_mm} mm" if r.strip_length_mm else "",
        "",
        "## Protocol",
        "1. Dimensional check on 10 samples: crimp height and width"
        + (", measured in two orientations (round crimp)" if round_crimp else "")
        + ", recorded individually.",
        "2. 3 cross-sections: conductor compression, bellmouth, cut-off per the "
        "spec's figures.",
        "3. Pull test to the spec minimum on 5 samples.",
        "4. Visual inspection per the spec's inspection figures.",
    ]
    step = 5
    if any("shield" in h.lower() or "ethernet" in h.lower() for h in [g.description]) \
            or r.family.lower() in ("matenet", "coax"):
        lines.append(f"{step}. Shielded/impedance-controlled joint: link test or VNA "
                     "sweep per the customer's test requirement.")
        step += 1
    lines += [
        f"{step}. Sealed system: seal-fit check on the finished termination (where "
        "applicable).",
        f"{step + 1}. Record results on this sheet; attach to the program file and "
        "update the tool inventory (certification date, cycle count).",
        "",
        "> Note: if the application spec restricts tooling to named tools, a customer "
        "deviation may be needed — raise it as an open item before series use.",
        "",
        "| Sample | Height (mm) | Width (mm) | Pull (N) | Visual | Pass |",
        "|---|---|---|---|---|---|",
    ]
    lines += [f"| {n} |  |  |  |  |  |" for n in range(1, 11)]
    lines += ["", f"Qualified by: ____________  Date: ________  "
                  f"Tool cycle count at qualification: ________"]
    return "\n".join(x for x in lines if x is not None)
