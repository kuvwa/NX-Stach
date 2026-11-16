import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                list_scroll = list_target = 0.0f;
                only_locked = 0;
                screen = 1;"""

new = """                list_scroll = list_target = 0.0f;
                only_locked = 0;

                for (int i = 0; i < view_count; i++) {
                    if (view[i] == import_title_index) {
                        selected = i;
                        break;
                    }
                }

                screen = 1;"""

if old not in s:
    raise SystemExit("anchor not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
