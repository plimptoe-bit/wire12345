"""Formboard (assembly board) drawings (Part 8A).

Lays each harness flat at true length, adds the manufacturing allowances the
customer drawing does not show, places pegs and nests, and emits:
  - SVG + PDF at true scale (1:1) with scale bar and registration marks
  - peg coordinate table (CSV, from the board datum)
  - cut list derived from the same geometry
  - plain-text build sequence

Conventions applied (stated on the drawing; deviations are open items):
  - dimensions are taken as point-to-point between node reference planes,
    per the segment's recorded length_convention
  - unspecified branch angles default to 90° off the trunk, alternating sides
  - folds are pegged U-turns, never placed on a tape or label position
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

from ..model import Harness, ProgramData, Segment

BOARD_W, BOARD_H = 2400.0, 1200.0   # standard board, mm
MARGIN = 100.0                      # usable margin from board edge
ROW_PITCH = 220.0                   # serpentine row spacing
SUPPORT_PEG_EVERY = 300.0
FOLD_KEEPOUT = 50.0                 # a fold may not land within this of tape/label
DEFAULT_STRIP_MM = 5.0              # assumption when the spec gives none
SHIELD_FOLDBACK_MM = 25.0           # assumption A-FB-SHIELD
MIN_FOLD_RADIUS = 50.0


@dataclass
class Peg:
    id: str
    x: float
    y: float
    kind: str        # nest|breakout|fold|support
    note: str = ""


@dataclass
class PlacedSegment:
    segment: Segment
    points: list[tuple[float, float]]
    cut_length_mm: float
    allowance_a: float
    allowance_b: float
    allowance_notes: str


@dataclass
class BoardLayout:
    harness: Harness
    board_w: float
    board_h: float
    node_pos: dict[str, tuple[float, float]]
    segments: list[PlacedSegment]
    pegs: list[Peg]
    folds: list[tuple[float, float]]
    notes: list[str] = field(default_factory=list)
    open_items: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# allowances: cut length = drawing length + end allowances


def _end_allowance(prog: ProgramData, h: Harness, seg: Segment, end: str
                   ) -> tuple[float, str]:
    node_id = seg.from_node if end == "A" else seg.to_node
    terms = [t for t in h.terminations
             if t.segment == seg.id and t.end == end] or \
            [t for t in h.terminations
             if t.segment == seg.id and t.node == node_id]
    total, notes = 0.0, []
    for t in terms:
        if t.ttype == "preterminated":
            return 0.0, "pre-terminated end — no allowance"
        term = prog.part(t.terminal_mpn)
        strip = (term.crimp.get("strip_length_mm") if term and term.crimp
                 else None)
        if strip is None:
            strip = DEFAULT_STRIP_MM
            notes.append(f"strip {strip:g} (assumed)")
        else:
            notes.append(f"strip {strip:g} per {term.source.short()}")
        total += strip
        hous = prog.part(t.housing_mpn)
        ins = hous.attrs.get("insertion_depth_mm", 0.0) if hous else 0.0
        if ins:
            total += ins
            notes.append(f"insertion {ins:g}")
        if t.shielded:
            total += SHIELD_FOLDBACK_MM
            notes.append(f"shield fold-back {SHIELD_FOLDBACK_MM:g} (assumed)")
    return total, "; ".join(notes) or "no termination at this end"


# --------------------------------------------------------------------------- #
# topology: trunk = longest leaf-to-leaf path, branches hang off it


def _adjacency(h: Harness) -> dict[str, list[tuple[str, Segment]]]:
    adj: dict[str, list[tuple[str, Segment]]] = {n.id: [] for n in h.nodes}
    for s in h.segments:
        adj[s.from_node].append((s.to_node, s))
        adj[s.to_node].append((s.from_node, s))
    return adj


def _components(h: Harness) -> list[list[str]]:
    adj = _adjacency(h)
    seen: set[str] = set()
    comps = []
    for n in h.nodes:
        if n.id in seen:
            continue
        comp, stack = [], [n.id]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(cur)
            stack += [nxt for nxt, _ in adj[cur] if nxt not in seen]
        comps.append(comp)
    return comps


def _longest_path(h: Harness, within: list[str]) -> list[str]:
    adj = _adjacency(h)
    allowed = set(within)

    def far(start: str) -> tuple[str, float, list[str]]:
        best = (start, 0.0, [start])
        stack = [(start, 0.0, [start])]
        while stack:
            node, dist, path = stack.pop()
            if dist > best[1]:
                best = (node, dist, path)
            for nxt, seg in adj[node]:
                if nxt in allowed and nxt not in path:
                    stack.append((nxt, dist + seg.length_mm, path + [nxt]))
        return best

    if not within:
        return []
    a, _, _ = far(within[0])
    _, _, path = far(a)
    return path


def _seg_between(h: Harness, a: str, b: str) -> Segment:
    for s in h.segments:
        if {s.from_node, s.to_node} == {a, b}:
            return s
    raise KeyError((a, b))


# --------------------------------------------------------------------------- #
def _keepout_positions(h: Harness, trunk_segs: list[Segment]) -> list[float]:
    """Cumulative trunk positions (mm) where a fold must not land."""
    pos, cum = [], 0.0
    seg_start = {}
    for s in trunk_segs:
        seg_start[s.id] = cum
        cum += s.length_mm
    for tp in h.tapes:
        if tp.get("segment") in seg_start:
            pos += [seg_start[tp["segment"]] + float(tp.get("from_mm", 0)),
                    seg_start[tp["segment"]] + float(tp.get("to_mm", 0))]
    for lb in h.labels:
        if lb.get("segment") in seg_start:
            pos.append(seg_start[lb["segment"]] + float(lb.get("offset_mm", 0)))
    return pos


def _fold_ok(at: float, keepouts: list[float]) -> bool:
    return all(abs(at - k) > FOLD_KEEPOUT for k in keepouts)


def layout_harness(prog: ProgramData, h: Harness,
                   board_w: float = BOARD_W, board_h: float = BOARD_H
                   ) -> BoardLayout:
    notes, open_items = [], []
    node_pos: dict[str, tuple[float, float]] = {}
    placed: list[PlacedSegment] = []
    folds: list[tuple[float, float]] = []
    placed_seg_ids: set[str] = set()
    baseline = MARGIN + 60.0

    for comp in _components(h):
        trunk = _longest_path(h, comp)
        trunk_segs = [_seg_between(h, a, b) for a, b in zip(trunk, trunk[1:])]
        keepouts = _keepout_positions(h, trunk_segs)

        # --- serpentine trunk ---------------------------------------------- #
        x, y, direction = MARGIN, baseline, 1
        if trunk:
            node_pos[trunk[0]] = (x, y)
        cum = 0.0
        for (a, b), seg in zip(zip(trunk, trunk[1:]), trunk_segs):
            pts = [node_pos[a]]
            remaining = seg.length_mm
            while True:
                limit = (board_w - MARGIN - x) if direction > 0 else (x - MARGIN)
                if remaining <= limit:
                    x += direction * remaining
                    cum += remaining
                    pts.append((x, y))
                    break
                # need a fold: run to the limit, backing off tape/label keepouts
                run = limit
                while run > 0 and not _fold_ok(cum + run, keepouts):
                    run -= 25.0
                if run <= 0:
                    run = max(limit, 0.0)  # fold right here (possibly zero travel)
                    if not _fold_ok(cum + run, keepouts):
                        open_items.append(
                            f"fold near trunk position {cum + run:.0f} mm conflicts "
                            "with a tape/label keep-out — confirm fold placement")
                x += direction * run
                cum += run
                remaining -= run
                pts.append((x, y))
                # the U-turn itself consumes half a circumference
                arc = math.pi * MIN_FOLD_RADIUS
                take = min(arc, remaining)
                remaining -= take
                cum += take
                folds.append((x, y + ROW_PITCH / 2))
                y += ROW_PITCH
                direction *= -1
                pts.append((x, y))
                if y > board_h - MARGIN:
                    notes.append("harness exceeds the board — split across two "
                                 "overlays at the match line (registered)")
                    open_items.append(
                        "harness longer than one board even with folds — "
                        "two-overlay build to be confirmed")
                    board_h = y + MARGIN  # extend virtual board; noted above
            node_pos[b] = pts[-1]
            placed.append(_placed(prog, h, seg, pts, start_node=a))
            placed_seg_ids.add(seg.id)

        # --- branches off the trunk ---------------------------------------- #
        side_at: dict[str, int] = {}
        adj = _adjacency(h)

        def place_branch(parent: str, depth: int):
            for nxt, seg in adj[parent]:
                if nxt in node_pos or seg.id in placed_seg_ids:
                    continue
                px, py = node_pos[parent]
                side_at[parent] = -side_at.get(parent, -1)
                side = side_at[parent]
                if seg.branch_angle_deg is not None:
                    ang = math.radians(seg.branch_angle_deg)
                    notes.append(f"branch {seg.id}: angle "
                                 f"{seg.branch_angle_deg:g}° from drawing")
                else:
                    ang = math.radians(90.0 if depth == 0 else 45.0)
                if depth == 0:
                    dx, dy = 0.0, seg.length_mm * side
                else:
                    dx = math.cos(ang) * seg.length_mm
                    dy = math.sin(ang) * seg.length_mm * side
                nx_, ny_ = px + dx, py + dy
                nx_ = min(max(nx_, MARGIN), board_w - MARGIN)
                node_pos[nxt] = (nx_, ny_)
                placed.append(_placed(prog, h, seg, [(px, py), (nx_, ny_)],
                                      start_node=parent))
                placed_seg_ids.add(seg.id)
                place_branch(nxt, depth + 1)

        for nid in list(trunk):
            place_branch(nid, 0)
        # duplicate segments between already-placed nodes (e.g. a twin wire):
        for seg in h.segments:
            if seg.id not in placed_seg_ids and seg.from_node in node_pos \
                    and seg.to_node in node_pos:
                placed.append(_placed(prog, h, seg,
                                      [node_pos[seg.from_node],
                                       node_pos[seg.to_node]],
                                      start_node=seg.from_node))
                placed_seg_ids.add(seg.id)
        ys_comp = [node_pos[nid][1] for nid in comp if nid in node_pos]
        if ys_comp:
            baseline = max(max(ys_comp) + ROW_PITCH, baseline)
        if len(_components(h)) > 1:
            pass  # components stack top-to-bottom; note added once below
    if len(_components(h)) > 1:
        notes.append(f"{len(_components(h))} separate sub-assemblies laid out "
                     "top-to-bottom on one board")

    # extend board for branches below/above
    ys = [p[1] for p in node_pos.values()]
    if ys and (max(ys) > board_h - MARGIN or min(ys) < MARGIN):
        shift = max(0.0, MARGIN - min(ys))
        if shift:
            node_pos = {k: (vx, vy + shift) for k, (vx, vy) in node_pos.items()}
            for ps in placed:
                ps.points = [(px, py + shift) for px, py in ps.points]
            folds = [(fx, fy + shift) for fx, fy in folds]
            ys = [p[1] for p in node_pos.values()]
        board_h = max(board_h, max(ys) + MARGIN)

    pegs = _pegs(prog, h, node_pos, placed, folds)
    lay = BoardLayout(h, board_w, board_h, node_pos, placed, pegs, folds,
                      notes, open_items)
    if trunk:
        conv = h.length_convention or \
            "point-to-point between node reference planes (default — confirm)"
        lay.notes.insert(0, f"dimension convention: {conv}")
        if not h.length_convention:
            lay.open_items.append(
                "customer drawing dimension origin not recorded — default "
                "point-to-point convention applied; confirm before first board")
    return lay


def _placed(prog: ProgramData, h: Harness, seg: Segment,
            pts: list[tuple[float, float]], start_node: str) -> PlacedSegment:
    # tape/label offsets are measured from the segment's A end (from_node), so
    # keep the point list oriented A -> B regardless of layout walk direction
    if seg.from_node != start_node:
        pts = list(reversed(pts))
    aa, na = _end_allowance(prog, h, seg, "A")
    ab, nb = _end_allowance(prog, h, seg, "B")
    return PlacedSegment(
        segment=seg, points=pts,
        cut_length_mm=round(seg.length_mm + aa + ab, 1),
        allowance_a=aa, allowance_b=ab,
        allowance_notes=f"A: {na} | B: {nb}")


def _pegs(prog, h, node_pos, placed, folds) -> list[Peg]:
    pegs, i = [], 0

    def add(x, y, kind, note=""):
        nonlocal i
        i += 1
        pegs.append(Peg(f"P{i:02d}", round(x, 1), round(y, 1), kind, note))

    for n in h.nodes:
        x, y = node_pos[n.id]
        if n.kind == "connector":
            add(x, y, "nest", f"{n.housing_mpn or ''} nest, keyed, "
                f"{n.mate_orientation or 'mated orientation'}")
        elif n.kind in ("breakout", "splice"):
            add(x, y, "breakout", n.id)
    for fx, fy in folds:
        add(fx, fy, "fold", "pegged U-turn, r=%.0f mm" % MIN_FOLD_RADIUS)
    for ps in placed:
        for (x1, y1), (x2, y2) in zip(ps.points, ps.points[1:]):
            run = math.hypot(x2 - x1, y2 - y1)
            n_pegs = int(run // SUPPORT_PEG_EVERY)
            for k in range(1, n_pegs + 1):
                t = k * SUPPORT_PEG_EVERY / run
                add(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, "support",
                    f"bundle support on {ps.segment.id}")
    return pegs


# --------------------------------------------------------------------------- #
# SVG rendering


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_svg(prog: ProgramData, lay: BoardLayout) -> str:
    h = lay.harness
    W, H = lay.board_w, lay.board_h
    e = []
    e.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" '
             f'height="{H}mm" viewBox="0 0 {W} {H}" '
             'font-family="Helvetica, Arial, sans-serif">')
    e.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="white" '
             'stroke="black" stroke-width="1"/>')
    # 100 mm grid
    for gx in range(0, int(W) + 1, 100):
        e.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}" stroke="#e5e5e5" '
                 'stroke-width="0.3"/>')
    for gy in range(0, int(H) + 1, 100):
        e.append(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="#e5e5e5" '
                 'stroke-width="0.3"/>')
    # registration marks
    for rx, ry in [(20, 20), (W - 20, 20), (20, H - 20), (W - 20, H - 20)]:
        e.append(f'<path d="M {rx - 8} {ry} H {rx + 8} M {rx} {ry - 8} V {ry + 8}" '
                 'stroke="black" stroke-width="0.6"/>')
        e.append(f'<circle cx="{rx}" cy="{ry}" r="5" fill="none" stroke="black" '
                 'stroke-width="0.6"/>')
    # scale bar
    e.append(f'<g transform="translate(30,{H - 42})">'
             '<rect x="0" y="0" width="100" height="6" fill="black"/>'
             '<rect x="100" y="0" width="100" height="6" fill="white" '
             'stroke="black" stroke-width="0.5"/>'
             '<text x="0" y="16" font-size="10">0</text>'
             '<text x="95" y="16" font-size="10">100</text>'
             '<text x="185" y="16" font-size="10">200 mm — SCALE 1:1</text></g>')

    # tape zones (under segments)
    seg_pts = {ps.segment.id: ps for ps in lay.segments}
    for tp in h.tapes:
        ps = seg_pts.get(tp.get("segment"))
        if not ps:
            continue
        band = _subpath(ps.points, float(tp.get("from_mm", 0)),
                        float(tp.get("to_mm", ps.segment.length_mm)))
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in band)
        e.append(f'<path d="{d}" stroke="#1f77b4" stroke-width="8" fill="none" '
                 'stroke-opacity="0.35"/>')
        mx, my = band[len(band) // 2]
        e.append(f'<text x="{mx:.1f}" y="{my - 8:.1f}" font-size="9" '
                 f'fill="#1f77b4">{_esc(tp.get("kind", "tape"))} '
                 f'{_esc(tp.get("mpn", ""))} '
                 f'{tp.get("from_mm", 0):g}–{tp.get("to_mm", 0):g} mm'
                 f'{" — " + _esc(tp["note"]) if tp.get("note") else ""}</text>')

    # segments
    for ps in lay.segments:
        part = prog.part(ps.segment.part_mpn)
        od = (part.attrs.get("jacket_od_mm") or part.attrs.get("insulation_od_mm")
              or 2.0) if part else 2.0
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in ps.points)
        e.append(f'<path d="{d}" stroke="#333" stroke-width="{max(od, 1.2):.1f}" '
                 'fill="none" stroke-linejoin="round"/>')
        mx, my = ps.points[len(ps.points) // 2]
        label = f"{ps.segment.id} {ps.segment.circuit} {ps.segment.length_mm:g}mm"
        e.append(f'<text x="{mx:.1f}" y="{my + 14:.1f}" font-size="10">'
                 f'{_esc(label.strip())}</text>')

    # folds
    for fx, fy in lay.folds:
        e.append(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{MIN_FOLD_RADIUS}" '
                 'fill="none" stroke="#999" stroke-dasharray="4 3" '
                 'stroke-width="0.8"/>')
        e.append(f'<text x="{fx + 4:.1f}" y="{fy:.1f}" font-size="9" fill="#555">'
                 f'FOLD x={fx:.0f} y={fy:.0f}</text>')

    # pegs
    for p in lay.pegs:
        color = {"nest": "#d62728", "breakout": "#2ca02c", "fold": "#999",
                 "support": "#aaa"}[p.kind]
        r = 6 if p.kind == "nest" else 3.5
        e.append(f'<circle cx="{p.x}" cy="{p.y}" r="{r}" fill="none" '
                 f'stroke="{color}" stroke-width="1.2"/>')
        if p.kind in ("nest", "breakout"):
            e.append(f'<text x="{p.x + 8}" y="{p.y - 8}" font-size="9" '
                     f'fill="{color}">{p.id}</text>')

    # connector call-outs with cavity maps + sequence numbers
    seq = 1
    for n in h.nodes:
        if n.kind != "connector":
            continue
        x, y = lay.node_pos[n.id]
        terms = h.terminations_at(n.id)
        lines = [f"{n.id}  {n.housing_mpn or ''}", f"{n.label}".strip()]
        for t in sorted(terms, key=lambda t: str(t.cavity)):
            seg = h.segment(t.segment)
            lines.append(f"cav {t.cavity or '?'}: {seg.color or seg.circuit or seg.id}")
        locks = sorted({a for t in terms for a in t.accessories})
        if locks:
            lines.append("fit+close: " + ", ".join(locks))
        lines.append(f"orientation: {n.mate_orientation or 'per nest key'}")
        bx, by = x - 10, y + 22
        bh = 11 * (len(lines) + 1)
        e.append(f'<rect x="{bx}" y="{by}" width="170" height="{bh}" fill="#fffbe8" '
                 'stroke="#c90" stroke-width="0.6"/>')
        for i, ln in enumerate(lines):
            e.append(f'<text x="{bx + 4}" y="{by + 12 + i * 11}" font-size="9">'
                     f'{_esc(ln)}</text>')
        e.append(f'<circle cx="{x - 16}" cy="{y - 14}" r="8" fill="white" '
                 'stroke="black" stroke-width="0.8"/>')
        e.append(f'<text x="{x - 16}" y="{y - 10.5}" font-size="10" '
                 f'text-anchor="middle" font-weight="bold">{seq}</text>')
        seq += 1

    # wire labels
    for lb in h.labels:
        ps = seg_pts.get(lb.get("segment"))
        if not ps:
            continue
        lx, ly = _point_at(ps.points, float(lb.get("offset_mm", 0)))
        e.append(f'<rect x="{lx - 2}" y="{ly - 18}" width="60" height="12" '
                 'fill="white" stroke="#555" stroke-width="0.5"/>')
        e.append(f'<text x="{lx}" y="{ly - 9}" font-size="8">'
                 f'LBL {_esc(lb.get("text", ""))} @{lb.get("offset_mm", 0):g}mm</text>')

    # inspection box
    insp = _inspection_points(prog, h)
    ix, iy = lay.board_w - 420, 30
    e.append(f'<rect x="{ix}" y="{iy}" width="390" height="{14 * (len(insp) + 2)}" '
             'fill="#f4fff4" stroke="#2ca02c" stroke-width="0.8"/>')
    e.append(f'<text x="{ix + 6}" y="{iy + 14}" font-size="11" font-weight="bold">'
             f'INSPECTION — {_esc(prog.meta.workmanship_standard)} '
             '(record on traveller)</text>')
    for i, item in enumerate(insp):
        e.append(f'<text x="{ix + 6}" y="{iy + 28 + i * 14}" font-size="9">'
                 f'{i + 1}. {_esc(item)}</text>')

    # revision block
    rb_y = lay.board_h - 120
    rows = [
        f"customer drawing: {h.drawing_number} rev {h.revision}",
        f"board overlay rev: {prog.meta.revision or 'A'}-{h.revision or '0'}  "
        f"date: {prog.meta.date}",
        f"program: {prog.meta.name}",
        "change summary: initial generation from data model",
    ]
    e.append(f'<rect x="{lay.board_w - 420}" y="{rb_y}" width="390" height="76" '
             'fill="white" stroke="black" stroke-width="0.8"/>')
    for i, rtxt in enumerate(rows):
        e.append(f'<text x="{lay.board_w - 412}" y="{rb_y + 16 + i * 16}" '
                 f'font-size="10">{_esc(rtxt)}</text>')

    # notes
    for i, ntxt in enumerate(lay.notes):
        e.append(f'<text x="30" y="{28 + i * 12}" font-size="9" fill="#555">'
                 f'NOTE: {_esc(ntxt)}</text>')
    e.append("</svg>")
    return "\n".join(e)


def _subpath(points, from_mm, to_mm):
    out, cum = [], 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        run = math.hypot(x2 - x1, y2 - y1)
        a, b = max(from_mm, cum), min(to_mm, cum + run)
        if b > a and run > 0:
            t1, t2 = (a - cum) / run, (b - cum) / run
            out.append((x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1))
            out.append((x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2))
        cum += run
    return out or points[:2]


def _point_at(points, at_mm):
    cum = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        run = math.hypot(x2 - x1, y2 - y1)
        if cum + run >= at_mm and run > 0:
            t = (at_mm - cum) / run
            return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        cum += run
    return points[-1]


def _inspection_points(prog: ProgramData, h: Harness) -> list[str]:
    items = ["tug test every crimped termination (spec pull values on the "
             "termination map)",
             "secondary lock / wedgelock closed — visual, every connector",
             "label text + position legible against this overlay",
             "bend radius at folds and breakouts ≥ cable datasheet minimum",
             "final length check against this overlay (tolerances per drawing)"]
    if any(t.shielded for t in h.terminations):
        items.append("shield termination: 360° contact, fold-back per spec figure")
    if any(t.ttype.startswith("solder") for t in h.terminations):
        items.append(f"solder joints per {prog.meta.workmanship_standard} "
                     "(wetting, no stress relief damage)")
    if h.test_requirements:
        items.append(f"program test: {h.test_requirements}")
    return items


# --------------------------------------------------------------------------- #
# outputs


def write_all(prog: ProgramData, out_dir: Path, pdf: bool = True,
              draft_note: str | None = None) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for h in prog.harnesses:
        lay = layout_harness(prog, h)
        if draft_note:
            lay.notes.insert(0, draft_note)
        base = out_dir / h.drawing_number.replace("/", "_")
        svg = render_svg(prog, lay)
        (base.with_suffix(".svg")).write_text(svg)
        written.append(str(base.with_suffix(".svg")))
        if pdf:
            try:
                import cairosvg
                cairosvg.svg2pdf(bytestring=svg.encode(),
                                 write_to=str(base.with_suffix(".pdf")))
                written.append(str(base.with_suffix(".pdf")))
            except Exception as ex:  # pragma: no cover
                (base.with_suffix(".pdf.SKIPPED.txt")).write_text(
                    f"PDF conversion unavailable: {ex}\n")
        # peg table
        with (base.parent / f"{base.name}_pegs.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["peg", "x_mm_from_datum", "y_mm_from_datum", "kind", "note"])
            for p in lay.pegs:
                w.writerow([p.id, p.x, p.y, p.kind, p.note])
        written.append(str(base.parent / f"{base.name}_pegs.csv"))
        # cut list from the same geometry
        with (base.parent / f"{base.name}_cutlist.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["segment", "circuit", "material_mpn", "drawing_length_mm",
                        "tol_mm", "allowance_A_mm", "allowance_B_mm",
                        "cut_length_mm", "source", "allowance_basis"])
            for ps in lay.segments:
                s = ps.segment
                w.writerow([s.id, s.circuit, s.part_mpn, s.length_mm, s.tol_mm,
                            ps.allowance_a, ps.allowance_b, ps.cut_length_mm,
                            s.source, ps.allowance_notes])
        written.append(str(base.parent / f"{base.name}_cutlist.csv"))
        # build sequence
        (base.parent / f"{base.name}_sequence.txt").write_text(
            build_sequence(prog, h, lay))
        written.append(str(base.parent / f"{base.name}_sequence.txt"))
        # open items from layout
        if lay.open_items:
            (base.parent / f"{base.name}_board_open_items.md").write_text(
                "# Formboard open items — do not release the overlay until "
                "answered\n\n" +
                "\n".join(f"- {o}" for o in lay.open_items) +
                "\n\nValidate the first board by building one harness and "
                "measuring against the customer drawing before release "
                "(checkpoint VALIDATE_FIRST_BOARD).\n")
            written.append(str(base.parent / f"{base.name}_board_open_items.md"))
    return written


def build_sequence(prog: ProgramData, h: Harness, lay: BoardLayout) -> str:
    lines = [f"BUILD SEQUENCE — {h.drawing_number} rev {h.revision} "
             f"({h.name or h.family})", ""]
    step = 1
    conn = [n for n in h.nodes if n.kind == "connector"]
    for n in conn:
        lines.append(f"{step:2d}. Load {n.housing_mpn or n.id} into nest at "
                     f"{tuple(round(v) for v in lay.node_pos[n.id])} "
                     f"({n.mate_orientation or 'keyed orientation'})")
        step += 1
    for ps in sorted(lay.segments, key=lambda p: -p.segment.length_mm):
        s = ps.segment
        lines.append(f"{step:2d}. Route segment {s.id} ({s.circuit or s.part_mpn}, "
                     f"cut {ps.cut_length_mm:g} mm) along its path; terminate per "
                     "termination map")
        step += 1
    for t in h.terminations:
        if t.accessories:
            lines.append(f"{step:2d}. Fit {', '.join(t.accessories)} at {t.node} "
                         f"({t.id}); close locks")
            step += 1
    for tp in h.tapes:
        lines.append(f"{step:2d}. Tape {tp.get('kind', '')} on {tp.get('segment')} "
                     f"{tp.get('from_mm', 0):g}–{tp.get('to_mm', 0):g} mm"
                     f"{' — ' + tp['note'] if tp.get('note') else ''}")
        step += 1
    for lb in h.labels:
        lines.append(f"{step:2d}. Apply label '{lb.get('text', '')}' on "
                     f"{lb.get('segment')} at {lb.get('offset_mm', 0):g} mm")
        step += 1
    lines.append(f"{step:2d}. Inspect per overlay inspection box; record on "
                 "traveller; final length check against overlay")
    return "\n".join(lines) + "\n"
