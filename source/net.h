#pragma once

#include <stdbool.h>
#include <stddef.h>

bool net_init(void);
void net_exit(void);
bool net_https_get(const char *host, const char *path,
                   char *response, size_t response_size);
const char *net_last_error(void);

const char *net_last_error(void);
