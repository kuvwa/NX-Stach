import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """            if (!consumed && screen == 0) {"""

new = """            if (!consumed && screen == 0 && (kDown & HidNpadButton_Y)) {
                char query[64];
                snprintf(query, sizeof(query), "%s", search);

                if (ask_search(query, sizeof(query))) {
                    snprintf(search, sizeof(search), "%s", query);

                    view_count = 0;
                    selected = 0;
                    grid_scroll = grid_target = 0.0f;

                    for (int i = 0; i < game_count; i++)
                        if (text_contains(games[i].name, search))
                            view[view_count++] = i;
                }

                consumed = true;
            }

            if (!consumed && screen == 0) {"""

if old not in s:
    raise SystemExit("anchor not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
