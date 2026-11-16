#pragma once

#include <switch.h>
#include <stdbool.h>

typedef enum {
    SFX_NAV = 0,
    SFX_OK,
    SFX_BACK,
    SFX_ERROR,
    SFX_START,
    SFX_TOGGLE,
    SFX_COUNT
} SfxId;

bool audio_init(void);
void audio_exit(void);
void audio_play(SfxId id);
