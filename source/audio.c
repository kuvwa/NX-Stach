#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <malloc.h>

#include "audio.h"

#define SAMPLE_RATE 48000
#define CHANNELS 2
#define MAX_SECONDS 0.30f
#define MAX_FRAMES ((int)(SAMPLE_RATE * MAX_SECONDS))
#define MAX_BYTES ((size_t)MAX_FRAMES * CHANNELS * sizeof(s16))

typedef struct {
    AudioOutBuffer buffer;
    s16 *data;
} SfxSlot;

static AudioOutBuffer out_buffer;
static s16 *out_data = NULL;
static bool ready = false;

static s16 *samples[SFX_COUNT];
static size_t sample_bytes[SFX_COUNT];

// «Стеклянный» тон: основной тон + негармонический призвук,
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

bool audio_init(void)
{
    if (ready) return true;

    build_sounds();

    if (R_FAILED(audoutInitialize()))
        return false;

    if (R_FAILED(audoutStartAudioOut()))
        return false;

    out_data = memalign(0x1000, (MAX_BYTES + 0xFFF) & ~0xFFF);

    if (!out_data)
        return false;

    memset(&out_buffer, 0, sizeof(AudioOutBuffer));
    out_buffer.buffer = out_data;
    out_buffer.buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
    out_buffer.data_size = 0;
    out_buffer.data_offset = 0;

    ready = true;
    return true;
}

void audio_exit(void)
{
    if (!ready) return;

    audoutStopAudioOut();
    audoutExit();

    free(out_data);
    out_data = NULL;

    for (int i = 0; i < SFX_COUNT; i++) {
        free(samples[i]);
        samples[i] = NULL;
    }

    ready = false;
}


void audio_play(SfxId id)
{
    if (!ready || id < 0 || id >= SFX_COUNT)
        return;

    if (!samples[id] || sample_bytes[id] == 0 || !out_data)
        return;

    memcpy(out_data, samples[id], sample_bytes[id]);

    out_buffer.data_size = (u32)sample_bytes[id];
    out_buffer.data_offset = 0;

    AudioOutBuffer *released = NULL;

    audoutPlayBuffer(&out_buffer, &released);
}
