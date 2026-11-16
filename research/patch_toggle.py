import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


# функция рисования тумблера
rep("""static void draw_scrollbar(u32 *fb, int x, int y, int h, int content, int view, int scroll)""",
    r'''// Тумблер: пилюля со светлой окантовкой, синяя когда включён,
// и «резиновая» кнопка, которая вытягивается в процессе переключения.
static void draw_toggle(u32 *fb, int x, int y, float t)
{
    const int w = 64, h = 34;

    u32 on  = RGBA8_MAXALPHA(30, 144, 255);
    u32 off = RGBA8_MAXALPHA(70, 74, 82);

    // окантовка
    round_rect(fb, x, y, w, h, h / 2, RGBA8_MAXALPHA(196, 201, 210));

    // дорожка
    round_rect(fb, x + 2, y + 2, w - 4, h - 4, (h - 4) / 2,
               blend_px(off, on, (int)(255.0f * t)));

    // кнопка: вытягивается на середине пути
    int knob_h = 24;
    int stretch = (int)(13.0f * 4.0f * t * (1.0f - t));
    int knob_w = knob_h + stretch;

    int pad = 5;
    int travel = (w - pad * 2) - knob_w;
    if (travel < 0) travel = 0;

    int kx = x + pad + (int)((float)travel * t);
    int ky = y + (h - knob_h) / 2;

    // лёгкая тень
    round_rect(fb, kx + 1, ky + 1, knob_w, knob_h, knob_h / 2,
               blend_px(RGBA8_MAXALPHA(40, 42, 48), RGBA8_MAXALPHA(0, 0, 0), 60));

    round_rect(fb, kx, ky, knob_w, knob_h, knob_h / 2,
               RGBA8_MAXALPHA(250, 251, 254));
}

static void draw_scrollbar(u32 *fb, int x, int y, int h, int content, int view, int scroll)''')

# состояние анимации
rep("""    u32 tick = 0;
    float pulse = 1.0f;""",
    """    u32 tick = 0;
    float pulse = 1.0f;
    float toggle_anim = 0.0f;""")

# использование
rep("""            int kn = (int)((only_locked ? 1.0f : 0.0f) * 38.0f);

            round_rect(pixels, 1140, 252, 62, 32, 16,
                       only_locked ? COLOR_ACCENT : COLOR_TRACK);
            round_rect(pixels, 1144 + kn, 256, 24, 24, 12,
                       RGBA8_MAXALPHA(245, 248, 252));""",
    """            draw_toggle(pixels, 1138, 251, toggle_anim);""")

# обновление анимации
rep("""        tick++;
        pulse = 0.5f + 0.5f * sinf((float)tick * 0.055f);""",
    """        tick++;
        pulse = 0.5f + 0.5f * sinf((float)tick * 0.055f);

        toggle_anim += ((only_locked ? 1.0f : 0.0f) - toggle_anim) * 0.16f;""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
