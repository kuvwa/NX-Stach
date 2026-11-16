import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """            if (!touch_dragged)
                grid_scroll += (grid_target - grid_scroll) * 0.35f;
        }"""

new = """            if (!touch_dragged)
                grid_scroll += (grid_target - grid_scroll) * 0.35f;
        }

        {
            float view = (float)(LIST_BOTTOM - LIST_TOP);
            float max_scroll = (float)list_total_height - view;

            if (max_scroll < 0) max_scroll = 0;

            if (list_target < 0) list_target = 0;
            if (list_target > max_scroll) list_target = max_scroll;
            if (list_scroll < 0) list_scroll = 0;
            if (list_scroll > max_scroll) list_scroll = max_scroll;

            if (!touch_dragged)
                list_scroll += (list_target - list_scroll) * 0.35f;
        }"""

if old not in s:
    raise SystemExit("clamp block not found")

s = s.replace(old, new, 1)

old2 = """            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            draw_scrollbar(pixels, W - 24, GRID_Y0, H - GRID_Y0 - 80,
                           rows * GRID_STEP_Y, 2 * GRID_STEP_Y,
                           (int)grid_scroll);"""

new2 = """            if (view_count == 0) {
                set_text_color(150, 155, 165);
                draw_text(face, pixels, 55, 340, "Ничего не найдено");
                reset_text_color();
            }

            int rows = (view_count + GRID_COLS - 1) / GRID_COLS;
            draw_scrollbar(pixels, W - 24, GRID_Y0, H - GRID_Y0 - 80,
                           rows * GRID_STEP_Y, 2 * GRID_STEP_Y,
                           (int)grid_scroll);"""

if old2 not in s:
    raise SystemExit("scrollbar block not found")

s = s.replace(old2, new2, 1)

open(p, "w", encoding="utf-8").write(s)
print("ok")
