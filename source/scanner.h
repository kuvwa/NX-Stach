#pragma once

#include <switch.h>
#include <stdbool.h>

typedef struct {
    bool found;
    char file_path[128];
    char marker[64];
    int offset;
    int skip;
    int format;
    int count;
    int unlocked;
    int confidence;     // 0..100
    char note[128];
} ScanResult;

// Сканирует сейв игры и пытается найти флаги достижений.
// expected_count — сколько достижений в каталоге Steam.
ScanResult scan_save_for_achievements(u64 title_id, int expected_count);
