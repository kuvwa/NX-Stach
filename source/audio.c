#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <malloc.h>

#include "audio.h"

#define SAMPLE_RATE 48000
#define CHANNELS 2
#define MAX_SECONDS 0.20f
#define MAX_FRAMES ((int)(SAMPLE_RATE * MAX_SECONDS))
#define MAX_BYTES ((size_t)MAX_FRAMES * CHANNELS * sizeof(s16))

static bool ready = false;

static int dbg_last_id = -1;
static int dbg_last_rc = 0;
static int dbg_total = 0;

#define PING_PONG 2

static AudioOutBuffer out_buf[PING_PONG];
static s16 *out_data[PING_PONG];
static int out_index = 0;

static s16 *samples[SFX_COUNT];
static size_t sample_frames[SFX_COUNT];

static void log_line(const char *fmt, ...)
{
    FILE *f = fopen("sdmc:/switch/NX-Stach/audio_log.txt", "a");
    if (!f) return;

    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);

    fclose(f);
}

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
    add_glass(samples[SFX_NAV], &f, 700, 1480.0f, 0.13f, 70.0f);
    sample_frames[SFX_NAV] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_OK], &f, 800, 1175.0f, 0.12f, 40.0f);
    add_glass(samples[SFX_OK], &f, 1200, 1568.0f, 0.12f, 32.0f);
    sample_frames[SFX_OK] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_BACK], &f, 800, 1318.0f, 0.12f, 40.0f);
    add_glass(samples[SFX_BACK], &f, 1000, 988.0f, 0.11f, 34.0f);
    sample_frames[SFX_BACK] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_ERROR], &f, 2200, 392.0f, 0.14f, 14.0f);
    sample_frames[SFX_ERROR] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_START], &f, 900, 880.0f, 0.11f, 26.0f);
    add_glass(samples[SFX_START], &f, 900, 1108.0f, 0.11f, 24.0f);
    add_glass(samples[SFX_START], &f, 1400, 1318.0f, 0.12f, 20.0f);
    sample_frames[SFX_START] = (size_t)f;

    f = 0;
    add_glass(samples[SFX_TOGGLE], &f, 600, 1760.0f, 0.12f, 80.0f);
    add_glass(samples[SFX_TOGGLE], &f, 900, 2093.0f, 0.11f, 55.0f);
    sample_frames[SFX_TOGGLE] = (size_t)f;
}

bool audio_init(void)
{
    if (ready) return true;

    #define DIR_NX "sdmc:/switch/NX-Stach"
    mkdir("sdmc:/switch", 0777);
    mkdir(DIR_NX, 0777);

    build_sounds();

    Result rc = audoutInitialize();

    log_line("init rc=0x%08X rate=%u ch=%u fmt=0x%X\n",
             (unsigned)rc, audoutGetSampleRate(), audoutGetChannelCount(),
             (unsigned)audoutGetPcmFormat());

    if (R_FAILED(rc))
        return false;

    rc = audoutStartAudioOut();

    log_line("start rc=0x%08X\n", (unsigned)rc);

    if (R_FAILED(rc))
        return false;

    u32 buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);

    for (int i = 0; i < PING_PONG; i++) {
        out_data[i] = memalign(0x1000, buffer_size);

        if (!out_data[i])
            return false;

        memset(out_data[i], 0, buffer_size);

        memset(&out_buf[i], 0, sizeof(AudioOutBuffer));
        out_buf[i].next = NULL;
        out_buf[i].buffer = out_data[i];
        out_buf[i].buffer_size = buffer_size;
        out_buf[i].data_size = 0;
        out_buf[i].data_offset = 0;
    }

    out_index = 0;
    ready = true;
    return true;
}

void audio_exit(void)
{
    if (!ready) return;

    audoutStopAudioOut();
    audoutExit();

    for (int i = 0; i < PING_PONG; i++) {
        free(out_data[i]);
        out_data[i] = NULL;
    }

    for (int i = 0; i < SFX_COUNT; i++) {
        free(samples[i]);
        samples[i] = NULL;
    }

    ready = false;
}

// Пинг-понг из двух буферов: пока драйвер играет один, готовим второй.
void audio_play(SfxId id)
{
    if (!ready || id < 0 || id >= SFX_COUNT)
        return;

    if (!samples[id] || sample_frames[id] == 0)
        return;

    size_t bytes = sample_frames[id] * CHANNELS * sizeof(s16);

    if (bytes > MAX_BYTES)
        return;

    // забираем всё, что уже отыграло, чтобы очередь не забивалась
    for (int guard = 0; guard < 8; guard++) {
        AudioOutBuffer *released = NULL;
        u32 released_count = 0;

        if (R_FAILED(audoutGetReleasedAudioOutBuffer(&released, &released_count)) ||
            released_count == 0)
            break;
    }

    int slot = out_index;
    out_index = (out_index + 1) % PING_PONG;

    memcpy(out_data[slot], samples[id], bytes);

    out_buf[slot].next = NULL;
    out_buf[slot].buffer = out_data[slot];
    out_buf[slot].data_size = (u32)bytes;
    out_buf[slot].data_offset = 0;

    Result rc = audoutAppendAudioOutBuffer(&out_buf[slot]);

    dbg_last_id = (int)id;
    dbg_last_rc = (int)rc;
    dbg_total++;
}

void audio_update(void)
{
    // поток не нужен: буферы пинг-понга отдаются сразу
}

void audio_debug(int *last_id, int *last_rc, int *total)
{
    *last_id = dbg_last_id;
    *last_rc = dbg_last_rc;
    *total = dbg_total;
}
