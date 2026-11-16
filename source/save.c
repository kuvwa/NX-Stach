#include <switch.h>
#include <jansson.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>

#include "save.h"

#define SAVE_DIR "sdmc:/switch/NX-Stach"
#define SAVE_FILE SAVE_DIR "/progress.json"
#define TEMP_FILE SAVE_DIR "/progress.tmp"
#define BACKUP_FILE SAVE_DIR "/progress.bak"

static json_t *root = NULL;
static bool mounted = false;
static char status_text[128] = "Not initialized";

const char *save_status(void)
{
    return status_text;
}

bool save_init(void)
{
    if (!fsdevGetDeviceFileSystem("sdmc")) {
        Result rc = fsdevMountSdmc();

        if (R_FAILED(rc)) {
            snprintf(status_text, sizeof(status_text),
                     "SD mount failed: 0x%08X", (unsigned int)rc);
            return false;
        }

        mounted = true;
    }

    if (mkdir("sdmc:/switch", 0777) != 0 && errno != EEXIST) {
        snprintf(status_text, sizeof(status_text),
                 "Create switch folder failed: %d", errno);
        return false;
    }

    if (mkdir(SAVE_DIR, 0777) != 0 && errno != EEXIST) {
        snprintf(status_text, sizeof(status_text),
                 "Create NX-Stach folder failed: %d", errno);
        return false;
    }

    FILE *file = fopen(SAVE_FILE, "r");

    if (file) {
        fclose(file);
        root = json_load_file(SAVE_FILE, 0, NULL);

        if (!root) {
            snprintf(status_text, sizeof(status_text),
                     "JSON file is invalid");
            return false;
        }
    } else {
        if (errno != ENOENT) {
            snprintf(status_text, sizeof(status_text),
                     "Open save failed: %d", errno);
            return false;
        }

        root = json_object();

        if (!root) {
            snprintf(status_text, sizeof(status_text),
                     "JSON allocation failed");
            return false;
        }

        json_object_set_new(root, "games", json_object());
    }

    if (!json_is_object(json_object_get(root, "games"))) {
        snprintf(status_text, sizeof(status_text),
                 "Invalid games data");
        return false;
    }

    snprintf(status_text, sizeof(status_text), "SD initialized OK");
    return true;
}

bool save_is_unlocked(const char *appid, const char *achievement_id)
{
    if (!root || !appid || !achievement_id)
        return false;

    json_t *games = json_object_get(root, "games");
    json_t *game = json_object_get(games, appid);
    json_t *achievements = json_object_get(game, "achievements");
    json_t *achievement = json_object_get(achievements, achievement_id);

    return json_is_true(achievement);
}

bool save_unlock(const char *appid, const char *achievement_id)
{
    if (!root || !appid || !achievement_id) {
        snprintf(status_text, sizeof(status_text), "Save not initialized");
        return false;
    }

    json_t *games = json_object_get(root, "games");
    json_t *game = json_object_get(games, appid);

    if (!game) {
        game = json_object();
        if (!game || json_object_set_new(games, appid, game) != 0) {
            snprintf(status_text, sizeof(status_text), "Create game failed");
            return false;
        }
    }

    json_t *achievements = json_object_get(game, "achievements");

    if (!achievements) {
        achievements = json_object();
        if (!achievements ||
            json_object_set_new(game, "achievements", achievements) != 0) {
            snprintf(status_text, sizeof(status_text),
                     "Create achievements failed");
            return false;
        }
    }

    if (json_object_set_new(achievements, achievement_id, json_true()) != 0) {
        snprintf(status_text, sizeof(status_text), "Set achievement failed");
        return false;
    }

    if (json_dump_file(root, TEMP_FILE, JSON_INDENT(2)) != 0) {
        snprintf(status_text, sizeof(status_text),
                 "Write JSON failed: %d", errno);
        return false;
    }

    remove(BACKUP_FILE);

    bool had_previous = false;

    if (rename(SAVE_FILE, BACKUP_FILE) == 0) {
        had_previous = true;
    } else if (errno != ENOENT) {
        snprintf(status_text, sizeof(status_text),
                 "Backup save failed: %d", errno);
        return false;
    }

    if (rename(TEMP_FILE, SAVE_FILE) != 0) {
        int err = errno;

        if (had_previous)
            rename(BACKUP_FILE, SAVE_FILE);

        snprintf(status_text, sizeof(status_text),
                 "Rename save failed: %d", err);
        return false;
    }

    Result rc = fsdevCommitDevice("sdmc");

    if (R_FAILED(rc)) {
        snprintf(status_text, sizeof(status_text),
                 "SD commit failed: 0x%08X", (unsigned int)rc);
        return false;
    }

    snprintf(status_text, sizeof(status_text), "Achievement saved OK");
    return true;
}

void save_exit(void)
{
    if (root) {
        json_decref(root);
        root = NULL;
    }

    if (mounted) {
        fsdevUnmountDevice("sdmc");
        mounted = false;
    }
}
