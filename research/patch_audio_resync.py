import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

old = """    u64 now = armGetSystemTick();
    u64 elapsed = armTicksToNs(now - audio_start_tick);"""

new = """    u64 now = armGetSystemTick();
    u64 elapsed = armTicksToNs(now - audio_start_tick);

    // если поток долго не кормили (заставка, тяжёлый кадр) — синхронизируемся
    if (elapsed > audio_produced_ns + 400000000ULL)
        audio_produced_ns = elapsed;"""

if old not in s:
    raise SystemExit("anchor not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
