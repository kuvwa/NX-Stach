#pragma once

#include <switch.h>
#include <stdbool.h>

// Открыть сейв игры (только чтение). Не забудь gamesave_close.
bool gamesave_open(u64 title_id, FsFileSystem *fs);
void gamesave_close(FsFileSystem *fs);

// Прочитать файл целиком (malloc). NULL при ошибке.
u8 *gamesave_read_file(FsFileSystem *fs, const char *path, size_t *out_size);

// Читает флаги по «рецепту».
//   file_path — путь внутри сейва ("/Game/save.dat")
//   marker    — если задан: ищем строку, после неё u32 длина, данные
//   offset    — если marker пуст: смещение в файле
//   skip      — сколько флагов пропустить в начале
//   format    — 0: ASCII '0'/'1' через перевод строки, 1: байты 0/1
int gamesave_read_block(u64 title_id, const char *file_path, const char *marker,
                        int offset, int skip, int format,
                        u8 *flags, int max_flags);

// Формат «по именам»: ищет название достижения и рядом байт 0/1.
// offset — окно поиска после имени.
int gamesave_read_named(u64 title_id, const char *file_path,
                        const char **names, int name_count,
                        int window, u8 *flags, int max_flags);

// Старое поведение (Hotline Miami), оставлено для совместимости.
int gamesave_read_unlocked(u64 title_id, const char *base_path,
                           u8 *flags, int max_flags);

const char *gamesave_last_error(void);

// Диагностика: дерево сейва в sdmc:/switch/NX-Stach/save_tree.txt
void gamesave_dump_tree(u64 title_id);
