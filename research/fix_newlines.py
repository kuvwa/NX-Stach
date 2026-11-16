import re, io, os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "source", "main.c")
s = open(p, encoding="utf-8").read()

before = s.count("\\\\n")
s = s.replace("\\\\n", "\\n")
print("fixed literal \\\\n:", before)

open(p, "w", encoding="utf-8").write(s)
