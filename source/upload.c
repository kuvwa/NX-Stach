#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>

#include "upload.h"
#include "net.h"

#define CONFIG_PATH "sdmc:/switch/NX-Stach/config.json"
#define RESPONSE_SIZE (64 * 1024)

static const char b64chars[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static char *base64_encode(const unsigned char *data, size_t len)
{
    size_t out_len = 4 * ((len + 2) / 3);
    char *out = malloc(out_len + 1);

    if (!out) return NULL;

    size_t i, o = 0;

    for (i = 0; i + 2 < len; i += 3) {
        out[o++] = b64chars[(data[i] >> 2) & 0x3F];
        out[o++] = b64chars[((data[i] & 0x3) << 4) | ((data[i + 1] >> 4) & 0xF)];
        out[o++] = b64chars[((data[i + 1] & 0xF) << 2) | ((data[i + 2] >> 6) & 0x3)];
        out[o++] = b64chars[data[i + 2] & 0x3F];
    }

    if (i < len) {
        out[o++] = b64chars[(data[i] >> 2) & 0x3F];

        if (i + 1 < len) {
            out[o++] = b64chars[((data[i] & 0x3) << 4) | ((data[i + 1] >> 4) & 0xF)];
            out[o++] = b64chars[(data[i + 1] & 0xF) << 2];
            out[o++] = '=';
        } else {
            out[o++] = b64chars[(data[i] & 0x3) << 4];
            out[o++] = '=';
            out[o++] = '=';
        }
    }

    out[o] = '\0';
    return out;
}

bool github_load_config(GithubConfig *cfg)
{
    memset(cfg, 0, sizeof(*cfg));

    json_error_t error;
    json_t *root = json_load_file(CONFIG_PATH, 0, &error);

    if (!root) return false;

    json_t *gh = json_object_get(root, "github");

    if (!json_is_object(gh)) {
        json_decref(root);
        return false;
    }

    const char *v;

    v = json_string_value(json_object_get(gh, "owner"));
    if (v) snprintf(cfg->owner, sizeof(cfg->owner), "%s", v);

    v = json_string_value(json_object_get(gh, "repo"));
    if (v) snprintf(cfg->repo, sizeof(cfg->repo), "%s", v);

    v = json_string_value(json_object_get(gh, "branch"));
    if (v) snprintf(cfg->branch, sizeof(cfg->branch), "%s", v);

    v = json_string_value(json_object_get(gh, "path"));
    if (v) snprintf(cfg->path, sizeof(cfg->path), "%s", v);

    v = json_string_value(json_object_get(gh, "token"));
    if (v) snprintf(cfg->token, sizeof(cfg->token), "%s", v);

    json_decref(root);

    if (!cfg->branch[0]) snprintf(cfg->branch, sizeof(cfg->branch), "main");
    if (!cfg->path[0]) snprintf(cfg->path, sizeof(cfg->path), "recipes");

    cfg->enabled = cfg->owner[0] && cfg->repo[0] && cfg->token[0];
    return cfg->enabled;
}

static bool fetch_sha(const GithubConfig *cfg, const char *name,
                      char *sha, size_t sha_size)
{
    sha[0] = '\0';

    char *response = malloc(RESPONSE_SIZE);
    if (!response) return false;

    char path[512];
    snprintf(path, sizeof(path), "/repos/%s/%s/contents/%s/%s?ref=%s",
             cfg->owner, cfg->repo, cfg->path, name, cfg->branch);

    bool ok = net_https_get("api.github.com", path, response, RESPONSE_SIZE);

    if (ok) {
        json_error_t error;
        json_t *root = json_loads(response, 0, &error);

        if (root) {
            const char *s = json_string_value(json_object_get(root, "sha"));

            if (s) snprintf(sha, sha_size, "%s", s);

            json_decref(root);
        }
    }

    free(response);
    return sha[0] != '\0';
}

bool github_upload_file(const GithubConfig *cfg, const char *name,
                        const char *content, char *message, size_t message_size)
{
    if (!cfg || !cfg->enabled) {
        snprintf(message, message_size, "нет config.json");
        return false;
    }

    char sha[96];
    bool exists = fetch_sha(cfg, name, sha, sizeof(sha));

    char *encoded = base64_encode((const unsigned char *)content, strlen(content));

    if (!encoded) {
        snprintf(message, message_size, "out of memory");
        return false;
    }

    json_t *payload = json_object();

    json_object_set_new(payload, "message",
                        json_string("nx-stach: recipe from scanner"));
    json_object_set_new(payload, "content", json_string(encoded));
    json_object_set_new(payload, "branch", json_string(cfg->branch));

    if (exists)
        json_object_set_new(payload, "sha", json_string(sha));

    char *body = json_dumps(payload, 0);
    json_decref(payload);
    free(encoded);

    if (!body) {
        snprintf(message, message_size, "out of memory");
        return false;
    }

    char path[512];
    snprintf(path, sizeof(path), "/repos/%s/%s/contents/%s/%s",
             cfg->owner, cfg->repo, cfg->path, name);

    char *response = malloc(16 * 1024);
    bool ok = false;

    if (response) {
        ok = net_https_request("api.github.com", "PUT", path,
                               "application/json", body, strlen(body),
                               response, 16 * 1024);

        if (ok) {
            snprintf(message, message_size, exists ? "обновлено в GitHub"
                                                   : "отправлено в GitHub");
        } else {
            snprintf(message, message_size, "GitHub: %s", net_last_error());
        }

        free(response);
    }

    free(body);
    return ok;
}
