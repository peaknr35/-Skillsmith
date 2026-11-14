"""Generate golden PDF fixtures (synthetic; no real paper). Run: python tests/make_fixtures.py"""
from pathlib import Path

import pymupdf

OUT = Path(__file__).parent / "fixtures"

BODY = [
    ("1 Introduction",
     "Flat retrieval fails when answers are spread across sections. We study hierarchical retrieval for long "
     "documents and report results on a 7B model with a 2k token context window. This section motivates the work "
     "and states scope: the method is not intended for single-fact lookup or tight latency budgets."),
    ("2 Method",
     "Chunk the document at 100 tokens. Embed each chunk, cluster the chunks, and summarize each cluster. "
     "Repeat until a single root remains. The default clustering threshold is 0.5 and the tested range was 0.3 to 0.7. "
     "Retrieve from every level of the tree rather than only the leaves."),
    ("2.1 Defaults",
     "Table 2 lists defaults. The summary length is 100 tokens per cluster. Using a threshold above 0.7 produced "
     "clusters that were too coarse in our tests. These defaults were tuned on narrative QA only."),
    ("3 Results",
     "Hierarchical retrieval improved accuracy by 20 points on multi-hop questions over flat top-k retrieval "
     "on the narrative QA benchmark. The gain was observational across three runs and was not replicated on code."),
    ("4 Limitations",
     "The approach adds indexing cost and latency. It did not help single-hop factual questions. We did not test "
     "models above 7B parameters, so scale effects are unknown."),
    ("5 Conclusion",
     "Practitioners building retrieval over long documents with cross-section questions should build a summary tree "
     "and retrieve from all levels. Single-fact lookup should keep flat retrieval."),
]


def build_sample(path: Path) -> None:
    doc = pymupdf.open()
    for roman, text in (("i", "Title page. Synthetic Test Paper for Skillsmith fixtures. No real content."),
                        ("ii", "Contents. 1 Introduction. 2 Method. 3 Results. 4 Limitations. 5 Conclusion.")):
        pg = doc.new_page()
        pg.insert_textbox(pymupdf.Rect(72, 100, 520, 300), text, fontsize=11)
        pg.insert_text((300, 800), roman, fontsize=10)
    for n, (head, body) in enumerate(BODY, 1):
        pg = doc.new_page()
        pg.insert_text((72, 90), head, fontsize=16)
        pg.insert_textbox(pymupdf.Rect(72, 130, 520, 400), body, fontsize=11)
        pg.insert_text((300, 800), str(n), fontsize=10)
    doc.save(path)


def build_scanned(path: Path) -> None:
    doc = pymupdf.open()
    for _ in range(3):
        pg = doc.new_page()
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 200), False)
        pix.clear_with(255)
        pg.insert_image(pymupdf.Rect(72, 72, 400, 400), pixmap=pix)
    doc.save(path)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build_sample(OUT / "sample.pdf")
    build_scanned(OUT / "scanned.pdf")
    print("fixtures written")
