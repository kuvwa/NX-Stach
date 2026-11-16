#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <malloc.h>

#include "audio.h"

#define SAMPLE_RATE 48000
#define CHANNELS 2

#define FRAMES_PER_BUF 512              // ~10.7 мс на буфер
#define RING_BUFS 8
#define TARGET_QUEUE 3                  // держим ~32 мс впереди
#define ACC_FRAMES (SAMPLE_RATE * 3)    // 3 секунды аккумулятора
#define MAX_SECONDS 0.35f
#define MAX_FRAMES ((int)(SAMPLE_RATE * MAX_SECONDS))
#define MAX_BYTES ((size_t)MAX_FRAMES * CHANNELS * sizeof(s16))

static bool ready = false;

static s16 *samples[SFX_COUNT];
static size_t sample_frames[SFX_COUNT];

static s16 acc[ACC_FRAMES * CHANNELS];
static int acc_read = 0;
static int acc_write = 0;

static AudioOutBuffer ring[RING_BUFS];
static s16 *ring_data[RING_BUFS];
static int ring_next = 0;

/* ----------------------------- генерация звуков ----------------------------- */

static void add_glass(s16 *dst, int *frame, int frames, float freq, float amp,
                      float decay)
{
    const int attack = SAMPLE_RATE / 400;

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
        sample_frames[id] = 0;
    }

    int f;

    f = 0;
    add_glass(samples[SFX_NAV], &f, 1500, 1480.0f, 0.13f, 42.0f);
    sample_frames[SFX_NAV] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_OK], &f, 1200, 1175.0f, 0.12f, 26.0f);
    add_glass(samples[SFX_OK], &f, 2600, 1568.0f, 0.12f, 20.0f);
    sample_frames[SFX_OK] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_BACK], &f, 1300, 1318.0f, 0.12f, 26.0f);
    add_glass(samples[SFX_BACK], &f, 2000, 988.0f, 0.11f, 22.0f);
    sample_frames[SFX_BACK] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_ERROR], &f, 4200, 392.0f, 0.14f, 9.0f);
    sample_frames[SFX_ERROR] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_START], &f, 1800, 880.0f, 0.11f, 18.0f);
    add_glass(samples[SFX_START], &f, 1800, 1108.0f, 0.11f, 17.0f);
    add_glass(samples[SFX_START], &f, 3200, 1318.0f, 0.12f, 13.0f);
    sample_frames[SFX_START] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_TOGGLE], &f, 900, 1760.0f, 0.12f, 60.0f);
    add_glass(samples[SFX_TOGGLE], &f, 1600, 2093.0f, 0.11f, 38.0f);
    sample_frames[SFX_TOGGLE] = (size_t)f;
}

/* --------------------------------- поток --------------------------------- */

static int acc_available(void)
{
    int diff = acc_write - acc_read;

    if (diff < 0)
        diff += ACC_FRAMES;

    return diff;
}

static void acc_push(s16 l, s16 r)
{
    int next = (acc_write + 1) % ACC_FRAMES;

    if (next == acc_read)
        return;   // переполнение — теряем самый старый кадр

    int sat_l = acc[acc_write * CHANNELS + 0] + l;
    int sat_r = acc[acc_write * CHANNELS + 1] + r;

    if (sat_l > 32767) sat_l = 32767;
    if (sat_l < -32768) sat_l = -32768;
    if (sat_r > 32767) sat_r = 32767;
    if (sat_r < -32768) sat_r = -32768;

    acc[acc_write * CHANNELS + 0] = (s16)sat_l;
    acc[acc_write * CHANNELS + 1] = (s16)sat_r;

    acc_write = next;
}

bool audio_init(void)
{
    if (ready) return true;

    build_sounds();

    if (R_FAILED(audoutInitialize()))
        return false;

    if (R_FAILED(audoutStartAudioOut()))
        return false;

    memset(acc, 0, sizeof(acc));
    acc_read = 0;
    acc_write = 0;

    size_t bytes = (size_t)FRAMES_PER_BUF * CHANNELS * sizeof(s16);
    size_t padded = (bytes + 0xFFF) & ~0xFFF;

    for (int i = 0; i < RING_BUFS; i++) {
        ring_data[i] = memalign(0x1000, padded);

        if (!ring_data[i])
            return false;

        memset(ring_data[i], 0, padded);

        memset(&ring[i], 0, sizeof(AudioOutBuffer));
        ring[i].buffer = ring_data[i];
        ring[i].buffer_size = (u32)padded;
        ring[i].data_size = (u32)bytes;
        ring[i].data_offset = 0;
    }

    ring_next = 0;
    ready = true;

    // сразу наполняем очередь тишиной, чтобы поток не начинался с провала
    for (int i = 0; i < TARGET_QUEUE; i++)
        audoutAppendAudioOutBuffer(&ring[i]);

    ring_next = TARGET_QUEUE % RING_BUFS;

    return true;
}

void audio_exit(void)
{
    if (!ready) return;

    audoutStopAudioOut();
    audoutExit();

    for (int i = 0; i < RING_BUFS; i++) {
        free(ring_data[i]);
        ring_data[i] = NULL;
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

    if (!samples[id] || sample_frames[id] == 0)
        return;

    // микшируем звук в аккумулятор
    for (size_t i = 0; i < sample_frames[id]; i++) {
        acc_push(samples[id][i * CHANNELS + 0], samples[id][i * CHANNELS + 1]);
    }
}

void audio_update(void)
{
    if (!ready)
        return;

    u32 queued = 0;

    if (R_FAILED(audoutGetAudioOutBufferCount(&queued)))
        queued = 0;

    int guard = 0;

    while (queued < TARGET_QUEUE && guard++ < RING_BUFS) {
        s16 *dst = ring_data[ring_next];
        int avail = acc_available();

        for (int i = 0; i < FRAMES_PER_BUF; i++) {
            if (avail > 0) {
                dst[i * CHANNELS + 0] = acc[acc_read * CHANNELS + 0];
                dst[i * CHANNELS + 1] = acc[acc_read * CHANNELS + 1];

                acc[acc_read * CHANNELS + 0] = 0;
                acc[acc_read * CHANNELS + 1] = 0;

                acc_read = (acc_read + 1) % ACC_FRAMES;
                avail--;
            } else {
                dst[i * CHANNELS + 0] = 0;
                dst[i * CHANNELS + 1] = 0;
            }
        }

        ring[ring_next].data_size = (u32)(FRAMES_PER_BUF * CHANNELS * sizeof(s16));
        ring[ring_next].data_offset = 0;

        if (R_FAILED(audoutAppendAudioOutBuffer(&ring[ring_next])))
            break;

        ring_next = (ring_next + 1) % RING_BUFS;
        queued++;
    }
}
