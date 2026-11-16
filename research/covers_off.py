import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


rep("#define HEADER_H 168", "#define HEADER_H 168\n\n// обложки временно выключены (декодер валит приложение)\n#define COVERS_ENABLED 0")

rep("const u32 *cover = library_cover(games[game_index].title_id);",
    "const u32 *cover = COVERS_ENABLED\n                                    ? library_cover(games[game_index].title_id)\n                                    : NULL;")

rep("const u32 *cover = library_cover(game->title_id);",
    "const u32 *cover = COVERS_ENABLED ? library_cover(game->title_id) : NULL;")

# в списке игр показывать название на плашке
rep("""                else
                    round_rect(pixels, x, y, CARD_W, CARD_H, 8, COLOR_PANEL);""",
    """                else {
                    round_rect(pixels, x, y, CARD_W, CARD_H, 8, COLOR_PANEL);

                    clip_left = x + 8;
                    clip_right = x + CARD_W - 8;
                    set_text_color(205, 210, 220);
                    draw_text(face_small, pixels, x + 10, y + CARD_H / 2,
                              games[game_index].name);
                    reset_text_color();
                    clip_left = 0;
                    clip_right = W;
                }""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
