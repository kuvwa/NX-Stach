#pragma once

#include <switch.h>
#include <stdbool.h>
#include <stddef.h>

typedef struct {
    bool enabled;
    char owner[64];
    char repo[64];
    char branch[32];
    char path[64];
    char token[192];
} GithubConfig;

// Читает sdmc:/switch/NX-Stach/config.json
bool github_load_config(GithubConfig *cfg);

// Создаёт или обновляет файл в репозитории.
// name — имя файла (например "0100D0E00E51E000.json"),
// content — содержимое (текст).
bool github_upload_file(const GithubConfig *cfg, const char *name,
                        const char *content, char *message, size_t message_size);
