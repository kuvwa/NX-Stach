import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

if "#include <sys/stat.h>" not in s:
    s = s.replace("#include <stdarg.h>", "#include <stdarg.h>\n#include <sys/stat.h>", 1)

if "mkdir(DIR_NX, 0777)" not in s:
    s = s.replace("    build_sounds();",
                  '    #define DIR_NX "sdmc:/switch/NX-Stach"\n'
                  '    mkdir("sdmc:/switch", 0777);\n'
                  '    mkdir(DIR_NX, 0777);\n'
                  '\n'
                  '    build_sounds();', 1)

open(p, "w", encoding="utf-8").write(s)
print("ok")
