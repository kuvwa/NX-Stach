#define TESLA_INIT_IMPL
#include <switch.h>
#include <tesla.hpp>
#include <jansson.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cctype>

// Приводит любой id к виду 0100D0E00E51E000 (16 hex, верхний регистр).
static void normalizeId(const char* in, char* out, size_t size) {
    char tmp[64] = {0};
    size_t j = 0;

    if (in) {
        const char* p = in;
        while (*p == ' ') p++;
        if (p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) p += 2;

        for (; *p && j < sizeof(tmp) - 1; p++) {
            if (*p == ' ' || *p == '-' || *p == '_' || *p == '\t') continue;
            tmp[j++] = (char)toupper((unsigned char)*p);
        }
    }

    if (j > 16) {
        memmove(tmp, tmp + (j - 16), 16);
        tmp[16] = 0;
    }

    snprintf(out, size, "%016llX",
             (unsigned long long)strtoull(tmp[0] ? tmp : "0", NULL, 16));
}

static bool findGame(u64 programId, char* gameName, size_t nameSize,
                     char* steamAppId, size_t appIdSize) {
    json_error_t error;
    json_t* root = json_load_file(
        "sdmc:/switch/NX-Stach/games.json", 0, &error
    );

    if (!root)
        return false;

    json_t* games = json_object_get(root, "games");

    if (!json_is_array(games)) {
        json_decref(root);
        return false;
    }

    char currentId[17];
    snprintf(currentId, sizeof(currentId), "%016llX",
             (unsigned long long)programId);

    bool found = false;
    size_t index;
    json_t* game;

    json_array_foreach(games, index, game) {
        const char* id = json_string_value(json_object_get(game, "switch_id"));
        const char* name = json_string_value(json_object_get(game, "name"));
        const char* appId = json_string_value(json_object_get(game, "steam_app_id"));

        char normalized[17];
        normalizeId(id, normalized, sizeof(normalized));

        if (strcmp(normalized, currentId) == 0) {
            snprintf(gameName, nameSize, "%s", name ? name : "Unknown game");
            snprintf(steamAppId, appIdSize, "%s", appId ? appId : "");
            found = true;
            break;
        }
    }

    json_decref(root);
    return found;
}

// Настоящее имя игры берём у консоли, даже если её нет в games.json.
static bool getAppName(u64 programId, char* out, size_t size) {
    static NsApplicationControlData control;
    u64 actual = 0;
    bool ok = false;

    if (R_FAILED(nsInitialize()))
        return false;

    if (R_SUCCEEDED(nsGetApplicationControlData(
            NsApplicationControlSource_Storage, programId,
            &control, sizeof(control), &actual))) {
        NacpLanguageEntry* lang = NULL;

        if (R_SUCCEEDED(nacpGetLanguageEntry(&control.nacp, &lang)) && lang &&
            lang->name[0]) {
            snprintf(out, size, "%s", lang->name);
            ok = true;
        }
    }

    nsExit();
    return ok;
}

static void getGameInfo(char* line1, size_t s1, char* line2, size_t s2) {
    Result rc = pmdmntInitialize();

    if (R_FAILED(rc)) {
        snprintf(line1, s1, "pm:dmnt error: 0x%08X", (unsigned)rc);
        snprintf(line2, s2, "");
        return;
    }

    u64 pid = 0;
    u64 programId = 0;

    rc = pmdmntGetApplicationProcessId(&pid);

    if (R_FAILED(rc)) {
        snprintf(line1, s1, "Game not running");
        snprintf(line2, s2, "Process error: 0x%08X", (unsigned)rc);
        pmdmntExit();
        return;
    }

    rc = pmdmntGetProgramId(&programId, pid);

    if (R_FAILED(rc)) {
        snprintf(line1, s1, "Game not running");
        snprintf(line2, s2, "Program ID error: 0x%08X", (unsigned)rc);
        pmdmntExit();
        return;
    }

    char gameName[128] = "";
    char steamAppId[32] = "";
    char consoleName[128] = "";

    bool inList = findGame(programId, gameName, sizeof(gameName),
                           steamAppId, sizeof(steamAppId));
    bool named = getAppName(programId, consoleName, sizeof(consoleName));

    snprintf(line2, s2, "ID: %016llX", (unsigned long long)programId);

    if (inList) {
        if (steamAppId[0])
            snprintf(line1, s1, "%s | Steam %s", gameName, steamAppId);
        else
            snprintf(line1, s1, "%s | no Steam ID", gameName);
    } else if (named) {
        snprintf(line1, s1, "%s", consoleName);
        snprintf(line2, s2, "ID: %016llX (no Steam ID)",
                 (unsigned long long)programId);
    } else {
        snprintf(line1, s1, "Unknown game");
    }

    pmdmntExit();
}

class TrackerGui : public tsl::Gui {
public:
    tsl::elm::Element* createUI() override {
        char line1[160];
        char line2[160];
        getGameInfo(line1, sizeof(line1), line2, sizeof(line2));

        auto* frame = new tsl::elm::OverlayFrame("NX-Stach", "Tracker");
        auto* list = new tsl::elm::List();

        list->addItem(new tsl::elm::CategoryHeader("Текущая игра"));
        list->addItem(new tsl::elm::ListItem(line1));
        list->addItem(new tsl::elm::ListItem(line2));

        frame->setContent(list);
        return frame;
    }
};

class TrackerOverlay : public tsl::Overlay {
public:
    std::unique_ptr<tsl::Gui> loadInitialGui() override {
        return initially<TrackerGui>();
    }
};

int main(int argc, char* argv[]) {
    return tsl::loop<TrackerOverlay>(argc, argv);
}
