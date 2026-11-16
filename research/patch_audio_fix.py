import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

start = s.find("void audio_play(SfxId id)")
if start < 0:
    raise SystemExit("audio_play not found")

new = r'''static bool slot_free[SFX_COUNT];
static u64 slot_tick[SFX_COUNT];

void audio_play(SfxId id)
{
    if (!ready || id < 0 || id >= SFX_COUNT)
        return;

    if (!samples[id] || sample_bytes[id] == 0)
        return;

    // забираем всё, что уже отыграло
    for (int guard = 0; guard < 32; guard++) {
        AudioOutBuffer *released = NULL;
        u32 released_count = 0;

        if (R_FAILED(audoutGetReleasedAudioOutBuffer(&released, &released_count)) ||
            released_count == 0)
            break;

        for (int i = 0; i < SFX_COUNT; i++) {
            if (released == (AudioOutBuffer *)&slots[i].buffer)
                slot_free[i] = true;
        }
    }

    // страховка: если драйвер не вернул буфер, освобождаем через 0.5 сек
    u64 now = armGetSystemTick();

    for (int i = 0; i < SFX_COUNT; i++) {
        if (!slot_free[i] && armTicksToNs(now - slot_tick[i]) > 500000000ULL) {
            slot_free[i] = true;
        }
    }

    if (!slot_free[id])
        return;

    memcpy(slots[id].data, samples[id], sample_bytes[id]);

    slots[id].buffer.data_size = (u32)sample_bytes[id];
    slots[id].buffer.data_offset = 0;

    if (R_SUCCEEDED(audoutAppendAudioOutBuffer(&slots[id].buffer))) {
        slot_free[id] = false;
        slot_tick[id] = now;
    }
}
'''

s = s[:start] + new
open(p, "w", encoding="utf-8").write(s)
print("ok")
