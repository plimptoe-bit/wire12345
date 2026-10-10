"""Source-of-truth tagging.

Every fact in the data model carries a Citation. Ranks follow the program
source hierarchy:

  1 application specification (authoritative)
  2 product specification / manufacturer customer drawing for the part
  3 manufacturer instruction sheet for a tool
  4 customer harness drawing (can be wrong)
  5 distributor data (single-source EOL notes are unconfirmed)
  6 unverified / own memory / synthetic fixture — never acceptable for a
    part number, tool number, dimension or price in a released deliverable
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

RANK_NAMES = {
    1: "application spec",
    2: "product spec / part drawing",
    3: "tool instruction sheet",
    4: "customer harness drawing",
    5: "distributor data",
    6: "unverified",
}


@dataclass
class Citation:
    rank: int = 6
    doc: str = ""            # document number, e.g. "TE 114-18858"
    revision: str = ""       # e.g. "Rev L"
    clause: str = ""         # e.g. "table 2"
    note: str = ""
    url: str | None = None
    url_verified: bool = False

    @property
    def rank_name(self) -> str:
        return RANK_NAMES.get(self.rank, "unknown")

    def short(self) -> str:
        bits = [b for b in (self.doc, self.revision, self.clause) if b]
        ref = ", ".join(bits) if bits else self.note or "no document"
        return f"[{self.rank_name}: {ref}]"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict | None) -> "Citation":
        if not d:
            return cls()
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


UNVERIFIED = Citation(rank=6, note="unverified — no document found yet")


def fixture(note: str = "synthetic fixture data") -> Citation:
    return Citation(rank=6, note=note)
