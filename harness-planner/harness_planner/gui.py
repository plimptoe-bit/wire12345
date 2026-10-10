"""Clickable interface: a local web app styled like a Windows XP application.

    python3 -m harness_planner gui            # starts on http://127.0.0.1:8321
                                              # and opens the browser

The server binds to localhost only and drives the same engine as the CLI:
list programs, run checks, confirm checkpoints, generate deliverables, and
view/download every output. The page itself is harness_planner/gui/index.html;
`tools/build_demo.py` packs the same page with the example outputs into a
standalone double-clickable HarnessPlannerXP.html.
"""
from __future__ import annotations

import json
import threading
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import rules
from .cli import generate_all, _default_inventory
from .ingest import Checkpoints
from .ingest.checkpoints import ALL as ALL_CHECKPOINTS
from .inventory import Inventory
from .model import ProgramData

GUI_DIR = Path(__file__).parent / "gui"

TEXT_TYPES = {".md": "text/markdown", ".csv": "text/csv", ".txt": "text/plain",
              ".json": "application/json", ".svg": "image/svg+xml"}
BIN_TYPES = {".xlsx": ("application/vnd.openxmlformats-officedocument."
                       "spreadsheetml.sheet"),
             ".pdf": "application/pdf", ".png": "image/png"}

FILE_GROUPS = [
    ("management_summary", "Reports"), ("costing", "Reports"),
    ("architecture", "Interpretation"), ("findings", "Interpretation"),
    ("bom", "BOM & parts"), ("termination_map", "BOM & parts"),
    ("tooling", "Tooling"), ("qualification", "Tooling"),
    ("production_plan", "Production plan"),
    ("procurement", "Procurement"),
]


def _group_for(relpath: str) -> str:
    if relpath.startswith("formboards/"):
        return "Formboards"
    if relpath.startswith("work/"):
        return "Work files"
    for prefix, group in FILE_GROUPS:
        if Path(relpath).name.startswith(prefix):
            return group
    return "Other"


