import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# убрать неиспользуемую функцию
start = s.find("// Квадратная иконка -> постер нужного размера (центральный кроп).")
end = s.find("static void draw_cover(u32 *fb,")

if start >= 0 and end > start:
    s = s[:start] + s[end:]

# белая рамка выбранной карточки + рестарт hover
rep("""                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);
                    int grow = (int)(hover_anim * 6.0f);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 34 + grow, glow, 78);
                }""",
    """                if (i == selected) {
                    u32 glow = library_cover_color(games[game_index].title_id);
                    int grow = (int)(hover_anim * 6.0f);

                    draw_glow(pixels, x - grow, y - grow, CARD_W + grow * 2,
                              10, 34 + grow, glow, 78);

                    round_rect(pixels, x - 3, y - 3, CARD_W + 6, CARD_H + 6,
                               10, COLOR_SELECT);
                }""")

rep("""            if (follow_selection) {
                int row = selected / GRID_COLS;""",
    """            if (follow_selection) {
                hover_anim = 0.55f;
                int row = selected / GRID_COLS;""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
