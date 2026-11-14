import json
from skillsmith.schema import SkillSpec, SkillProposal
base = json.load(open(r"E:\Skillsmith\source-to-skill\tests\fixtures\skillspec_valid.json"))
print("valid fixture desc:", base["description"][:60])
SkillSpec.model_validate(base)
cases = ["Use when building retrieval over long documents or when answers miss details.",
 "use when lowercase start is used for retrieval over docs", "Builds retrieval over long documents for engineers.",
 "Use when I build retrieval over long documents.", "Use when we are building retrieval over long documents.",
 "Use when you want retrieval over long documents.", "Use when a user wants it; their team's work is long.",
 "Use when it's about your own docs", "Use when the user asks; I'd say", "Use whenever building something big enough",
 "Use when You build things", "Use when building retrieval over long documents; ours is bigger.", "Use when we're retrieving documents of length",
 "Use when students ask about Wii or I/O or we-b scraping tasks", "Use when yourself", "Use when 'I' appear", "Use when me and my team search"]
for d in cases:
    r = []
    for cls, kw in ((SkillSpec, dict(base, description=d)),
                    (SkillProposal, {"name": base["name"], "description": d, "role": "standard", "section_ids": ["ch01"]})):
        try: cls.model_validate(kw); r.append("ACCEPT")
        except Exception as e: r.append("reject")
    print(r, repr(d))
