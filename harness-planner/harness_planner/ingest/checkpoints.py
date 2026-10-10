"""Human-confirmation checkpoints.

Interpretation is where errors hide (lesson 8), so the pipeline cannot flow
straight from ingestion to costing. Costing, procurement and formboard release
are gated on explicit confirmations recorded here — a checkpoint is confirmed
by a person, never by code.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

# standard checkpoints, in pipeline order
ARCHITECTURE = "CONFIRM_ARCHITECTURE"      # harness architecture table confirmed
VOLUME_UNITS = "CONFIRM_VOLUME_UNITS"      # sets vs harnesses, volumes confirmed
BLOCKERS = "RESOLVE_BLOCKERS"              # blocker findings answered or defaulted
FORMBOARD = "VALIDATE_FIRST_BOARD"         # first harness built & measured on board

ALL = [ARCHITECTURE, VOLUME_UNITS, BLOCKERS, FORMBOARD]

# which outputs each checkpoint gates
GATES = {
    "costing": [ARCHITECTURE, VOLUME_UNITS],
    "procurement": [ARCHITECTURE, VOLUME_UNITS, BLOCKERS],
    "formboard_release": [ARCHITECTURE, FORMBOARD],
}


class CheckpointPending(Exception):
    pass


class Checkpoints:
    def __init__(self, data: dict, path: Path | None = None):
        self.data = data
        self.path = path

    @classmethod
    def load(cls, program_dir: str | Path) -> "Checkpoints":
        path = Path(program_dir) / "checkpoints.json"
        data = json.loads(path.read_text()) if path.exists() else {}
        for cid in ALL:
            data.setdefault(cid, {"status": "pending", "by": "", "date": "",
                                  "notes": ""})
        return cls(data, path)

    def save(self):
        if self.path:
            self.path.write_text(json.dumps(self.data, indent=2))

    def confirm(self, checkpoint_id: str, by: str, notes: str = ""):
        self.data[checkpoint_id] = {
            "status": "confirmed", "by": by,
            "date": datetime.now().isoformat(timespec="seconds"), "notes": notes,
        }
        self.save()

    def reset(self, checkpoint_id: str, notes: str = ""):
        """A design revision or corrected interpretation re-opens a checkpoint."""
        self.data[checkpoint_id] = {"status": "pending", "by": "", "date": "",
                                    "notes": notes}
        self.save()

    def is_confirmed(self, checkpoint_id: str) -> bool:
        return self.data.get(checkpoint_id, {}).get("status") == "confirmed"

    def require(self, gate: str):
        """Raise CheckpointPending when a gated output is requested too early."""
        missing = [c for c in GATES.get(gate, []) if not self.is_confirmed(c)]
        if missing:
            raise CheckpointPending(
                f"output '{gate}' is gated on unconfirmed checkpoint(s): "
                f"{', '.join(missing)}. Confirm the harness architecture and the "
                "units of volume with the owner first (interaction rule 10.1).")

    def summary_markdown(self) -> str:
        rows = ["| Checkpoint | Status | By | Date | Notes |", "|---|---|---|---|---|"]
        for cid in ALL:
            c = self.data[cid]
            rows.append(f"| {cid} | {c['status']} | {c['by'] or '—'} | "
                        f"{c['date'] or '—'} | {c['notes'] or '—'} |")
        return "\n".join(rows) + "\n"
