"""Step 1 of ingestion: inventory the customer package.

Lists every file, type, page count, whether a PDF has a text layer, and flags
files whose revision could not be read. Uses poppler (pdftotext/pdftoppm) and
pypdf — both available in the standard environment.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

DRAWING_EXT = {".pdf", ".dxf", ".dwg", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TABLE_EXT = {".xlsx", ".xls", ".csv", ".tsv"}
DOC_EXT = {".docx", ".doc", ".txt", ".md", ".eml", ".msg"}

_REV_RE = re.compile(r"\brev(?:ision)?[.\s:]*([A-Z0-9]{1,3})\b", re.IGNORECASE)


@dataclass
class FileRecord:
    path: str
    kind: str              # drawing|table|document|data|other
    ext: str
    size_kb: float
    pages: int | None = None
    has_text_layer: bool | None = None
    revision_guess: str | None = None
    flags: list[str] = field(default_factory=list)


def _classify(ext: str) -> str:
    if ext in DRAWING_EXT:
        return "drawing"
    if ext in TABLE_EXT:
        return "table"
    if ext in DOC_EXT:
        return "document"
    if ext == ".json":
        return "data"
    return "other"


def _pdf_info(path: Path) -> tuple[int | None, bool | None, str | None]:
    pages, has_text, rev = None, None, None
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = len(reader.pages)
    except Exception:
        pass
    try:
        txt = subprocess.run(["pdftotext", "-l", "3", str(path), "-"],
                             capture_output=True, text=True, timeout=60).stdout
        has_text = len(txt.strip()) > 40
        m = _REV_RE.search(txt)
        rev = m.group(1) if m else None
    except Exception:
        pass
    return pages, has_text, rev


def inventory_package(package_dir: str | Path) -> list[FileRecord]:
    package_dir = Path(package_dir)
    records: list[FileRecord] = []
    for p in sorted(package_dir.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        ext = p.suffix.lower()
        rec = FileRecord(
            path=str(p.relative_to(package_dir)), kind=_classify(ext), ext=ext,
            size_kb=round(p.stat().st_size / 1024, 1),
        )
        if ext == ".pdf":
            rec.pages, rec.has_text_layer, rec.revision_guess = _pdf_info(p)
            if rec.has_text_layer is False:
                rec.flags.append("no text layer — rasterize and read visually / OCR")
        if rec.kind == "drawing" and not rec.revision_guess:
            rec.flags.append("revision not found — read title block / ask customer")
        if ext == ".dwg":
            rec.flags.append("binary DWG — request DXF or PDF export")
        records.append(rec)
    return records


def rasterize_pdfs(package_dir: str | Path, out_dir: str | Path, dpi: int = 200):
    """Rasterize every PDF so drawings can be read visually (no-text-layer case)."""
    package_dir, out_dir = Path(package_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for p in sorted(package_dir.rglob("*.pdf")):
        stem = p.stem.replace(" ", "_")
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(p),
                        str(out_dir / stem)], check=False, timeout=300)
        made += sorted(str(f) for f in out_dir.glob(f"{stem}*.png"))
    return made


def inventory_markdown(records: list[FileRecord]) -> str:
    rows = ["| File | Kind | Pages | Text layer | Revision | Flags |",
            "|---|---|---|---|---|---|"]
    for r in records:
        rows.append("| {} | {} | {} | {} | {} | {} |".format(
            r.path, r.kind, r.pages if r.pages is not None else "—",
            {True: "yes", False: "NO", None: "—"}[r.has_text_layer],
            r.revision_guess or "?", "; ".join(r.flags) or "—"))
    return "\n".join(rows) + "\n"
