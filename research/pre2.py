import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


loading = (
"static void draw_loading(Framebuffer *fb, FT_Face face, FT_Face face_small,\n"
"                         int done, int total)\n"
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
    loading + "static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)")

# предзагрузка с журналом
rep("""    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""",
    """    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);

    // Обложки грузим здесь: в кадре декодирования нет.
    for (int i = 0; i < game_count; i++) {
        FILE *log = fopen("sdmc:/switch/NX-Stach/cover_log.txt", "w");

        if (log) {
            fprintf(log, "index=%d id=%016llX name=%s\\n", i,
                    (unsigned long long)games[i].title_id, games[i].name);
            fclose(log);
        }

        draw_loading(&fb, face, face_small, i, game_count);

        library_cover(games[i].title_id);
    }

    FILE *log = fopen("sdmc:/switch/NX-Stach/cover_log.txt", "w");
    if (log) {
        fprintf(log, "done %d\\n", game_count);
        fclose(log);
    }""")

# в кадре — только кэш
s = s.replace("const u32 *cover = library_cover(games[game_index].title_id);",
              "const u32 *cover = library_cover_cached(games[game_index].title_id);", 1)
s = s.replace("const u32 *cover = library_cover(game->title_id);",
              "const u32 *cover = library_cover_cached(game->title_id);", 1)

open(p, "w", encoding="utf-8").write(s)
print("main ok")
