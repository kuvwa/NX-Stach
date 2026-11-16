import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

start = s.find("static unsigned int noise_state")
end = s.find("bool audio_init(void)")

if start < 0 or end < 0:
    raise SystemExit("sound block not found")

block = r'''// «Стеклянный» тон: основной тон + негармонический призвук,
// мягкая атака и быстрое, но плавное затухание.
static void add_glass(s16 *dst, int *frame, int frames, float freq, float amp,
                      float decay)
{
    const int attack = SAMPLE_RATE / 400;   // ~2.5 мс

    for (int i = 0; i < frames && *frame < MAX_FRAMES; i++, (*frame)++) {
        float t = (float)i / (float)SAMPLE_RATE;
        float env = expf(-decay * t);

        if (i < attack)
            env *= (float)i / (float)attack;

        float w = 2.0f * 3.14159265f * t;

        float v = sinf(w * freq) * 0.72f
                + sinf(w * freq * 2.02f) * 0.20f
                + sinf(w * freq * 3.07f) * 0.08f;

        v *= env * amp;

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

    // навигация: короткий стеклянный «тинь»
    f = 0;
    add_glass(samples[SFX_NAV], &f, 1500, 1480.0f, 0.13f, 42.0f);
    sample_bytes[SFX_NAV] = (size_t)f * CHANNELS * sizeof(s16);

    // подтверждение: два стеклянных тона вверх
    f = 0;
    add_glass(samples[SFX_OK], &f, 1200, 1175.0f, 0.12f, 26.0f);
    add_glass(samples[SFX_OK], &f, 2600, 1568.0f, 0.12f, 20.0f);
    sample_bytes[SFX_OK] = (size_t)f * CHANNELS * sizeof(s16);

    // назад: два тона вниз
    f = 0;
    add_glass(samples[SFX_BACK], &f, 1300, 1318.0f, 0.12f, 26.0f);
    add_glass(samples[SFX_BACK], &f, 2000, 988.0f, 0.11f, 22.0f);
    sample_bytes[SFX_BACK] = (size_t)f * CHANNELS * sizeof(s16);

    // ошибка: низкий, глухой стеклянный удар
    f = 0;
    add_glass(samples[SFX_ERROR], &f, 4200, 392.0f, 0.14f, 9.0f);
    sample_bytes[SFX_ERROR] = (size_t)f * CHANNELS * sizeof(s16);

    // запуск: стеклянное арпеджио
    f = 0;
    add_glass(samples[SFX_START], &f, 1800, 880.0f, 0.11f, 18.0f);
    add_glass(samples[SFX_START], &f, 1800, 1108.0f, 0.11f, 17.0f);
    add_glass(samples[SFX_START], &f, 3200, 1318.0f, 0.12f, 13.0f);
    sample_bytes[SFX_START] = (size_t)f * CHANNELS * sizeof(s16);

    // тумблер: двойной стеклянный «клик»
    f = 0;
    add_glass(samples[SFX_TOGGLE], &f, 900, 1760.0f, 0.12f, 60.0f);
    add_glass(samples[SFX_TOGGLE], &f, 1600, 2093.0f, 0.11f, 38.0f);
    sample_bytes[SFX_TOGGLE] = (size_t)f * CHANNELS * sizeof(s16);
}

'''

s = s[:start] + block + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
