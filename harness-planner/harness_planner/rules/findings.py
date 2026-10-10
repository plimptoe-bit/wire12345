"""Findings: what the rules engine emits.

A Finding is never silently fixed — blockers become open items for the
customer/owner, warnings go to the assumptions/risk register.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..model import OpenItem
from ..sources import Citation

SEVERITIES = ("blocker", "warning", "info")


@dataclass
class Finding:
    id: str
    severity: str           # blocker|warning|info
    check: str              # machine name of the check
    message: str
    harness: str | None = None
    ref: str | None = None  # termination/segment/BOM-line id
    citations: list[Citation] = field(default_factory=list)
    proposed_default: str = ""
    lesson: str | None = None  # regression tag, e.g. "lesson-1"

    def cite(self) -> str:
        return "; ".join(c.short() for c in self.citations) if self.citations else ""


def findings_to_markdown(findings: list[Finding]) -> str:
    if not findings:
        return "No findings.\n"
    order = {s: i for i, s in enumerate(SEVERITIES)}
    rows = sorted(findings, key=lambda f: (order.get(f.severity, 9), f.harness or "", f.id))
    out = ["| ID | Severity | Harness | Ref | Finding | Source | Proposed default |",
           "|---|---|---|---|---|---|---|"]
    for f in rows:
        out.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            f.id, f.severity.upper(), f.harness or "—", f.ref or "—",
            f.message.replace("|", "/"), f.cite().replace("|", "/"),
            f.proposed_default.replace("|", "/") or "—"))
    return "\n".join(out) + "\n"


def findings_to_open_items(findings: list[Finding]) -> list[OpenItem]:
    items = []
    for f in findings:
        if f.severity != "blocker":
            continue
        items.append(OpenItem(
            id=f"OI-{f.id}",
            question=f.message,
            impact=f"Check '{f.check}' failed; affected: {f.harness or 'program'}"
                   f"{' / ' + f.ref if f.ref else ''}. Sources: {f.cite()}",
            proposed_default=f.proposed_default,
            owner="customer",
            status="open",
            refs=[f.id],
        ))
    return items
