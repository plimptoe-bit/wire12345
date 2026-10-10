"""Termination map: every joint, its process parameters and its sources."""
from __future__ import annotations

import csv
from pathlib import Path

from ..model import ProgramData


def _params_text(prog: ProgramData, t) -> str:
    term = prog.part(t.terminal_mpn)
    bits = []
    if term and term.crimp:
        c = term.crimp
        if c.get("height_mm") is not None:
            bits.append(f"CH {c['height_mm']}±{c.get('height_tol_mm', 0.05)} mm")
        if c.get("width_mm") is not None:
            bits.append(f"CW {c['width_mm']}±{c.get('width_tol_mm', 0.05)} mm")
        if c.get("strip_length_mm") is not None:
            bits.append(f"strip {c['strip_length_mm']} mm")
        if c.get("pull_force_min_n") is not None:
            bits.append(f"pull ≥{c['pull_force_min_n']} N")
    for k, v in (t.process_params or {}).items():
        bits.append(f"{k}={v}")
    return "; ".join(bits) or "—"


def termination_rows(prog: ProgramData) -> list[dict]:
    rows = []
    for h in prog.harnesses:
        for t in h.terminations:
            seg = h.segment(t.segment)
            wire = prog.part(seg.part_mpn)
            term = prog.part(t.terminal_mpn)
            src = term.source if term else t.citation
            rows.append({
                "harness": h.drawing_number,
                "termination": t.id,
                "node": t.node,
                "cavity": t.cavity or "—",
                "segment": f"{seg.id} {seg.circuit}".strip(),
                "wire": seg.part_mpn,
                "conductor_mm2": wire.conductor_mm2 if wire else "",
                "type": t.ttype,
                "terminal": t.terminal_mpn or "—",
                "housing": t.housing_mpn or "—",
                "sealed": "yes" if t.sealed else "no",
                "shielded": "yes" if t.shielded else "no",
                "accessories": ", ".join(t.accessories) or "—",
                "process_params": _params_text(prog, t),
                "source": src.short(),
            })
    return rows


def write_csv(prog: ProgramData, path: Path):
    rows = termination_rows(prog)
    if not rows:
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def markdown(prog: ProgramData) -> str:
    rows = termination_rows(prog)
    out = [f"# Termination map — {prog.meta.name}", ""]
    hdr = ["Harness", "Term", "Node/cavity", "Segment", "Wire", "Type", "Terminal",
           "Accessories", "Process parameters", "Source"]
    out.append("| " + " | ".join(hdr) + " |")
    out.append("|" + "---|" * len(hdr))
    for r in rows:
        out.append("| {harness} | {termination} | {node}/{cavity} | {segment} | "
                   "{wire} | {type} | {terminal} | {accessories} | "
                   "{process_params} | {source} |".format(**r))
    return "\n".join(out) + "\n"
