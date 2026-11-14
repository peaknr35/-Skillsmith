import sys, re, json, tempfile, shutil
from pathlib import Path
sys.path.insert(0, r"E:\Skillsmith\source-to-skill")
from tests import fakes
from skillsmith import runner, gates, workspace
from skillsmith.llm import FakeProvider
FIX = Path(r"E:\Skillsmith\source-to-skill\tests\fixtures\sample.pdf")

def two_map(user):
    d = json.loads(fakes._map(user)); sid = d["proposed_skills"][0]["section_ids"]
    h = len(sid)//2
    base = d["proposed_skills"][0]
    d["proposed_skills"] = [dict(base, name="skill-alpha", section_ids=sid[:h]), dict(base, name="skill-beta", section_ids=sid[h:])]
    return json.dumps(d)

def run(batch=None):
    root = Path(tempfile.mkdtemp(prefix="qa_s04_")); 
    w = workspace.scaffold(root / "w", FIX)
    calls = []
    def resp(system, user):
        if "stage 02_map" in user: return two_map(user)
        if "stage 04_consolidate" in user: calls.append(user)
        return fakes.responder(system, user)
    p = FakeProvider(resp)
    runner.run_stage(w, "01_ingest"); runner.run_stage(w, "02_map", p); gates.approve(w, "02_map")
    runner.run_stage(w, "03_extract", p)
    if batch: runner.BATCH_TOKENS = batch
    runner.run_stage(w, "04_consolidate", p)
    return w, calls

w, calls = run()
print("default: consolidation calls =", len(calls))
sm = json.loads((w.output("02_map")/"source_map.json").read_text())
for c in calls:
    name = re.search(r'"name": "([^"]+)"', c).group(1)
    ids = set(re.findall(r"^(\S+-u\d+):", c.split("All extracted units", 1)[1], re.M))
    secs = {i.rsplit("-u",1)[0] for i in ids}
    want = next(p["section_ids"] for p in sm["proposed_skills"] if p["name"]==name)
    print(" ", name, "sections in prompt", sorted(secs), "expected", want, "OK" if secs==set(want) else "MISMATCH")
src_text = " ".join((w.output("01_ingest")/"text"/f).read_text() for f in [p.name for p in (w.output("01_ingest")/"text").glob("*.md")])
print("--- tiny BATCH_TOKENS")
w2, calls2 = run(batch=50)
print("calls", len(calls2))
for c in calls2:
    name = re.search(r'"name": "([^"]+)"', c).group(1)
    ids = re.findall(r"^(\S+-u\d+):", c.split("All extracted units", 1)[1], re.M)
    print(" ", name, ids)
merge = [c for c in calls2 if "merge-u" in c]
print("merge calls:", len(merge))
st = (w2.output("01_ingest")/"text")
srcs = [p.read_text() for p in st.glob("*.md")]
for m in merge:
    leaks = [s[:40] for s in srcs for sent in re.findall(r"[A-Z][^.\n]{40,}\.", s) if sent in m]
    print("  merge prompt contains '[[ pdf p.' markers:", "pdf p." in m, "| source sentences leaked:", len(leaks))
