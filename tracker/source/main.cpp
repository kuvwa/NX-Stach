#define TESLA_INIT_IMPL
#include <switch.h>
#include <tesla.hpp>
#include <jansson.h>
#include <cstdio>
#include <cstring>

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
        json_t* idValue = json_object_get(game, "switch_id");
        json_t* nameValue = json_object_get(game, "name");
        json_t* appValue = json_object_get(game, "steam_app_id");

        const char* id = json_string_value(idValue);
        const char* name = json_string_value(nameValue);
        const char* appId = json_string_value(appValue);

        if (id && name && strcmp(id, currentId) == 0) {
            snprintf(gameName, nameSize, "%s", name);
            snprintf(steamAppId, appIdSize, "%s",
                     appId ? appId : "");
            found = true;
            break;
        }
    }

    json_decref(root);
    return found;
}

static void getGameInfo(char* output, size_t size) {
    Result rc = pmdmntInitialize();

    if (R_FAILED(rc)) {
        snprintf(output, size, "pm:dmnt error: 0x%08X",
                 (unsigned)rc);
        return;
    }

    u64 pid = 0;
    u64 programId = 0;

    rc = pmdmntGetApplicationProcessId(&pid);

    if (R_FAILED(rc)) {
        snprintf(output, size, "Process error: 0x%08X",
                 (unsigned)rc);
    } else {
        rc = pmdmntGetProgramId(&programId, pid);

        if (R_FAILED(rc)) {
            snprintf(output, size, "Program ID error: 0x%08X",
                     (unsigned)rc);
        } else {
            char gameName[64] = "Unknown game";
            char steamAppId[32] = "";

            if (findGame(programId, gameName, sizeof(gameName),
                         steamAppId, sizeof(steamAppId))) {
                if (steamAppId[0]) {
                    snprintf(output, size, "%s | Steam: %s",
                             gameName, steamAppId);
                } else {
                    snprintf(output, size, "%s | No Steam AppID",
                             gameName);
                }
            } else {
                snprintf(output, size, "Unknown | ID: %016llX",
                         (unsigned long long)programId);
            }
        }
    }

    pmdmntExit();
}

class TrackerGui : public tsl::Gui {
public:
    tsl::elm::Element* createUI() override {
        char gameInfo[128];
        getGameInfo(gameInfo, sizeof(gameInfo));

        auto* frame = new tsl::elm::OverlayFrame("NX-Stach", "Tracker");
        auto* list = new tsl::elm::List();

        list->addItem(new tsl::elm::ListItem("NX-Stach Tracker"));
        list->addItem(new tsl::elm::ListItem("Overlay initialized"));
        list->addItem(new tsl::elm::ListItem(gameInfo));

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
