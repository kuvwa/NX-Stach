import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


load_fn = (
"static void draw_cover_loading(Framebuffer *fb, FT_Face face, FT_Face face_small,\n"
"                               int done, int total)\n"
"{\n"
"    u32 stride;\n"
"    u32 *px = (u32 *)framebufferBegin(fb, &stride);\n"
"    fb_width = stride / sizeof(u32);\n"
"\n"
"    fill_bg(px, COLOR_BG);\n"
"\n"
"    clip_left = 0;\n"
"    clip_right = W;\n"
"    clip_top = 0;\n"
"    clip_bottom = H;\n"
"\n"
"    draw_text(face, px, 55, 320, \"Загрузка обложек...\");\n"
"\n"
"    char line[64];\n"
"    snprintf(line, sizeof(line), \"%d / %d\", done, total);\n"
"\n"
"    set_text_color(170, 175, 185);\n"
"    draw_text(face_small, px, 55, 356, line);\n"
"    reset_text_color();\n"
"\n"
"    round_rect(px, 55, 380, 1170, 14, 7, COLOR_TRACK);\n"
"\n"
"    if (total > 0 && done > 0)\n"
"        round_rect(px, 55, 380, 1170 * done / total, 14, 7, COLOR_ACCENT);\n"
"\n"
"    framebufferEnd(fb);\n"
"}\n"
"\n")

rep("static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)",
    load_fn + "static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)")

rep("        if ((i % 2) == 0)\n\n        draw_cover_loading",
    "        draw_cover_loading")

rep("                g_detail_id = (unsigned long long)games[game_index].title_id;\n\n"
    "                if ((i % 3) == 0 || i == selected)\n"
    "                const u32 *cover = library_cover_cached",
    "                const u32 *cover = library_cover_cached")

open(p, "w", encoding="utf-8").write(s)
print("ok")
