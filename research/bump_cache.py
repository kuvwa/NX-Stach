import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()
s = s.replace("#define CACHE_SLOTS 8", "#define CACHE_SLOTS 24")
open(p, "w", encoding="utf-8").write(s)
print("cache slots:", "#define CACHE_SLOTS 24" in s)
