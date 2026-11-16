import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

decl = """static bool slot_free[SFX_COUNT];
static u64 slot_tick[SFX_COUNT];

"""
if s.count("static bool slot_free[SFX_COUNT];") > 1:
    s = s.replace(decl, "", 1)

if "static bool slot_free[SFX_COUNT];" not in s:
    raise SystemExit("decl missing")

s = s.replace("static SfxSlot slots[SFX_COUNT];",
              "static SfxSlot slots[SFX_COUNT];\nstatic bool slot_free[SFX_COUNT];\nstatic u64 slot_tick[SFX_COUNT];", 1)

open(p, "w", encoding="utf-8").write(s)
print("ok")
