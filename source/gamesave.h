#pragma once

#include <switch.h>
#include <stdbool.h>

// Читает unlocked_achievements.dat из сейва игры (только чтение, оригинал не меняется).
// title_id  — Title ID игры на Switch (0x0100D0E00E51E000)
// base_path — путь к папке сейва внутри контейнера ("/HotlineMiami")
// flags     — массив, куда пишутся 0/1
// Возвращает количество флагов или -1 при ошибке.
int gamesave_read_unlocked(u64 title_id, const char *base_path,
                           u8 *flags, int max_flags);

const char *gamesave_last_error(void);

// Диагностика: пишет дерево сейва в sdmc:/switch/NX-Stach/save_tree.txt
void gamesave_dump_tree(u64 title_id);
