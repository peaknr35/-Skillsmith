"""Run the real CLI main() with the scripted fake provider swapped in. Usage: python cli_fake.py <cli args...>
Env QA_FAKE_MODE: normal | bad (always invalid JSON) | bad_extract (invalid only for stage 03)"""
import os, sys
sys.path.insert(0, r"E:\Skillsmith\source-to-skill")
from tests import fakes
from skillsmith import cli
from skillsmith.llm import FakeProvider
mode = os.environ.get("QA_FAKE_MODE", "normal")
def resp(system, user):
    if mode == "bad" or (mode == "bad_extract" and "stage 03_extract" in user):
        return "not json {"
    if mode == "bad_cite" and "stage 03_extract" in user:
        import json
        return json.dumps([{"title":"abc","triggers":["t"],"procedure":["p"],"boundaries":["b"],"failure_modes":["f"],"example":"exx",
            "evidence":[{"claim":"c","grade":"A","conditions":"c","cite":{"printed_page":9999}}]}])
    return fakes.responder(system, user)
cli.get_provider = lambda name, model=None: FakeProvider(resp)
raise SystemExit(cli.main(sys.argv[1:]))
