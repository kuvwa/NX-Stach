import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:150])
    s = s.replace(old, new, 1)


# ---------- пустое состояние с кнопкой ----------
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
                const char *t1 = "Достижения не подключены";
                const char *t2 = "Найди игру в Steam — подтянем достижения, иконки и описания";

                int w1 = measure_text(face, t1);
                int w2 = measure_text(face_small, t2);

                set_text_color(225, 230, 240);
                draw_text(face, pixels, (W - w1) / 2, 470, t1);
                reset_text_color();

                set_text_color(140, 146, 158);
                draw_text(face_small, pixels, (W - w2) / 2, 505, t2);
                reset_text_color();

                round_rect(pixels, 330, 560, 620, 64, 16,
                           blend_px(COLOR_BG, COLOR_ACCENT, 110));

                set_text_color(242, 247, 255);
                draw_text(face_small, pixels, 360, 600,
                          "Импортировать из Steam по названию");
                reset_text_color();

                set_text_color(30, 45, 60);
                draw_text(face_small, pixels, 916, 600, "Y");
                reset_text_color();
            }""")

# ---------- тап по кнопке ----------
rep("""                } else if (tap_y >= 276 && tap_y <= 332) {""",
    """                } else if (achievement_count <= 0 &&
                           tap_x >= 330 && tap_x <= 950 &&
                           tap_y >= 560 && tap_y <= 624) {
                    kDown |= HidNpadButton_Y;
                } else if (tap_y >= 276 && tap_y <= 332) {""")

# ---------- модальное окно выбора из Steam ----------
rep("""        if (toast_frames > 0) {""",
    """        if (steam_mode == 1) {
            for (int py = 0; py < H; py++) {
                for (int px = 0; px < W; px++) {
                    u32 *dst = &pixels[(size_t)py * fb_width + px];
                    *dst = blend_px(*dst, RGBA8_MAXALPHA(0, 0, 0), 150);
                }
            }

            int rows = steam_result_count > 0 ? steam_result_count : 1;
            int w = 760;
            int h = 110 + rows * 58;
            int x = (W - w) / 2;
            int y = (H - h) / 2;

            round_rect(pixels, x, y, w, h, 22, RGBA8_MAXALPHA(42, 45, 51));

            set_text_color(210, 215, 225);
            draw_text(face_small, pixels, x + 28, y + 44, "Найдено в Steam");
            reset_text_color();

            for (int i = 0; i < steam_result_count; i++) {
                int ry = y + 64 + i * 58;

                if (i == steam_selected)
                    round_rect(pixels, x + 14, ry, w - 28, 50, 12,
                               RGBA8_MAXALPHA(62, 66, 74));

                if (steam_icons[i]) {
                    for (int j = 0; j < 44; j++) {
                        int py = ry + 3 + j;
                        if (py < 0 || py >= H) continue;

                        for (int k = 0; k < 44; k++) {
                            int px = x + 24 + k;
                            if (px < 0 || px >= W) continue;

                            pixels[(size_t)py * fb_width + px] =
                                steam_icons[i][(size_t)j * 44 + k];
                        }
                    }
                } else {
                    round_rect(pixels, x + 24, ry + 3, 44, 44, 8,
                               RGBA8_MAXALPHA(32, 34, 38));
                }

                if (i == steam_selected) set_text_color(240, 245, 252);
                else set_text_color(185, 190, 200);

                clip_left = x + 82;
                clip_right = x + w - 20;
                draw_text(face_small, pixels, x + 82, ry + 31,
                          steam_results[i].name);
                clip_left = 0;
                clip_right = W;
                reset_text_color();
            }

            set_text_color(140, 145, 155);
            draw_text(face_small, pixels, x + 28, y + h - 18,
                      "A: импортировать    B: отмена");
            reset_text_color();
        }

        if (toast_frames > 0) {""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
