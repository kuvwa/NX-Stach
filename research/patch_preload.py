import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- library: кэш-только + больше слотов ----------
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

s = s.replace("#define CACHE_SLOTS 24", "#define CACHE_SLOTS 48", 1)

if "library_cover_cached" not in s:
    s = s.rstrip() + """

// Только из кэша: ничего не декодирует (безопасно вызывать в кадре).
const u32 *library_cover_cached(u64 title_id)
{
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++)
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].pixels;

    return NULL;
}
"""
    open(p, "w", encoding="utf-8").write(s)
    print("library ok")

# ---------- library.h ----------
p = os.path.join(ROOT, "source", "library.h")
s = open(p, encoding="utf-8").read()
if "library_cover_cached" not in s:
    s = s.replace("u32 library_cover_color(u64 title_id);",
                  "u32 library_cover_color(u64 title_id);\n\n"
                  "// Только из кэша, без декодирования.\nconst u32 *library_cover_cached(u64 title_id);", 1)
    open(p, "w", encoding="utf-8").write(s)
    print("library.h ok")

# ---------- main ----------
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:160])
    s = s.replace(old, new, 1)


# прогресс-экран для загрузки обложек
rep("/* --------------------------------- main --------------------------------- */",
r'''static void draw_cover_loading(Framebuffer *fb, FT_Face face, FT_Face face_small,
                               int done, int total)
{
    u32 stride;
    u32 *px = (u32 *)framebufferBegin(fb, &stride);
    fb_width = stride / sizeof(u32);

    fill_bg(px, COLOR_BG);

    clip_left = 0;
    clip_right = W;
    clip_top = 0;
    clip_bottom = H;

    draw_text(face, px, 55, 320, "Загрузка обложек...");

    char line[64];
    snprintf(line, sizeof(line), "%d / %d", done, total);

    set_text_color(170, 175, 185);
    draw_text(face_small, px, 55, 356, line);
    reset_text_color();

    round_rect(px, 55, 380, 1170, 14, 7, COLOR_TRACK);

    if (total > 0 && done > 0)
        round_rect(px, 55, 380, 1170 * done / total, 14, 7, COLOR_ACCENT);

    framebufferEnd(fb);
}

/* --------------------------------- main --------------------------------- */''')

# предзагрузка после library_load
rep("""    bool romfs_ready = R_SUCCEEDED(romfsInit());""",
    """    // обложки грузим один раз здесь: в кадре декодирования больше нет
    for (int i = 0; i < game_count; i++) {
        g_detail_id = (unsigned long long)games[i].title_id;
        beat("cover", i);

        if ((i % 2) == 0)
            beat_flush();

        draw_cover_loading(&fb, face, face_small, i, game_count);

        library_cover(games[i].title_id);
    }

    beat("cover_done", game_count);
    beat_flush();

    bool romfs_ready = R_SUCCEEDED(romfsInit());""")

# в кадре — только кэш
s = s.replace("const u32 *cover = library_cover(games[game_index].title_id);",
              "const u32 *cover = library_cover_cached(games[game_index].title_id);", 1)

s = s.replace("const u32 *cover = library_cover(game->title_id);",
              "const u32 *cover = library_cover_cached(game->title_id);", 1)

open(p, "w", encoding="utf-8").write(s)
print("main ok")
