import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

# точный якорь: блок ОТРИСОВКИ модального окна
anchor = "        if (steam_mode == 1) {\n            for (int py = 0; py < H; py++) {"

start = s.find(anchor)
if start < 0:
    raise SystemExit("modal draw block not found")

end = s.find("        if (toast_frames > 0) {", start)
if end < 0:
    raise SystemExit("toast block not found")

modal = r'''        if (steam_mode == 1) {
            for (int py = 0; py < H; py++) {
                for (int px = 0; px < W; px++) {
                    u32 *dst = &pixels[(size_t)py * fb_width + px];
                    *dst = blend_px(*dst, RGBA8_MAXALPHA(0, 0, 0), 150);
                }
            }

            const int visible = 8;
            int rows = steam_result_count < visible ? steam_result_count : visible;

            if (rows < 1) rows = 1;

            int w = 820;
            int h = 108 + rows * 58;
            int x = (W - w) / 2;
            int y = (H - h) / 2;

            round_rect(pixels, x, y, w, h, 22, RGBA8_MAXALPHA(42, 45, 51));

            char head[64];
            snprintf(head, sizeof(head), "Найдено в Steam: %d",
                     steam_result_count);

            set_text_color(210, 215, 225);
            draw_text(face_small, pixels, x + 28, y + 42, head);
            reset_text_color();

            int first = (steam_selected / visible) * visible;

            if (first > steam_result_count - visible)
                first = steam_result_count - visible;

            if (first < 0) first = 0;

            for (int row = 0; row < visible; row++) {
                int i = first + row;

                if (i >= steam_result_count) break;

                int ry = y + 62 + row * 58;

                if (i == steam_selected)
                    round_rect(pixels, x + 14, ry, w - 28, 50, 12,
                               RGBA8_MAXALPHA(62, 66, 74));

                if (!steam_icons[i])
                    steam_icons[i] = steam_fetch_capsule(steam_results[i].appid);

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

            char foot[96];
            snprintf(foot, sizeof(foot), "A: импортировать    B: отмена    %d / %d",
                     steam_selected + 1, steam_result_count);

            set_text_color(140, 145, 155);
            draw_text(face_small, pixels, x + 28, y + h - 16, foot);
            reset_text_color();
        }

'''

s = s[:start] + modal + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
