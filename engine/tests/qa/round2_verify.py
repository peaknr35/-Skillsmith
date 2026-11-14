from skillsmith.verify import check_text
SRC={"5","20","1000","30","64"}
for t in ["Use 5-20 items (p. 5).","pp. 5-20 and p. 5","see page 5","Use 64k context","Use 64KB and 30ms","Use 1,000 docs","Use 5, 20, 30 items","Use 1,2,3 items","Use 5–20 items (en dash)","Use 5 to 20","5×20","~30","30%-50%","## Example\nUse 9999 chunks.\n## Next\nUse 8888\n","1.5x","Use 5, 7 or 9",". 75 ok  .75", "Use 77 (p. 5)","Fig. 3 shows","Table 2 lists","see Section 4.2","p.5","pages 5 and 20","[p. 5]","(pp. 5, 20)"]:
    r=check_text(t,SRC); print(repr(t),"->unsourced",[u.number for u in r.unsourced],"checked",r.checked)
