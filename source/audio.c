#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <malloc.h>

#include "audio.h"

#define SAMPLE_RATE 48000
#define CHANNELS 2
#define POOL_SIZE 8
#define MAX_SECONDS 0.30f
#define MAX_FRAMES ((int)(SAMPLE_RATE * MAX_SECONDS))
#define MAX_BYTES ((size_t)MAX_FRAMES * CHANNELS * sizeof(s16))

typedef struct {
    AudioOutBuffer buffer;
    s16 *data;
    bool busy;
} SfxSlot;

static SfxSlot pool[POOL_SIZE];
static bool ready = false;

// короткие звуки: общий буфер-образец под каждый тип
static s16 *samples[SFX_COUNT];
static size_t sample_bytes[SFX_COUNT];

static unsigned int noise_state = 0x1234567u;

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

bool audio_init(void)
{
    if (ready) return true;

    build_sounds();

    if (R_FAILED(audoutInitialize()))
        return false;

    if (R_FAILED(audoutStartAudioOut()))
        return false;

    for (int i = 0; i < POOL_SIZE; i++) {
        pool[i].data = memalign(0x1000, MAX_BYTES);
        if (!pool[i].data) return false;

        memset(&pool[i].buffer, 0, sizeof(AudioOutBuffer));
        pool[i].buffer.buffer = pool[i].data;
        pool[i].buffer.buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
        pool[i].busy = false;
    }

    ready = true;
    return true;
}

void audio_exit(void)
{
    if (!ready) return;

    audoutStopAudioOut();
    audoutExit();

    for (int i = 0; i < POOL_SIZE; i++) {
        free(pool[i].data);
        pool[i].data = NULL;
    }

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

    if (!samples[id] || sample_bytes[id] == 0)
        return;

    // освобождаем проигранные буферы
    AudioOutBuffer *released = NULL;
    u32 released_count = 0;

    while (R_SUCCEEDED(audoutGetReleasedAudioOutBuffer(&released, &released_count)) &&
           released_count > 0) {
        for (int i = 0; i < POOL_SIZE; i++) {
            if ((AudioOutBuffer *)&pool[i].buffer == released)
                pool[i].busy = false;
        }
    }

    int slot = -1;

    for (int i = 0; i < POOL_SIZE; i++) {
        if (!pool[i].busy) {
            slot = i;
            break;
        }
    }

    if (slot < 0)
        return;

    memcpy(pool[slot].data, samples[id], sample_bytes[id]);

    pool[slot].buffer.data_size = (u32)sample_bytes[id];
    pool[slot].buffer.data_offset = 0;

    if (R_SUCCEEDED(audoutAppendAudioOutBuffer(&pool[slot].buffer)))
        pool[slot].busy = true;
}
