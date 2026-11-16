import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

# ---------- один буфер, синхронное проигрывание ----------
start = s.find("static SfxSlot slots[SFX_COUNT];")
if start < 0:
    raise SystemExit("slots decl not found")

s = s.replace("static SfxSlot slots[SFX_COUNT];\nstatic bool slot_free[SFX_COUNT];\nstatic u64 slot_tick[SFX_COUNT];",
              "static AudioOutBuffer out_buffer;\nstatic s16 *out_data = NULL;", 1)

# init
old_init = """    for (int i = 0; i < SFX_COUNT; i++) {
        slots[i].data = memalign(0x1000, MAX_BYTES);
        if (!slots[i].data) return false;

        memset(&slots[i].buffer, 0, sizeof(AudioOutBuffer));
        slots[i].buffer.buffer = slots[i].data;
        slots[i].buffer.buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
    }

    for (int i = 0; i < SFX_COUNT; i++) {
        slot_free[i] = true;
        slot_tick[i] = 0;
    }

    ready = true;
    return true;"""

new_init = """    out_data = memalign(0x1000, (MAX_BYTES + 0xFFF) & ~0xFFF);

    if (!out_data)
        return false;

    memset(&out_buffer, 0, sizeof(AudioOutBuffer));
    out_buffer.buffer = out_data;
    out_buffer.buffer_size = (u32)((MAX_BYTES + 0xFFF) & ~0xFFF);
    out_buffer.data_size = 0;
    out_buffer.data_offset = 0;

    ready = true;
    return true;"""

if old_init not in s:
    raise SystemExit("init block not found")

s = s.replace(old_init, new_init, 1)

# exit
old_exit = """    for (int i = 0; i < SFX_COUNT; i++) {
        free(slots[i].data);
        slots[i].data = NULL;
    }"""
new_exit = """    free(out_data);
    out_data = NULL;"""

if old_exit not in s:
    raise SystemExit("exit block not found")

s = s.replace(old_exit, new_exit, 1)

# play
start = s.find("void audio_play(SfxId id)")
if start < 0:
    raise SystemExit("play not found")

new_play = r'''void audio_play(SfxId id)
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
'''

s = s[:start] + new_play
open(p, "w", encoding="utf-8").write(s)
print("ok")
