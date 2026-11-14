from skillsmith.verify import check_text, numbers_in
SRC = {"5","20","0.5","1000","30"}
cases = [
 # (label, text, expect_unsourced_tokens)
 ("table unsourced", "| Param | Value |\n|---|---|\n| k | 77 |\n", ["77"]),
 ("table sourced", "| k | 20 | - | p. 5 |\n", []),
 ("percent unsourced", "Use 45% of the budget.", ["45"]),
 ("percent sourced 30", "Use 30% of the budget.", []),
 ("percent but source has bare 30 only -> passes (norm drops %)", "Use 30% now", []),
 ("dollar unsourced", "Costs $99 per call.", ["99"]),
 ("dollar thousand sep", "Costs $1,000 per call.", []),
 ("decimal unsourced", "Set lr to 0.75.", ["0.75"]),
 ("decimal leading dot", "Set lr to .75.", ["75?"]),
 ("decimal sourced", "Set lr to 0.5.", []),
 ("number in heading unsourced", "## Step 88 of the plan\nbody", ["88"]),
 ("number in heading sourced", "## Use 20 chunks\n", []),
 ("hyphenated id", "See ch05-u02 and stage 01_ingest.", []),
 ("hyphen number range unsourced", "Use 15-25 items.", ["15","25"]),
 ("range sourced", "Use 5-20 items.", []),
 ("number-hyphen-word", "A 3-step process.", ["3?"]),
 ("number glued unit", "Use 64k context and 512MB.", ["64?","512?"]),
 ("negative", "Drop of -12 points.", ["12?"]),
 ("year", "In 2023 researchers said.", ["2023?"]),
 ("sci notation", "lr 1e-4 and 3e5", ["?"]),
 ("fraction", "Use 3/4 of tokens.", ["3","4"]),
 ("words", "Use twelve chunks of fifty tokens.", ["twelve?"]),
 ("version", "needs v1.2.3 or python 3.11", ["3.11?"]),
 ("example heading skip hides numbers", "## Example\nUse 9999 chunks.\n## Next\n", ["9999?"]),
 ("numbered list marker only", "1. Do this\n2. Do that\n", []),
 ("numbered list with unsourced number inside", "1. Use 4096 tokens\n", ["4096"]),
 ("comment line hides numbers", "Use 31337 <!-- unit:u01 -->", ["31337?"]),
 ("code fence hides numbers", "```\nuse 424242\n```\n", ["424242?"]),
 ("front matter hides numbers", "---\nname: x\ndescription: Use 8888 chunks\n---\nbody\n", ["8888?"]),
 ("page cite stripped even if wrong form", "see p. 999 and pp. 5-20", []),
 ("page cite 'page 999'", "see page 999", ["999?"]),
 ("thousand no sep", "Use 100000 docs", ["100000"]),
 ("ordinal", "the 3rd step and 1st", ["3?","1?"]),
 ("number at sentence end", "Chunk size is 77.", ["77"]),
 ("number followed by comma", "Sizes 77, 88 tokens", ["77","88"]),
 ("comma list collision", "Sizes 1,2,3 here", ["?"]),
 ("unicode minus / fullwidth", "Use ５５ chunks", ["55?"]),
 ("legit text w/ 'Grade A' and 'Step 1'", "Grade A evidence. Step 1 matters.", ["1?"]),
 ("table sep row", "|---|---|\n", []),
 ("time", "meet at 10:30", ["10?","30?"]),
 ("multi-line number in bullet", "- 5 chunks (p. 5)", []),
 ("bullet star number", "* 61 chunks", ["61"]),
 ("number in markdown link/url", "see https://x.org/a/123/b?id=456", ["123?"]),
 ("bold number", "**77** chunks", ["77"]),
 ("number in parens", "(77)", ["77"]),
 ("number after slash", "7/8", ["7","8"]),
]
for label, text, exp in cases:
    r = check_text(text, SRC)
    got = [u.number for u in r.unsourced]
    exp_clean = [e.rstrip("?") for e in exp]
    soft = any(e.endswith("?") for e in exp) 
    ok = (sorted(got) == sorted(exp_clean)) if not soft else None
    tag = "OK " if ok else ("?? " if soft else "BAD")
    print(f"{tag} {label:55s} got={got} checked={r.checked} expected={exp}")
