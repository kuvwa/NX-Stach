import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


rep('#include "history.h"', '#include "history.h"\n#include "audio.h"')

# ---------- заставка ----------
rep("""/* --------------------------------- main --------------------------------- */""",
    r'''static void show_splash(Framebuffer *fb, FT_Face face, FT_Face face_small)
{
    PadState pad;
    padInitializeDefault(&pad);

    for (int frame = 0; frame < 135; frame++) {
        padUpdate(&pad);

        u32 down = padGetButtonsDown(&pad);

        if (frame > 25 && down)
            break;

        u32 stride;
        u32 *px = (u32 *)framebufferBegin(fb, &stride);
        fb_width = stride / sizeof(u32);

        fill_bg(px, COLOR_BG);

        clip_left = 0;
        clip_right = W;
        clip_top = 0;
        clip_bottom = H;

        int tw = measure_text(face, "NX-Stach");
        draw_text_shine(face, px, (W - tw) / 2, H / 2 - 8, "NX-Stach",
                        frame * 30);

        const char *sub = "Developed by kuba";
        int sw = measure_text(face_small, sub);

        set_text_color(112, 118, 130);
        draw_text(face_small, px, (W - sw) / 2, H / 2 + 42, sub);
        reset_text_color();

        framebufferEnd(fb);
    }
}

/* --------------------------------- main --------------------------------- */''')

# ---------- вызов заставки ----------
rep("""    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""",
    """    audio_init();

    show_splash(&fb, face, face_small);

    Game games[MAX_GAMES];
    int game_count = library_load(games, MAX_GAMES);""")

# ---------- звуки ----------
rep("""                    if (kDown & HidNpadButton_Right)
                        selected = (selected + 1) % view_count;
                    if (kDown & HidNpadButton_Left)
                        selected = (selected + view_count - 1) % view_count;""",
    """                    if (kDown & HidNpadButton_Right) {
                        selected = (selected + 1) % view_count;
                        audio_play(SFX_NAV);
                    }

                    if (kDown & HidNpadButton_Left) {
                        selected = (selected + view_count - 1) % view_count;
                        audio_play(SFX_NAV);
                    }""")

rep("""                    if (sx) {
                        selected = (selected + sx + view_count) % view_count;
                        follow_selection = 1;
                    }""",
    """                    if (sx) {
                        selected = (selected + sx + view_count) % view_count;
                        follow_selection = 1;
                        audio_play(SFX_NAV);
                    }""")

rep("""                        if (next >= 0 && next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }""",
    """                        if (next >= 0 && next < view_count) {
                            selected = next;
                            follow_selection = 1;
                            audio_play(SFX_NAV);
                        }
                    }""")

rep("""                    ach_icons_load(game->steam_appid, achievement_count, achievements);
                    playtime_minutes = game_playtime_minutes(game->title_id);
                    build_header_bg(game->title_id);

                    screen = 1;""",
    """                    ach_icons_load(game->steam_appid, achievement_count, achievements);
                    playtime_minutes = game_playtime_minutes(game->title_id);
                    build_header_bg(game->title_id);

                    audio_play(SFX_OK);

                    screen = 1;""")

rep("""                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }""",
    """                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                    audio_play(SFX_BACK);
                }""")

rep("""                } else if (tap_y >= 276 && tap_y <= 332) {
                    only_locked = !only_locked;
                    list_scroll = list_target = 0.0f;
                    consumed = true;
                }""",
    """                } else if (tap_y >= 276 && tap_y <= 332) {
                    only_locked = !only_locked;
                    list_scroll = list_target = 0.0f;
                    audio_play(SFX_NAV);
                    consumed = true;
                }""")

rep("""                    int copied = gamesave_dump_to_sd(g->title_id);""",
    """                    audio_play(SFX_OK);

                    int copied = gamesave_dump_to_sd(g->title_id);""")

# ---------- выключение звука ----------
rep("""    if (net_ready) net_exit();
    ach_icons_clear();""",
    """    audio_exit();

    if (net_ready) net_exit();
    ach_icons_clear();""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
