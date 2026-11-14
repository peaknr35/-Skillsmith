# Stage 01_ingest
## Inputs
Source PDF
## Process
Extract text, tables, algorithm boxes, equations, captions. Detect printed-vs-PDF page offset. Split into per-chapter/section files.
## Outputs
text/ch##.md (each chunk with printed+PDF page), page-map.md, toc.md
## Verify
Check outputs against _config/quality-checklist.md before finishing.
