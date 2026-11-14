# Real-document run 1: ICM paper, stage 01 only
Source: https://arxiv.org/pdf/2603.16021v2 (arXiv:2603.16021v2, 21 pages, 600,063 bytes). Saved at real-docs/icm-paper/icm-2603.16021v2.pdf. Workspace: real-docs/run-icm.
Evidence level: REAL-DOCUMENT TESTED for stage 01 (ingest, page map, segmentation) only. Stages 02-06 were NOT run (no LLM provider key). Not live-LLM tested.

Found on the real paper and fixed (with regression tests):
1. Printed page numbers were reported unknown: the number sits in a running header/footer that PyMuPDF merges into a larger block. Detection now also reads the first/last raw lines of each page. Result: offset 0, printed = pdf for all 21 pages, matching the visible page numbers on pdf p. 2, 7 and 21.
2. "Abstract" and "1 Introduction" are separate outline entries on pdf page 1. My duplicate-page fix had silently dropped the second title; shared-page entries are now joined ("Abstract / 1 Introduction").

Checks run by hand: every pdf page is in exactly one section; 11,150 words in the PDF vs 11,187 in the section files (the difference is the added section title lines); a sentence from the paper's stage-contract passage is present.
Section split (outline-based): 7 sections: Abstract/Intro (p.1), Background (2-4), ICM (5-9), Implementations (10-13), Discussion (14-15), Future (16-17), Conclusion/References (18-21). The References are inside the last section; the map gate should triage them as skip. Page-level splitting cannot separate Conclusion from References.
Claim fidelity (does a cited page support the claim?) is not checked by any tool and needs human review at the gates.
