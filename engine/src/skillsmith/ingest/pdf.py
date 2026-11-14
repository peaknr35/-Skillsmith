"""PyMuPDF ingest: text blocks per page, printed-vs-PDF page offset, TOC."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


class IngestAbstain(Exception):
    """Source cannot be ingested faithfully (e.g. scanned PDF). Nothing is written."""


@dataclass
class Page:
    pdf_page: int
    printed_page: int | None
    label: str | None
    blocks: list[str]


@dataclass
class Ingested:
    pages: list[Page]
    toc: list[tuple[int, str, int]]  # (level, title, pdf_page)
    offset: int | None  # printed = pdf - offset ; None => unknown
    page_basis: str  # "printed" | "pdf"
    warnings: list[str] = field(default_factory=list)
    title: str = ""
    author: str = ""


_INT = re.compile(r"^\s*(\d{1,4})\s*$")


def _blocks(page: "pymupdf.Page") -> list[str]:
    out = []
    for b in page.get_text("blocks", sort=True):
        if b[6] != 0:  # image block
            continue
        text = " ".join(b[4].split())
        if text:
            out.append(text)
    return out


def _page_number_candidate(blocks: list[str]) -> int | None:
    for b in (blocks[:1] + blocks[-2:]):
        m = _INT.match(b)
        if m:
            return int(m.group(1))
    return None


def ingest_pdf(path: Path, min_chars_per_page: int = 25) -> Ingested:
    with pymupdf.open(path) as doc:  # closed on every exit path, including IngestAbstain
        return _ingest(doc, path, min_chars_per_page)


def _ingest(doc: "pymupdf.Document", path: Path, min_chars_per_page: int) -> Ingested:
    n = len(doc)
    if n == 0:
        raise IngestAbstain("PDF has no pages.")
    raw = [_blocks(doc[i]) for i in range(n)]
    total = sum(len(" ".join(b)) for b in raw)
    if total < min_chars_per_page * n:
        raise IngestAbstain(
            f"Only {total} text characters across {n} pages: likely a scanned PDF. "
            "OCR is out of scope for v1; supply a text PDF."
        )

    labels = [doc[i].get_label() or None for i in range(n)]
    cands = []
    for i in range(n):
        c = _page_number_candidate(raw[i])
        if c is None:  # running headers/footers get merged into bigger blocks: look at raw lines too
            lines = [ln.strip() for ln in doc[i].get_text("text").splitlines() if ln.strip()]
            for ln in lines[:3] + lines[-3:]:
                m = _INT.match(ln)
                if m:
                    c = int(m.group(1))
                    break
        cands.append((i + 1, c))
    votes = Counter(p - c for p, c in cands if c is not None)
    offset: int | None = None
    warnings: list[str] = []
    if votes:
        best, cnt = votes.most_common(1)[0]
        numbered = sum(votes.values())
        if cnt >= 3 and cnt / numbered >= 0.6:
            offset = best
    basis = "printed"
    if offset is None:
        basis = "pdf"
        warnings.append("Printed page offset not detected; printed pages are unknown (None). "
                        "Citations carry PDF pages only.")

    pages: list[Page] = []
    for i in range(n):
        pdf_p = i + 1
        printed = (pdf_p - offset) if offset is not None else None
        blocks = raw[i]
        # drop the bare page-number block so it does not pollute text
        if cands[i][1] is not None and basis == "printed":
            for j in (0, len(blocks) - 1, len(blocks) - 2):
                if 0 <= j < len(blocks) and _INT.match(blocks[j]):
                    blocks = blocks[:j] + blocks[j + 1:]
                    break
        pages.append(Page(pdf_p, printed if printed is not None and printed >= 1 else None, labels[i], blocks))

    toc = [(lvl, title.strip(), pg) for lvl, title, pg in doc.get_toc() if pg >= 1]
    md = doc.metadata or {}
    title = (md.get("title") or "").strip()
    if not title:  # fall back to the first line of the first page
        first = [b for b in raw[0] if len(b) > 8]
        title = first[0][:160] if first else ""
    return Ingested(pages, toc, offset, basis, warnings, title, (md.get("author") or "").strip())
