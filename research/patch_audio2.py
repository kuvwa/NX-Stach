import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


rep("""                    if (kDown & HidNpadButton_Right) {
                        selected = (selected + 1) % view_count;
                        follow_selection = 1;
                    }
                    if (kDown & HidNpadButton_Left) {
                        selected = (selected + view_count - 1) % view_count;
                        follow_selection = 1;
                    }""",
    """                    if (kDown & HidNpadButton_Right) {
                        selected = (selected + 1) % view_count;
                        follow_selection = 1;
                        audio_play(SFX_NAV);
                    }
                    if (kDown & HidNpadButton_Left) {
                        selected = (selected + view_count - 1) % view_count;
                        follow_selection = 1;
                        audio_play(SFX_NAV);
                    }""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
