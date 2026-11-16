import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s:\n%s" % (path, old[:160]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


patch("source/audio.h", [
("""    SFX_ERROR,
    SFX_START,
    SFX_COUNT""",
 """    SFX_ERROR,
    SFX_START,
    SFX_TOGGLE,
    SFX_COUNT"""),
])

patch("source/audio.c", [
# мягкая атака + затухание
("""static void add_tone(s16 *dst, int *frame, int frames, float freq, float amp,
                     float decay)
{
    for (int i = 0; i < frames && *frame < MAX_FRAMES; i++, (*frame)++) {
        float t = (float)i / (float)SAMPLE_RATE;
        float env = expf(-decay * t);
        float v = sinf(2.0f * 3.14159265f * freq * t) * env * amp;""",
 """static void add_tone(s16 *dst, int *frame, int frames, float freq, float amp,
                     float decay)
{
    const int attack = SAMPLE_RATE / 250;   // ~4 мс мягкого нарастания

    for (int i = 0; i < frames && *frame < MAX_FRAMES; i++, (*frame)++) {
        float t = (float)i / (float)SAMPLE_RATE;
        float env = expf(-decay * t);

        if (i < attack)
            env *= (float)i / (float)attack;

        float v = sinf(2.0f * 3.14159265f * freq * t) * env * amp;"""),

# новые, более тихие и мягкие звуки
("""    int f;

    // навигация: короткий клик
    f = 0;
    add_tone(samples[SFX_NAV], &f, 700, 1180.0f, 0.22f, 60.0f);
    sample_bytes[SFX_NAV] = (size_t)f * CHANNELS * sizeof(s16);

    // подтверждение: два тона вверх
    f = 0;
    add_tone(samples[SFX_OK], &f, 900, 660.0f, 0.26f, 26.0f);
    add_tone(samples[SFX_OK], &f, 1800, 990.0f, 0.26f, 22.0f);
    sample_bytes[SFX_OK] = (size_t)f * CHANNELS * sizeof(s16);

    // назад: тон вниз
    f = 0;
    add_tone(samples[SFX_BACK], &f, 1400, 520.0f, 0.24f, 26.0f);
    add_tone(samples[SFX_BACK], &f, 900, 380.0f, 0.22f, 30.0f);
    sample_bytes[SFX_BACK] = (size_t)f * CHANNELS * sizeof(s16);

    // ошибка: низкий гудок
    f = 0;
    add_tone(samples[SFX_ERROR], &f, 3600, 190.0f, 0.28f, 12.0f);
    sample_bytes[SFX_ERROR] = (size_t)f * CHANNELS * sizeof(s16);

    // запуск: арпеджио вверх
    f = 0;
    add_tone(samples[SFX_START], &f, 1600, 523.0f, 0.22f, 16.0f);
    add_tone(samples[SFX_START], &f, 1600, 659.0f, 0.22f, 16.0f);
    add_tone(samples[SFX_START], &f, 2600, 784.0f, 0.24f, 12.0f);
    sample_bytes[SFX_START] = (size_t)f * CHANNELS * sizeof(s16);""",
 """    int f;

    // навигация: мягкий короткий тон
    f = 0;
    add_tone(samples[SFX_NAV], &f, 1100, 880.0f, 0.085f, 42.0f);
    sample_bytes[SFX_NAV] = (size_t)f * CHANNELS * sizeof(s16);

    // подтверждение: два мягких тона вверх
    f = 0;
    add_tone(samples[SFX_OK], &f, 1500, 587.0f, 0.095f, 20.0f);
    add_tone(samples[SFX_OK], &f, 2600, 880.0f, 0.095f, 16.0f);
    sample_bytes[SFX_OK] = (size_t)f * CHANNELS * sizeof(s16);

    // назад: тон вниз
    f = 0;
    add_tone(samples[SFX_BACK], &f, 1800, 494.0f, 0.085f, 20.0f);
    add_tone(samples[SFX_BACK], &f, 1400, 370.0f, 0.080f, 24.0f);
    sample_bytes[SFX_BACK] = (size_t)f * CHANNELS * sizeof(s16);

    // ошибка: низкий тихий гудок
    f = 0;
    add_tone(samples[SFX_ERROR], &f, 4200, 175.0f, 0.10f, 9.0f);
    sample_bytes[SFX_ERROR] = (size_t)f * CHANNELS * sizeof(s16);

    // запуск: арпеджио вверх
    f = 0;
    add_tone(samples[SFX_START], &f, 2200, 523.0f, 0.085f, 13.0f);
    add_tone(samples[SFX_START], &f, 2200, 659.0f, 0.085f, 13.0f);
    add_tone(samples[SFX_START], &f, 3200, 784.0f, 0.095f, 10.0f);
    sample_bytes[SFX_START] = (size_t)f * CHANNELS * sizeof(s16);

    // тумблер: характерный «двойной» щелчок, не похож на остальные
    f = 0;
    add_tone(samples[SFX_TOGGLE], &f, 900, 1318.0f, 0.085f, 55.0f);
    add_tone(samples[SFX_TOGGLE], &f, 1200, 988.0f, 0.080f, 50.0f);
    sample_bytes[SFX_TOGGLE] = (size_t)f * CHANNELS * sizeof(s16);"""),
])

# ---------- main: звук на вверх/вниз и на тумблер ----------
patch("source/main.c", [
("""                    if (kDown & HidNpadButton_Down) {
                        int next = selected + GRID_COLS;
                        if (next < view_count) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }
                    if (kDown & HidNpadButton_Up) {
                        int next = selected - GRID_COLS;
                        if (next >= 0) {
                            selected = next;
                            follow_selection = 1;
                        }
                    }""",
 """                    if (kDown & HidNpadButton_Down) {
                        int next = selected + GRID_COLS;
                        if (next < view_count) {
                            selected = next;
                            follow_selection = 1;
                            audio_play(SFX_NAV);
                        }
                    }
                    if (kDown & HidNpadButton_Up) {
                        int next = selected - GRID_COLS;
                        if (next >= 0) {
                            selected = next;
                            follow_selection = 1;
                            audio_play(SFX_NAV);
                        }
                    }"""),

("""                    only_locked = !only_locked;
                    list_scroll = list_target = 0.0f;
                    audio_play(SFX_NAV);""",
 """                    only_locked = !only_locked;
                    list_scroll = list_target = 0.0f;
                    audio_play(SFX_TOGGLE);"""),
])
