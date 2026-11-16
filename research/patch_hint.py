import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:220])
    s = s.replace(old, new, 1)


# ---------- 1. X работает на обоих экранах ----------
old_x = """            if (!consumed && screen == 0 && (kDown & HidNpadButton_X) && view_count > 0) {
                char query[64];
                snprintf(query, sizeof(query), "%s", games[view[selected]].name);

                if (ask_search(query, sizeof(query)) && query[0]) {
                    steam_result_count = 0;
                    steam_selected = 0;

                    steam_result_count = steam_search(query, steam_results,
                                                      STEAM_MAX_RESULTS);

                    if (steam_result_count > 0) {
                        steam_mode = 1;
                        import_title_index = view[selected];
                    } else {
                        snprintf(toast, sizeof(toast), "В Steam ничего не найдено");
                        toast_frames = 150;
                    }
                }

                consumed = true;
            }

"""
rep(old_x, "")

shared_x = """        if (!consumed && (kDown & HidNpadButton_X) && view_count > 0) {
            char query[64];
            snprintf(query, sizeof(query), "%s", games[view[selected]].name);

            if (ask_search(query, sizeof(query)) && query[0]) {
                steam_result_count = 0;
                steam_selected = 0;

                steam_result_count = steam_search(query, steam_results,
                                                  STEAM_MAX_RESULTS);

                if (steam_result_count > 0) {
                    steam_mode = 1;
                    import_title_index = view[selected];
                } else {
                    snprintf(toast, sizeof(toast), "В Steam ничего не найдено");
                    toast_frames = 150;
                }
            }

            consumed = true;
        }

        if (!consumed) {
"""

rep("""        /* ----------------------------- навигация ----------------------------- */
        if (!consumed) {""",
    """        /* ----------------------------- навигация ----------------------------- */
""" + shared_x)

# ---------- 2. подсказка на главном ----------
rep("""            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            draw_scrollbar(pixels, W - 22, GRID_Y0, H - GRID_Y0 - 20,
                           rows * GRID_STEP_Y, H - GRID_Y0,
                           (int)grid_scroll);""",
    """            if (view_count > 0 && !games[view[selected]].steam_appid[0]) {
                const char *hint = "Добавить достижения из Steam";
                int text_w = measure_text(face_small, hint);
                int pill_w = text_w + 96;
                int pill_x = (W - pill_w) / 2;
                int pill_y = H - 84;

                round_rect(pixels, pill_x, pill_y, pill_w, 50, 14,
                           RGBA8_MAXALPHA(38, 41, 47));
                round_rect(pixels, pill_x, pill_y, pill_w, 50, 14,
                           blend_px(COLOR_BG, COLOR_ACCENT, 90));

                round_rect(pixels, pill_x + 18, pill_y + 11, 28, 28, 14,
                           RGBA8_MAXALPHA(74, 79, 88));

                set_text_color(238, 242, 250);
                draw_text(face_small, pixels, pill_x + 25, pill_y + 32, "X");
                draw_text(face_small, pixels, pill_x + 60, pill_y + 32, hint);
                reset_text_color();
            }

            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            draw_scrollbar(pixels, W - 22, GRID_Y0, H - GRID_Y0 - 20,
                           rows * GRID_STEP_Y, H - GRID_Y0,
                           (int)grid_scroll);""")

# ---------- 3. пустое состояние на экране игры ----------
rep("""            if (achievement_count <= 0) {
                set_text_color(150, 155, 165);
                draw_text(face_small, pixels, 55, 410, "Нет каталога достижений");
                draw_text(face_small, pixels, 55, 440,
                          game->steam_appid[0]
                          ? "Проверь romfs:/catalog/ и Steam AppID"
                          : "У игры не указан Steam AppID");
                reset_text_color();
            }""",
    """            if (achievement_count <= 0) {
                round_rect(pixels, 594, 362, 92, 92, 46, RGBA8_MAXALPHA(36, 39, 45));
                round_rect(pixels, 594, 362, 92, 92, 46,
                           blend_px(COLOR_BG, COLOR_ACCENT, 60));

                set_text_color(150, 175, 210);
                draw_text(face, pixels, 620, 424, "+");
                reset_text_color();

                const char *t1 = "Достижений пока нет";
                const char *t2 = "Найди игру в Steam — достижения и иконки подтянутся сами";

                int w1 = measure_text(face, t1);
                set_text_color(232, 236, 244);
                draw_text(face, pixels, (W - w1) / 2, 500, t1);
                reset_text_color();

                int w2 = measure_text(face_small, t2);
                set_text_color(143, 148, 162);
                draw_text(face_small, pixels, (W - w2) / 2, 530, t2);
                reset_text_color();

                round_rect(pixels, 420, 566, 440, 60, 16,
                           blend_px(COLOR_BG, COLOR_ACCENT, 110));

                round_rect(pixels, 446, 580, 32, 32, 16,
                           RGBA8_MAXALPHA(234, 242, 251));

                set_text_color(30, 45, 60);
                draw_text(face_small, pixels, 454, 603, "X");
                reset_text_color();

                set_text_color(242, 247, 255);
                draw_text(face_small, pixels, 492, 604, "Найти достижения в Steam");
                reset_text_color();
            }""")

# ---------- 4. тап по кнопке ----------
rep("""                } else if (tap_y >= 276 && tap_y <= 332) {""",
    """                } else if (achievement_count <= 0 &&
                           tap_x >= 420 && tap_x <= 860 &&
                           tap_y >= 566 && tap_y <= 626) {
                    kDown |= HidNpadButton_X;
                } else if (tap_y >= 276 && tap_y <= 332) {""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
