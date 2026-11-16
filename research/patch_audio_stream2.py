import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

# добавляем состояние тайминга
s = s.replace("""static AudioOutBuffer ring[RING_BUFS];
static s16 *ring_data[RING_BUFS];
static int ring_next = 0;""",
"""static AudioOutBuffer ring[RING_BUFS];
static s16 *ring_data[RING_BUFS];
static int ring_next = 0;

static u64 audio_start_tick = 0;
static u64 audio_produced_ns = 0;

#define BUF_NS ((u64)FRAMES_PER_BUF * 1000000000ULL / SAMPLE_RATE)
#define LEAD_NS 45000000ULL""", 1)

# init: тайминг
s = s.replace("""    ring_next = 0;
    ready = true;

    // сразу наполняем очередь тишиной, чтобы поток не начинался с провала
    for (int i = 0; i < TARGET_QUEUE; i++)
        audoutAppendAudioOutBuffer(&ring[i]);

    ring_next = TARGET_QUEUE % RING_BUFS;

    return true;""",
"""    ring_next = 0;
    audio_produced_ns = 0;
    audio_start_tick = armGetSystemTick();

    ready = true;

    // наполняем очередь тишиной
    for (int i = 0; i < TARGET_QUEUE; i++) {
        if (R_SUCCEEDED(audoutAppendAudioOutBuffer(&ring[i]))) {
            ring_next = (ring_next + 1) % RING_BUFS;
            audio_produced_ns += BUF_NS;
        }
    }

    return true;""", 1)

# update: по времени, без опроса счётчика
start = s.find("void audio_update(void)")
if start < 0:
    raise SystemExit("audio_update not found")

new_update = r'''static bool append_one(void)
{
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
        return false;

    ring_next = (ring_next + 1) % RING_BUFS;
    return true;
}

void audio_update(void)
{
    if (!ready)
        return;

    u64 now = armGetSystemTick();
    u64 elapsed = armTicksToNs(now - audio_start_tick);

    int guard = 0;

    while (audio_produced_ns + BUF_NS < elapsed + LEAD_NS && guard++ < RING_BUFS) {
        if (!append_one())
            break;

        audio_produced_ns += BUF_NS;
    }
}
'''

s = s[:start] + new_update
open(p, "w", encoding="utf-8").write(s)
print("ok")
