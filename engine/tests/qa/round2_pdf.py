"""Round 2: text-conservation + marker checks over round-1 adversarial PDFs."""
import re, sys
sys.path.insert(0, __file__.rsplit("\\",1)[0] if "\\" in __file__ else __file__.rsplit("/",1)[0])
import adversarial as A
from skillsmith.ingest import ingest_pdf, segment
MK = re.compile(r"\[\[[^\]]*\]\]")
def words(t): return MK.sub(" ", t).split()
for mk in [A.pdf_no_numbers, A.pdf_outline, A.pdf_long, A.pdf_toc_single, A.pdf_toc_unsorted_nested,
           lambda: A.pdf_long2(True), lambda: A.pdf_long2(False), A.pdf_bigpage]:
    p = mk(); ing = ingest_pdf(p); secs = segment(ing)
    src = [w for pg in ing.pages for b in pg.blocks for w in b.split()]
    out = [w for s in secs for w in words(s.text)]
    starts = [bool(MK.match(s.text.lstrip())) for s in secs]
    # page-in-marker consistency
    bad=[]
    for s in secs:
        ms=[int(m) for m in re.findall(r"pdf p\. (\d+)\]\]", s.text)]
        if ms and (min(ms)!=s.start_pdf or max(ms)!=s.end_pdf): bad.append(s.id)
    print(p.name, "words src/out", len(src), len(out), "EQUAL" if src==out else "DIFF",
          "| all start with marker:", all(starts), "| range!=markers:", bad,
          "| max tok", max(s.tokens for s in secs))
