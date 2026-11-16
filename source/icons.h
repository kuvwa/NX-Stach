#pragma once

#include <switch.h>

#define CONSOLE_ICON_W 256
#define CONSOLE_ICON_H 256

// Инициализация (ns-сервис поднимается один раз).
bool icons_init(void);
void icons_exit(void);

// Возвращает обложку игры 256x256 в RGBA (по 4 байта на пиксель),
// либо NULL, если обложки нет. Указатель живёт до следующей загрузки.
const u8 *icon_get(u64 title_id);

// Имя игры из консоли (NACP). Возвращает false, если не удалось.
bool icon_get_name(u64 title_id, char *out, size_t out_size);
