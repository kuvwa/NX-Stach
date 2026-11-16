import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

start = s.find("static void add_tone(")
end = s.find("bool audio_init(void)")

if start < 0 or end < 0:
    raise SystemExit("sound block not found")

new_block = r'''static unsigned int noise_state = 0x1234567u;

static float next_noise(void)
{
    noise_state = noise_state * 1664525u + 1013904223u;
    return ((float)((noise_state >> 9) & 0x3FFF) / 8192.0f) - 1.0f;
}

// «Цокающий» звук: короткий низкий тон + щелчок шума, очень быстрое затухание.
static void add_click(s16 *dst, int *frame, int frames, float freq, float amp,
                      float decay, float noise_mix)
{
    const int attack = SAMPLE_RATE / 800;   // ~1.2 мс

    for (int i = 0; i < frames && *frame < MAX_FRAMES; i++, (*frame)++) {
        float t = (float)i / (float)SAMPLE_RATE;
        float env = expf(-decay * t);

        if (i < attack)
            env *= (float)i / (float)attack;

        float tone = sinf(2.0f * 3.14159265f * freq * t);
        float v = (tone * (1.0f - noise_mix) + next_noise() * noise_mix) * env * amp;
        int s = (int)(v * 32767.0f);

        if (s > 32767) s = 32767;
        if (s < -32768) s = -32768;

        dst[(*frame) * CHANNELS + 0] = (s16)s;
        dst[(*frame) * CHANNELS + 1] = (s16)s;
    }
}

static void build_sounds(void)
{
    for (int id = 0; id < SFX_COUNT; id++) {
        samples[id] = calloc(MAX_BYTES, 1);
        sample_bytes[id] = 0;
    }

    int f;

    // навигация: деревянный «ток»
    f = 0;
    add_click(samples[SFX_NAV], &f, 520, 420.0f, 0.16f, 95.0f, 0.55f);
    sample_bytes[SFX_NAV] = (size_t)f * CHANNELS * sizeof(s16);

    // подтверждение: два «тока» вверх
    f = 0;
    add_click(samples[SFX_OK], &f, 520, 520.0f, 0.15f, 80.0f, 0.5f);
    add_click(samples[SFX_OK], &f, 900, 700.0f, 0.14f, 55.0f, 0.45f);
    sample_bytes[SFX_OK] = (size_t)f * CHANNELS * sizeof(s16);

    // назад: «ток» вниз
    f = 0;
    add_click(samples[SFX_BACK], &f, 520, 430.0f, 0.15f, 85.0f, 0.55f);
    add_click(samples[SFX_BACK], &f, 800, 300.0f, 0.14f, 60.0f, 0.5f);
    sample_bytes[SFX_BACK] = (size_t)f * CHANNELS * sizeof(s16);

    // ошибка: глухой низкий «тук»
    f = 0;
    add_click(samples[SFX_ERROR], &f, 2600, 180.0f, 0.17f, 22.0f, 0.65f);
    sample_bytes[SFX_ERROR] = (size_t)f * CHANNELS * sizeof(s16);

    // запуск: три «тока» вверх
    f = 0;
    add_click(samples[SFX_START], &f, 700, 392.0f, 0.14f, 60.0f, 0.5f);
    add_click(samples[SFX_START], &f, 900, 523.0f, 0.14f, 55.0f, 0.48f);
    add_click(samples[SFX_START], &f, 1400, 659.0f, 0.15f, 40.0f, 0.45f);
    sample_bytes[SFX_START] = (size_t)f * CHANNELS * sizeof(s16);

    // тумблер: «клац-клац»
    f = 0;
    add_click(samples[SFX_TOGGLE], &f, 420, 760.0f, 0.15f, 140.0f, 0.6f);
    add_click(samples[SFX_TOGGLE], &f, 700, 480.0f, 0.14f, 95.0f, 0.6f);
    sample_bytes[SFX_TOGGLE] = (size_t)f * CHANNELS * sizeof(s16);
}

'''

s = s[:start] + new_block + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("audio ok")

# ---------- заставка: короче и без пропуска ----------
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """    PadState pad;
    padInitializeDefault(&pad);

    for (int frame = 0; frame < 135; frame++) {
        padUpdate(&pad);

        u32 down = padGetButtonsDown(&pad);

        if (frame > 25 && down)
            break;

        u32 stride;"""

new = """    for (int frame = 0; frame < 68; frame++) {
        u32 stride;"""

if old not in s:
    raise SystemExit("splash block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("splash ok")
