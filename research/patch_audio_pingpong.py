import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

# два буфера вместо одного
s = s.replace("""static AudioOutBuffer out_buf;
static s16 *out_data = NULL;""",
"""#define PING_PONG 2

static AudioOutBuffer out_buf[PING_PONG];
static s16 *out_data[PING_PONG];
static int out_index = 0;""", 1)

# init
old_init = """    u32 buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
    out_data = memalign(0x1000, buffer_size);

    if (!out_data)
        return false;

    memset(out_data, 0, buffer_size);

    memset(&out_buf, 0, sizeof(out_buf));
    out_buf.next = NULL;
    out_buf.buffer = out_data;
    out_buf.buffer_size = buffer_size;
    out_buf.data_size = 0;
    out_buf.data_offset = 0;

    ready = true;
    return true;"""

new_init = """    u32 buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);

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
    return true;"""

if old_init not in s:
    raise SystemExit("init block not found")

s = s.replace(old_init, new_init, 1)

# exit
old_exit = """    free(out_data);
    out_data = NULL;"""
new_exit = """    for (int i = 0; i < PING_PONG; i++) {
        free(out_data[i]);
        out_data[i] = NULL;
    }"""

if old_exit not in s:
    raise SystemExit("exit block not found")

s = s.replace(old_exit, new_exit, 1)

# play
start = s.find("// Ровно как в примере devkitPro playtone")
if start < 0:
    raise SystemExit("play comment not found")

new_play = r'''// Пинг-понг из двух буферов: пока драйвер играет один, готовим второй.
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
'''

s = s[:start] + new_play
open(p, "w", encoding="utf-8").write(s)
print("ok")
