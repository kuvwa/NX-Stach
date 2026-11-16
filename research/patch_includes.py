import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

if '#include "steamsearch.h"' not in s:
    s = s.replace('#include "upload.h"', '#include "upload.h"\n#include "steamsearch.h"', 1)

if "#include <sys/stat.h>" not in s:
    s = s.replace("#include <math.h>", "#include <math.h>\n#include <sys/stat.h>", 1)

open(p, "w", encoding="utf-8").write(s)
print("ok")
