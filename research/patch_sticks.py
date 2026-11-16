import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# --- math.h
if "#include <math.h>" not in s:
    s = s.replace("#include <time.h>", "#include <time.h>\n#include <math.h>", 1)

# --- дубль условия в стике
rep("""                if (stick.y > 16000 || stick.y < -16000 || 
                    stick.y < -16000) {""",
    """                if (stick.y > 16000 || stick.y < -16000) {""")

# --- убрать неиспользуемую draw_toggle
rep("""static void draw_toggle(u32 *fb, int x, int y, bool on)
{
    round_rect(fb, x, y, 62, 32, 16, on ? COLOR_ACCENT : COLOR_TRACK);

    int knob = 24;
    int kx = on ? x + 62 - knob - 4 : x + 4;

    round_rect(fb, kx, y + 4, knob, knob, knob / 2, RGBA8_MAXALPHA(245, 248, 252));
}

""", "")

# --- helper автоповтора стика
rep("""/* ------------------------------ список строк ------------------------------ */""",
    r'''typedef struct {
    int dir_x;
    int dir_y;
    int frames;
} StickRepeat;

// Возвращает шаг стика с автоповтором: -1/0/1 по каждой оси.
static void stick_update(StickRepeat *st, HidAnalogStickState raw,
                         int *out_x, int *out_y)
{
    int dx = 0, dy = 0;

    if (raw.x > 16000) dx = 1;
    else if (raw.x < -16000) dx = -1;

    if (raw.y > 16000) dy = 1;
    else if (raw.y < -16000) dy = -1;

    *out_x = 0;
    *out_y = 0;

    if (dx == 0 && dy == 0) {
        st->frames = 0;
        st->dir_x = 0;
        st->dir_y = 0;
        return;
    }

    if (dx != st->dir_x || dy != st->dir_y) {
        st->dir_x = dx;
        st->dir_y = dy;
        st->frames = 0;
        *out_x = dx;
        *out_y = dy;
        return;
    }

    st->frames++;

    if (st->frames > 16 && (st->frames % 4) == 0) {
        *out_x = dx;
        *out_y = dy;
    }
}

/* ------------------------------ список строк ------------------------------ */''')

# --- объявления состояний стиков
rep("""    bool stick_latch = false;
    int hold_frames = 0;""",
    """    StickRepeat stick_left = {0};
    StickRepeat stick_right = {0};
    int hold_frames = 0;""")

# --- главный экран: оба стика
rep("""                HidAnalogStickState stick = padGetStickPos(&pad, 0);

                if (stick.y > 16000 || stick.y < -16000) {
                    if (!stick_latch) {
                        stick_latch = true;
                        grid_target += (stick.y > 0 ? GRID_STEP_Y : -GRID_STEP_Y);
                    }
                } else {
                    stick_latch = false;
                }
""",
    """                int sx = 0, sy = 0;

                stick_update(&stick_left, padGetStickPos(&pad, 0), &sx, &sy);

                if (sx && view_count > 0)
                    selected = (selected + sx + view_count) % view_count;
                if (sy)
                    grid_target -= (float)sy * (float)GRID_STEP_Y;

                stick_update(&stick_right, padGetStickPos(&pad, 1), &sx, &sy);

                if (sy)
                    grid_target -= (float)sy * (float)GRID_STEP_Y;
""")

# --- экран достижений: оба стика
rep("""                HidAnalogStickState stick = padGetStickPos(&pad, 1);

                if (stick.y > 16000 || stick.y < -16000) {
                    if (!stick_latch) {
                        stick_latch = true;
                        list_target += stick.y > 0 ? ROW_H : -ROW_H;
                    }
                } else {
                    stick_latch = false;
                }
""",
    """                int sx = 0, sy = 0;

                stick_update(&stick_left, padGetStickPos(&pad, 0), &sx, &sy);
                if (sy) list_target -= (float)sy * (float)ROW_H;

                stick_update(&stick_right, padGetStickPos(&pad, 1), &sx, &sy);
                if (sy) list_target -= (float)sy * (float)ROW_H;
""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