class Backend:
    """What the GUI can do; every path is validated against known programs."""

    def __init__(self, roots: list[Path], inventory: Path | None = None):
        self.roots = [Path(r).resolve() for r in roots]
        self.inventory = inventory

    # ------------------------------------------------------------------ #
    def program_dirs(self) -> dict[str, Path]:
        found: dict[str, Path] = {}
        for root in self.roots:
            if (root / "program.json").exists():
                found[root.name] = root
            for pj in sorted(root.glob("*/program.json")) + \
                    sorted(root.glob("*/*/program.json")):
                found[pj.parent.name] = pj.parent
        return found

    def _dir(self, program: str) -> Path:
        dirs = self.program_dirs()
        if program not in dirs:
            raise KeyError(f"unknown program '{program}'")
        return dirs[program]

    def _inventory_for(self, pdir: Path) -> Inventory:
        return Inventory.load(self.inventory or _default_inventory(pdir))

    # ------------------------------------------------------------------ #
    def list_programs(self) -> list[dict]:
        out = []
        for name, pdir in self.program_dirs().items():
            try:
                prog = ProgramData.load(pdir)
            except Exception as e:
                out.append({"id": name, "error": str(e)})
                continue
            cps = Checkpoints.load(pdir)
            out.append({
                "id": name,
                "name": prog.meta.name,
                "customer": prog.meta.customer,
                "revision": prog.meta.revision,
                "date": prog.meta.date,
                "volume_unit": prog.meta.volume_unit,
                "volumes": prog.meta.volumes_per_week,
                "planned_volumes": prog.meta.planned_volumes(),
                "harnesses": [{"drawing": h.drawing_number, "rev": h.revision,
                               "name": h.name or h.family,
                               "qty_per_set": h.qty_per_set}
                              for h in prog.harnesses],
                "checkpoints": {c: cps.data.get(c, {}) for c in ALL_CHECKPOINTS},
            })
        return out

    def check(self, program: str) -> dict:
        pdir = self._dir(program)
        prog = ProgramData.load(pdir)
        inv = self._inventory_for(pdir)
        findings, additions, _ = rules.run_all(prog, inv)
        return {
            "findings": [{
                "id": f.id, "severity": f.severity, "check": f.check,
                "harness": f.harness, "ref": f.ref, "message": f.message,
                "source": f.cite(), "proposed_default": f.proposed_default,
            } for f in findings],
            "additions": [{
                "harness": a.harness, "mpn": a.mpn,
                "qty_per_harness": a.qty_per_harness,
                "required_by": a.required_by, "when": a.when,
                "source": a.citation.short(), "note": a.note,
            } for a in additions],
        }

    def confirm(self, program: str, checkpoint: str, by: str,
                notes: str = "") -> dict:
        if checkpoint not in ALL_CHECKPOINTS:
            raise KeyError(f"unknown checkpoint '{checkpoint}'")
        if not by.strip():
            raise ValueError("a confirmation needs a name in 'by'")
        cps = Checkpoints.load(self._dir(program))
        cps.confirm(checkpoint, by=by.strip(), notes=notes)
        return {c: cps.data[c] for c in ALL_CHECKPOINTS}

    def generate(self, program: str) -> dict:
        pdir = self._dir(program)
        return generate_all(pdir, inventory_path=self.inventory)

    # ------------------------------------------------------------------ #
    def list_files(self, program: str) -> list[dict]:
        pdir = self._dir(program)
        out = []
        for sub in ("deliverables", "work"):
            base = pdir / sub
            if not base.exists():
                continue
            for f in sorted(base.rglob("*")):
                if not f.is_file() or f.suffix == ".pyc":
                    continue
                rel = str(f.relative_to(pdir))
                shown = str(f.relative_to(base)) if sub == "deliverables" \
                    else rel
                out.append({
                    "path": rel, "name": shown,
                    "group": _group_for(shown if sub == "deliverables"
                                        else rel),
                    "ext": f.suffix.lstrip("."),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
        return out

    def file_path(self, program: str, relpath: str) -> Path:
        pdir = self._dir(program)
        f = (pdir / relpath).resolve()
        if not str(f).startswith(str(pdir.resolve())) or not f.is_file():
            raise KeyError(f"no such file: {relpath}")
        return f


class _Handler(BaseHTTPRequestHandler):
    backend: Backend = None  # set by serve()

    # silence default request logging to stderr noise
    def log_message(self, fmt, *args):  # pragma: no cover
        pass

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, e, status=400):
        self._json({"error": str(e)}, status=status)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path in ("/", "/index.html"):
                body = (GUI_DIR / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif url.path == "/api/programs":
                self._json(self.backend.list_programs())
            elif url.path == "/api/files":
                self._json(self.backend.list_files(q["program"]))
            elif url.path == "/api/file":
                f = self.backend.file_path(q["program"], q["path"])
                ctype = TEXT_TYPES.get(f.suffix) or BIN_TYPES.get(f.suffix) \
                    or "application/octet-stream"
                body = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                if f.suffix in BIN_TYPES or q.get("download"):
                    self.send_header("Content-Disposition",
                                     f'attachment; filename="{f.name}"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._error("not found", 404)
        except KeyError as e:
            self._error(e, 404)
        except Exception as e:
            self._error(e, 500)

    def do_POST(self):
        url = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            if url.path == "/api/check":
                self._json(self.backend.check(data["program"]))
            elif url.path == "/api/generate":
                self._json(self.backend.generate(data["program"]))
            elif url.path == "/api/confirm":
                self._json(self.backend.confirm(
                    data["program"], data["checkpoint"],
                    data.get("by", ""), data.get("notes", "")))
            else:
                self._error("not found", 404)
        except (KeyError, ValueError) as e:
            self._error(e, 400)
        except Exception as e:
            self._error(e, 500)


def serve(roots: list[Path], inventory: Path | None = None,
          port: int = 8321, open_browser: bool = True) -> ThreadingHTTPServer:
    _Handler.backend = Backend(roots, inventory)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    print(f"Harness Planner XP running at {url}  (Ctrl+C to quit)")
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    return httpd


def main(roots: list[str], inventory: str | None, port: int,
         open_browser: bool = True):  # pragma: no cover
    httpd = serve([Path(r) for r in roots],
                  Path(inventory) if inventory else None, port, open_browser)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
