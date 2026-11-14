"""QA drill: adversarial PDFs through ingest + segment. Run: python tests/qa/adversarial.py"""
import sys, re, tempfile, json
from pathlib import Path
import pymupdf
from skillsmith.ingest import ingest_pdf, segment
from skillsmith.ingest.pdf import IngestAbstain

OUT = Path(tempfile.mkdtemp(prefix="qa_pdf_"))
LOREM = ("The quick brown fox jumps over the lazy dog while the committee reviews the retrieval procedure in detail. ")

def add(doc, lines, number=None, h=842, fs=10):
    pg = doc.new_page()
    y = 40
    for ln in lines:
        hh = (fs*1.4) * (2 + len(ln) // int(440/(fs*0.55))) + 6
        r = pg.insert_textbox(pymupdf.Rect(60, y, 540, y + hh), ln, fontsize=fs)
        assert r >= 0, ('overflow', r, len(ln))
        y += hh + 4
    if number is not None:
        pg.insert_text((290, h - 30), str(number), fontsize=10)
    return pg

def pdf_no_numbers():
    d = pymupdf.open()
    for i in range(8):
        lines = ([f"{i//2+1} Section number {i//2+1} title"] if i % 2 == 0 else []) + [LOREM * 3]
        add(d, lines)
    p = OUT / "nonum.pdf"; d.save(p); return p

def pdf_outline(offset=10, chapters=4, per=3):
    d = pymupdf.open()
    for i in range(offset):
        add(d, [f"Front matter {i} " + LOREM * 2], number=None)
    toc = []
    pg = offset
    for c in range(chapters):
        for k in range(per):
            lines = ([f"Chapter {c+1} Heading text"] if k == 0 else []) + [LOREM * 4]
            add(d, lines, number=pg - offset + 1)
            if k == 0:
                toc.append([1, f"Chapter {c+1} Heading text", pg + 1])
            pg += 1
    d.set_toc(toc)
    p = OUT / "outline.pdf"; d.save(p); return p

def pdf_long():
    d = pymupdf.open()
    add(d, ["Chapter 1 Intro", LOREM * 3], number=1)
    for i in range(2, 40):
        lines = []
        if i % 7 == 0:
            lines.append(f"1.{i//7} Sub heading {i}")
        lines.append((LOREM * 6))
        add(d, lines, number=i)
    add(d, ["Chapter 2 Outro", LOREM * 3], number=40)
    p = OUT / "long.pdf"; d.save(p); return p

def pdf_toc_single():
    d = pymupdf.open()
    for i in range(6):
        add(d, ([ "Chapter 1 Only"] if i==0 else []) + [LOREM*3], number=i+1)
    d.set_toc([[1, "Chapter 1 Only", 1]])
    p = OUT / "single.pdf"; d.save(p); return p

def pdf_toc_unsorted_nested():
    d = pymupdf.open()
    for i in range(9):
        add(d, [f"Chapter {i//3+1} x" if i%3==0 else "", LOREM*3], number=i+1)
    # two chapters begin on the same page + one going backwards
    d.set_toc([[1,"A",1],[2,"A.1",2],[1,"B",4],[1,"C",4],[1,"D",3]])
    p = OUT / "weird_toc.pdf"; d.save(p); return p

def check(p, expect_offset=None, expect_basis=None):
    print(f"=== {p.name}")
    try:
        ing = ingest_pdf(p)
    except IngestAbstain as e:
        print("ABSTAIN", e); return
    print("offset", ing.offset, "basis", ing.page_basis, "warn", ing.warnings, "toc", ing.toc[:6])
    print("printed pages:", [pg.printed_page for pg in ing.pages])
    secs = segment(ing)
    for s in secs:
        print(f"  {s.id:10s} pdf {s.start_pdf}-{s.end_pdf} printed {s.printed_start}-{s.printed_end} tok~{s.tokens} title={s.title[:30]!r}")
    problems = []
    if expect_offset is not None and ing.offset != expect_offset: problems.append(f"offset {ing.offset} != {expect_offset}")
    if expect_basis and ing.page_basis != expect_basis: problems.append(f"basis {ing.page_basis} != {expect_basis}")
    # empties
    for s in secs:
        body = re.sub(r"\[\[[^\]]*\]\]", "", s.text).strip()
        if not body: problems.append(f"EMPTY section {s.id}")
        if s.end_pdf < s.start_pdf: problems.append(f"bad range {s.id}")
    # coverage: every pdf page appears in some section; text of every block present
    allt = "\n".join(s.text for s in secs)
    norm = lambda t: " ".join(t.split())
    allnorm = norm(allt)
    for pg in ing.pages:
        for b in pg.blocks:
            if norm(b) not in allnorm:
                problems.append(f"LOST block pdf p{pg.pdf_page}: {b[:50]!r}")
    # markers: each page marker occurs
    for pg in ing.pages:
        if f"pdf p. {pg.pdf_page}]]" not in allt:
            problems.append(f"missing marker for pdf p{pg.pdf_page}")
    # overlap/gaps
    cov = [0]*(len(ing.pages)+2)
    for s in secs:
        for q in range(s.start_pdf, s.end_pdf+1): cov[q]+=1
    over = [q for q in range(1,len(ing.pages)+1) if cov[q]>1]
    gap = [q for q in range(1,len(ing.pages)+1) if cov[q]==0]
    if over: problems.append(f"pages in >1 section: {over}")
    if gap: problems.append(f"pages in no section: {gap}")
    # section range consistent with markers in its text
    for s in secs:
        ms = [int(m) for m in re.findall(r"pdf p\. (\d+)\]\]", s.text)]
        if ms and (min(ms) != s.start_pdf or max(ms) != s.end_pdf):
            problems.append(f"{s.id} range {s.start_pdf}-{s.end_pdf} != markers {min(ms)}-{max(ms)}")
    # max tokens
    big = [s.id for s in secs if s.tokens > 8000]
    if big: problems.append(f"oversize {big}")
    print("PROBLEMS:" if problems else "OK", *problems[:12], sep="\n  " if problems else " ")

if __name__ == "__main__":
    check(pdf_no_numbers(), expect_offset=0, expect_basis="pdf")
    check(pdf_outline(), expect_offset=10, expect_basis="printed")
    check(pdf_long(), expect_offset=0, expect_basis="printed")
    check(pdf_toc_single())
    check(pdf_toc_unsorted_nested())

def pdf_long2(sub=True):
    d = pymupdf.open()
    add(d, ["Chapter 1 Intro", LOREM * 3], number=1)
    for i in range(2, 60):
        lines = []
        if sub and i % 9 == 0:
            lines.append(f"1.{i//9} Sub heading {i}")
        lines.append((LOREM * 9))
        add(d, lines, number=i, fs=6)
    add(d, ["Chapter 2 Outro", LOREM * 3], number=60)
    p = OUT / ("long2_sub.pdf" if sub else "long2_nosub.pdf"); d.save(p); return p

def pdf_bigpage():
    d = pymupdf.open()
    add(d, ["Chapter 1 Intro", LOREM * 3], number=1)
    pg = d.new_page()
    # one page with a single 40k-char paragraph at tiny font
    pg.insert_textbox(pymupdf.Rect(10,10,585,830), LOREM*400, fontsize=3)
    pg.insert_text((290, 812), "2", fontsize=6)
    add(d, ["Chapter 2 end", LOREM * 3], number=3)
    p = OUT / "bigpage.pdf"; d.save(p); return p

if __name__ == "__main__":
    check(pdf_long2(True), expect_offset=0, expect_basis="printed")
    check(pdf_long2(False), expect_offset=0, expect_basis="printed")
    check(pdf_bigpage())
