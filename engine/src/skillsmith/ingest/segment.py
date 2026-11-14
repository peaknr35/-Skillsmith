"""Structure-aware segmentation: outline first, heading heuristics second, size-capped parts.

Not embedding-based semantic chunking: boundaries come from the PDF outline or heading
patterns, then a token cap splits long sections at subheadings and paragraphs."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .pdf import Ingested, Page

MAX_TOKENS = 8000
HEADING = re.compile(
    r"^(?:(?:chapter|part|appendix)\s+[\dIVXLC]+\b.*|\d{1,2}\.?\s+[A-Z][^.!?]{2,80}|"
    r"abstract|introduction|related work|background|method(?:s|ology)?|results?|discussion|"
    r"conclusions?|references)$",
    re.I,
)
SUBHEADING = re.compile(r"^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\.?\s+\S")
MARK = re.compile(r"^\[\[(?:printed p\. (\d+) \| )?pdf p\. (\d+)\]\]$")
SEP = "\n\n"


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class Section:
    id: str
    title: str
    start_pdf: int
    end_pdf: int
    printed_start: int | None
    printed_end: int | None
    text: str  # includes [[printed p. N | pdf p. M]] markers

    @property
    def tokens(self) -> int:
        return est_tokens(self.text)

    def pdf_pages(self) -> list[int]:
        return list(range(self.start_pdf, self.end_pdf + 1))


def _marker(pg: Page) -> str:
    if pg.printed_page is not None:
        return f"[[printed p. {pg.printed_page} | pdf p. {pg.pdf_page}]]"
    return f"[[pdf p. {pg.pdf_page}]]"


def _is_heading(block: str) -> bool:
    return len(block) < 90 and bool(HEADING.match(block.strip()))


def _page_range_text(pages: list[Page], lo: int, hi: int) -> str:
    out = []
    for pg in pages[lo - 1:hi]:
        out.append(_marker(pg))
        out.extend(pg.blocks)
    return SEP.join(out)


def _mk(sid: str, title: str, pages: list[Page], lo: int, hi: int, text: str) -> Section:
    return Section(sid, title, lo, hi, pages[lo - 1].printed_page, pages[hi - 1].printed_page, text)


def _from_toc(ing: Ingested) -> list[Section]:
    lvl1 = [t for t in ing.toc if t[0] == 1]
    by_page: dict[int, tuple] = {}
    for t in lvl1:  # entries sharing a page cannot be split at page granularity: join their titles
        if t[2] in by_page:
            prev = by_page[t[2]]
            by_page[t[2]] = (prev[0], f"{prev[1]} / {t[1]}", prev[2])
        else:
            by_page[t[2]] = t
    top = sorted(by_page.values(), key=lambda t: t[2])
    if len(top) < 2:
        return []
    n = len(ing.pages)
    out = []
    if top[0][2] > 1:  # pages before the first outline entry are kept, not dropped
        out.append(_mk("ch00", "Front matter", ing.pages, 1, top[0][2] - 1,
                       _page_range_text(ing.pages, 1, top[0][2] - 1)))
    for i, (_, title, start) in enumerate(top):
        end = (top[i + 1][2] - 1) if i + 1 < len(top) else n
        end = max(start, min(end, n))
        out.append(_mk(f"ch{i + 1:02d}", title, ing.pages, start, end,
                       _page_range_text(ing.pages, start, end)))
    return out


def _from_headings(ing: Ingested) -> list[Section]:
    """Walk blocks in order; every heading-looking block starts a new section."""
    cur_title, cur_lo, cur_blocks = "Document start", 1, []
    secs: list[tuple[str, int, int, list[str]]] = []
    last_page = 1
    for pg in ing.pages:
        mk = _marker(pg)
        cur_blocks.append(mk)
        for b in pg.blocks:
            if _is_heading(b) and len(" ".join(cur_blocks)) > 200:
                if cur_blocks and cur_blocks[-1] == mk:  # heading is first on the page: marker moves
                    cur_blocks.pop()
                    secs.append((cur_title, cur_lo, last_page, cur_blocks))
                else:
                    secs.append((cur_title, cur_lo, pg.pdf_page, cur_blocks))
                cur_title, cur_lo, cur_blocks = b.strip(), pg.pdf_page, [mk]
            cur_blocks.append(b)
        last_page = pg.pdf_page
    secs.append((cur_title, cur_lo, last_page, cur_blocks))
    out = []
    for i, (title, lo, hi, blocks) in enumerate(secs):
        out.append(_mk(f"ch{i + 1:02d}", title, ing.pages, lo, hi, SEP.join(blocks)))
    return out


def _split_huge(p: str, max_tokens: int) -> list[str]:
    """A single paragraph over the cap is cut at sentence boundaries (then hard-cut)."""
    limit = max_tokens * 4
    if len(p) <= limit:
        return [p]
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", p):
        while len(sent) > limit:
            if cur:
                out.append(cur)
                cur = ""
            out.append(sent[:limit])
            sent = sent[limit:]
        if cur and len(cur) + len(sent) + 1 > limit:
            out.append(cur)
            cur = ""
        cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out


def split_long(sec: Section, max_tokens: int = MAX_TOKENS) -> list[Section]:
    """Split at subheadings (then paragraphs) so each part fits the token cap.

    Every part starts with the page marker in force at its first paragraph, so page
    ranges stay exact and no marker is separated from its page content."""
    if sec.tokens <= max_tokens:
        return [sec]
    max_tokens = max(50, max_tokens - 60)  # headroom: markers are re-inserted after the split
    paras: list[str] = []
    for p in sec.text.split(SEP):
        paras.extend(_split_huge(p, max_tokens))
    groups: list[list[str]] = [[]]
    for p in paras:
        if SUBHEADING.match(p) and groups[-1] and est_tokens(SEP.join(groups[-1])) > max_tokens // 4:
            groups.append([])
        groups[-1].append(p)
    parts: list[list[str]] = [[]]
    for g in groups:
        units = [[p] for p in g] if est_tokens(SEP.join(g)) > max_tokens else [g]
        for unit in units:
            if parts[-1] and est_tokens(SEP.join(parts[-1] + unit)) > max_tokens:
                parts.append([])
            parts[-1].extend(unit)
    # marker fix-up: a marker belongs with the content that follows it
    cur_marker = None
    for i, part in enumerate(parts):
        while part and MARK.match(part[-1]) and i + 1 < len(parts):
            parts[i + 1].insert(0, part.pop())
        if part and not MARK.match(part[0]) and cur_marker:
            part.insert(0, cur_marker)
        for q in part:
            if MARK.match(q):
                cur_marker = q
    out = []
    for i, part in enumerate(p for p in parts if p):
        ms = [MARK.match(q) for q in part if MARK.match(q)]
        lo_m, hi_m = ms[0], ms[-1]
        lo = int(lo_m.group(2))
        hi = int(hi_m.group(2))
        out.append(Section(f"{sec.id}-p{i + 1}", f"{sec.title} (part {i + 1})", lo, hi,
                           int(lo_m.group(1)) if lo_m.group(1) else None,
                           int(hi_m.group(1)) if hi_m.group(1) else None, SEP.join(part)))
    return out


def segment(ing: Ingested, max_tokens: int = MAX_TOKENS) -> list[Section]:
    secs = _from_toc(ing) or _from_headings(ing)
    out: list[Section] = []
    for s in secs:
        out.extend(split_long(s, max_tokens))
    return out
