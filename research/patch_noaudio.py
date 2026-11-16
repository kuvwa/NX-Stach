import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# 1) include
s = s.replace('#include "audio.h"\n', "")

# 2) вызовы audio_play(...) — построчно
s = re.sub(r"[ \t]*audio_play\([^)]*\);[ \t]*\n", "", s)

# 3) audio_init / audio_exit / audio_update
s = re.sub(r"[ \t]*audio_init\(\);[ \t]*\n", "", s)
s = re.sub(r"[ \t]*audio_exit\(\);[ \t]*\n", "", s)
s = re.sub(r"[ \t]*audio_update\(\);[ \t]*\n", "", s)

# 4) отладочный блок
start = s.find("        {\n            int aid = -1, arc = 0, atot = 0;")
if start >= 0:
    end = s.find("        framebufferEnd(&fb);", start)
    if end > start:
        s = s[:start] + s[end:]

open(p, "w", encoding="utf-8").write(s)
print("main cleaned")

for f in ("source/audio.c", "source/audio.h"):
    path = os.path.join(ROOT, f)
    if os.path.exists(path):
        os.remove(path)
        print("removed", f)
