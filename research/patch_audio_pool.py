import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

# заголовок: пул слотов
s = s.replace("""#define SAMPLE_RATE 48000
#define CHANNELS 2""",
"""#define SAMPLE_RATE 48000
#define CHANNELS 2
#define POOL_SLOTS 32""", 1)

s = s.replace("""static AudioOutBuffer out_buffer;
static s16 *out_data = NULL;""",
"""static AudioOutBuffer pool[POOL_SLOTS];
static s16 *pool_data[POOL_SLOTS];
static int pool_next = 0;""", 1)

# init
old_init = """    out_data = memalign(0x1000, (MAX_BYTES + 0xFFF) & ~0xFFF);

    if (!out_data)
        return false;

    memset(&out_buffer, 0, sizeof(AudioOutBuffer));
    out_buffer.buffer = out_data;
    out_buffer.buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
    out_buffer.data_size = 0;
    out_buffer.data_offset = 0;

    ready = true;
    return true;"""

new_init = """    for (int i = 0; i < POOL_SLOTS; i++) {
        pool_data[i] = memalign(0x1000, (MAX_BYTES + 0xFFF) & ~0xFFF);

        if (!pool_data[i])
            return false;

        memset(&pool[i], 0, sizeof(AudioOutBuffer));
        pool[i].buffer = pool_data[i];
        pool[i].buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
        pool[i].data_size = 0;
        pool[i].data_offset = 0;
    }

    pool_next = 0;
    ready = true;
    return true;"""

if old_init not in s:
    raise SystemExit("init not found")

s = s.replace(old_init, new_init, 1)

# exit
old_exit = """    free(out_data);
    out_data = NULL;"""

new_exit = """    for (int i = 0; i < POOL_SLOTS; i++) {
        free(pool_data[i]);
        pool_data[i] = NULL;
    }"""

if old_exit not in s:
    raise SystemExit("exit not found")

s = s.replace(old_exit, new_exit, 1)

# play: round-robin, без отслеживания освобождения
start = s.find("void audio_play(SfxId id)")
if start < 0:
    raise SystemExit("play not found")

new_play = r'''void audio_play(SfxId id)
{
    if (!ready || id < 0 || id >= SFX_COUNT)
        return;

    if (!samples[id] || sample_bytes[id] == 0)
        return;

    if (sample_bytes[id] > MAX_BYTES)
        return;

    // Кольцевой пул: буфер не переиспользуется, пока не пройдёт 32 звука
    // (~1.5 секунды), поэтому звук никогда не перезаписывается на ходу.
    int slot = pool_next;
    pool_next = (pool_next + 1) % POOL_SLOTS;

    memcpy(pool_data[slot], samples[id], sample_bytes[id]);

    pool[slot].data_size = (u32)sample_bytes[id];
    pool[slot].data_offset = 0;

    audoutAppendAudioOutBuffer(&pool[slot]);
}
'''

s = s[:start] + new_play
open(p, "w", encoding="utf-8").write(s)
print("ok")
