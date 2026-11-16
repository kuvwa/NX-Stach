import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


# тост
rep("""    u32 *steam_icons[STEAM_MAX_RESULTS];""",
    """    u32 *steam_icons[STEAM_MAX_RESULTS];

    char toast[128] = "";
    int toast_frames = 0;""")

# модальный ввод — в начале обработки
rep("""        bool consumed = false;""",
    """        bool consumed = false;

        if (steam_mode == 1) {
            if (steam_result_count > 0) {
                if (kDown & HidNpadButton_Down)
                    steam_selected = (steam_selected + 1) % steam_result_count;
                if (kDown & HidNpadButton_Up)
                    steam_selected = (steam_selected + steam_result_count - 1) %
                                     steam_result_count;
                if (kDown & HidNpadButton_A)
                    import_request = 1;
            }

            if (kDown & HidNpadButton_B)
                steam_mode = 0;

            consumed = true;
        }""")

# поиск: Y на экране игры, если каталога нет
rep("""            } else if (screen == 1) {
                if (kDown & HidNpadButton_B) {""",
    """            } else if (screen == 1) {
                if ((kDown & HidNpadButton_Y) && achievement_count <= 0) {
                    Game *g = &games[view[selected]];
                    char query[96];

                    snprintf(query, sizeof(query), "%s", g->name);

                    if (ask_search(query, sizeof(query)) && query[0]) {
                        draw_progress(&fb, face, face_small, "Поиск в Steam...",
                                      query, 25);

                        steam_result_count = steam_search(query, steam_results,
                                                          STEAM_MAX_RESULTS);

                        for (int i = 0; i < steam_result_count; i++) {
                            char line[96];
                            snprintf(line, sizeof(line), "Иконка %d / %d",
                                     i + 1, steam_result_count);

                            draw_progress(&fb, face, face_small, "Поиск в Steam...",
                                          line, 30 + 60 * i /
                                          (steam_result_count ? steam_result_count : 1));

                            free(steam_icons[i]);
                            steam_icons[i] = steam_fetch_capsule(steam_results[i].appid);
                        }

                        steam_selected = 0;

                        if (steam_result_count > 0) {
                            steam_mode = 1;
                        } else {
                            snprintf(toast, sizeof(toast), "В Steam ничего не найдено");
                            toast_frames = 180;
                        }
                    }
                }

                if (kDown & HidNpadButton_B) {""")

# тост на экране
rep("""        framebufferEnd(&fb);""",
    """        if (toast_frames > 0) {
            int tw = measure_text(face_small, toast);
            int bw = tw + 48;

            if (bw > W - 80) bw = W - 80;

            int bx = (W - bw) / 2;
            int by = H - 92;

            round_rect(pixels, bx, by, bw, 44, 14, RGBA8_MAXALPHA(52, 56, 63));

            clip_left = bx + 20;
            clip_right = bx + bw - 20;
            set_text_color(235, 240, 250);
            draw_text(face_small, pixels, bx + 24, by + 29, toast);
            reset_text_color();
            clip_left = 0;
            clip_right = W;

            toast_frames--;
        }

        framebufferEnd(&fb);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
