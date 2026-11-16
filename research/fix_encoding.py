import os, sys

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "source", "main.c")
text = open(p, "rb").read().decode("utf-8-sig")

fixed = text.encode("cp1251").decode("utf-8")
open(p, "wb").write(fixed.encode("utf-8"))

print("ok")
for line in fixed.splitlines():
    if "умеем" in line or "Какие" in line:
        print(line)
