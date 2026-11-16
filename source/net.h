#pragma once

#include <stdbool.h>
#include <stddef.h>

bool net_init(void);
void net_exit(void);
bool net_https_get(const char *host, const char *path,
                   char *response, size_t response_size);
const char *net_last_error(void);

const char *net_last_error(void);

// Универсальный запрос (GET/PUT/POST) с телом.
bool net_https_request(const char *host, const char *method, const char *path,
                       const char *content_type, const char *body,
                       size_t body_len, char *response, size_t response_size);
