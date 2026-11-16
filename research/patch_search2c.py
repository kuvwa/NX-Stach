import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

OLD = """        framebufferEnd(&fb);

        tick++;"""

NEW = r'''        if (steam_mode == 1) {
            for (int py = 0; py < H; py++) {
                for (int px = 0; px < W; px++) {
                    u32 *dst = &pixels[(size_t)py * fb_width + px];
                    *dst = blend_px(*dst, RGBA8_MAXALPHA(0, 0, 0), 150);
                }
            }

            int w = 660;
            int rows = steam_result_count > 0 ? steam_result_count : 1;
            int h = 120 + rows * 52;
            int x = (W - w) / 2;
            int y = (H - h) / 2;

            round_rect(pixels, x, y, w, h, 22, RGBA8_MAXALPHA(42, 45, 51));

            draw_text(face_small, pixels, x + 28, y + 46, "Найдено в Steam");

            for (int i = 0; i < steam_result_count; i++) {
                int ry = y + 70 + i * 52;

                if (i == steam_selected)
                    round_rect(pixels, x + 16, ry, w - 32, 44, 12,
                               RGBA8_MAXALPHA(62, 66, 74));

                if (i == steam_selected) set_text_color(240, 245, 252);
                else set_text_color(190, 195, 205);

                clip_left = x + 30;
                clip_right = x + w - 30;
                draw_text(face_small, pixels, x + 30, ry + 28,
                          steam_results[i].name);
                clip_left = 0;
                clip_right = W;
                reset_text_color();
            }

            set_text_color(140, 145, 155);
            draw_text(face_small, pixels, x + 28, y + h - 20,
                      "A: импортировать    B: отмена");
            reset_text_color();
        }

        if (toast_frames > 0) {
            int tw = measure_text(face_small, toast);
            int w = tw + 48;
            int x = (W - w) / 2;
            int y = H - 110;

            round_rect(pixels, x, y, w, 46, 14, RGBA8_MAXALPHA(52, 56, 63));
            set_text_color(235, 240, 250);
            draw_text(face_small, pixels, x + 24, y + 30, toast);
            reset_text_color();

            toast_frames--;
        }

        framebufferEnd(&fb);

        tick++;'''

if OLD not in s:
    raise SystemExit("framebufferEnd mark not found")

s = s.replace(OLD, NEW, 1)
open(p, "w", encoding="utf-8").write(s)
print("modal ok")
