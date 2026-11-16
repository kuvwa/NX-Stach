import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

start = s.find("                if ((kDown & HidNpadButton_Y) && achievement_count > 0) {")
end = s.find("                if (kDown & HidNpadButton_B) {", start)

if start < 0 or end < 0 or end <= start:
    raise SystemExit("Y block not found")

BLOCK = r'''                if (kDown & HidNpadButton_Y) {
                    Game *g = &games[view[selected]];

                    GithubConfig cfg;
                    bool gh = github_load_config(&cfg);
                    char up_msg[120] = "локально";

                    // --- 1. каталог достижений из Steam, если его ещё нет ---
                    if (!g->steam_appid[0]) {
                        draw_progress(&fb, face, face_small, g->name,
                                      "Ищем игру в Steam...", 8);

                        SteamSearchResult results[STEAM_MAX_RESULTS];
                        int n = steam_search(g->name, results, STEAM_MAX_RESULTS);

                        if (n <= 0) {
                            snprintf(toast, sizeof(toast),
                                     "В Steam не нашлось: %s", g->name);
                            toast_frames = 200;
                        } else {
                            int appid = results[0].appid;
                            char appid_text[32];
                            snprintf(appid_text, sizeof(appid_text), "%d", appid);

                            draw_progress(&fb, face, face_small, g->name,
                                          "Скачиваем достижения из Steam...", 18);

                            char *buf = malloc(512 * 1024);
                            int len = buf ? steam_fetch_achievements(appid, buf,
                                                                     512 * 1024)
                                          : -1;

                            if (len > 0) {
                                mkdir("sdmc:/switch/NX-Stach", 0777);
                                mkdir("sdmc:/switch/NX-Stach/catalog", 0777);

                                char path[220];
                                snprintf(path, sizeof(path),
                                         "sdmc:/switch/NX-Stach/catalog/%s.json",
                                         appid_text);

                                FILE *f = fopen(path, "wb");
                                if (f) { fwrite(buf, 1, (size_t)len, f); fclose(f); }

                                SteamAchievement tmp[MAX_ACHIEVEMENTS];
                                int cnt = steam_parse_achievements(buf, tmp,
                                                                   MAX_ACHIEVEMENTS);

                                if (cnt > 0) {
                                    char idir[220];
                                    snprintf(idir, sizeof(idir),
                                             "sdmc:/switch/NX-Stach/catalog/icons/%s",
                                             appid_text);
                                    mkdir("sdmc:/switch/NX-Stach/catalog/icons", 0777);
                                    mkdir(idir, 0777);

                                    unsigned char *icon = malloc(256 * 1024);

                                    for (int i = 0; i < cnt; i++) {
                                        char line[120];
                                        snprintf(line, sizeof(line),
                                                 "Иконки %d / %d", i + 1, cnt);

                                        draw_progress(&fb, face, face_small, g->name,
                                                      line, 18 + 50 * i / cnt);

                                        if (!icon) break;

                                        int got = steam_fetch_icon(appid, tmp[i].icon,
                                                                   icon, 256 * 1024);

                                        if (got > 0) {
                                            char ip[340];
                                            snprintf(ip, sizeof(ip),
                                                     "sdmc:/switch/NX-Stach/catalog/icons/%s/%.96s.jpg",
                                                     appid_text, tmp[i].id);

                                            FILE *fi = fopen(ip, "wb");
                                            if (fi) {
                                                fwrite(icon, 1, (size_t)got, fi);
                                                fclose(fi);
                                            }
                                        }
                                    }

                                    free(icon);
                                }

                                if (gh) {
                                    GithubConfig c2 = cfg;
                                    snprintf(c2.path, sizeof(c2.path), "catalog");

                                    char cat_name[48];
                                    snprintf(cat_name, sizeof(cat_name), "%s.json",
                                             appid_text);

                                    github_upload_file(&c2, cat_name, buf,
                                                       up_msg, sizeof(up_msg));
                                }

                                games_json_set_appid(g->title_id, g->name,
                                                     appid_text);
                                snprintf(g->steam_appid, sizeof(g->steam_appid),
                                         "%s", appid_text);

                                achievement_count = load_catalog(g->steam_appid,
                                                                 achievements,
                                                                 MAX_ACHIEVEMENTS);
                                fill_ach_names(achievements, achievement_count);
                                ach_icons_load(g->steam_appid, achievement_count,
                                               achievements);
                            }

                            free(buf);
                        }
                    }

                    // --- 2. ищем, как читать прогресс из сейва ---
                    if (achievement_count > 0) {
                        draw_progress(&fb, face, face_small, g->name,
                                      "Сканируем сейв игры...", 72);

                        ScanResult sr = scan_save_for_achievements(g->title_id,
                                                                   achievement_count,
                                                                   g_ach_names,
                                                                   g_ach_name_count);

                        if (sr.found) {
                            Recipe r;
                            memset(&r, 0, sizeof(r));

                            r.title_id = g->title_id;
                            snprintf(r.steam_appid, sizeof(r.steam_appid), "%s",
                                     g->steam_appid);
                            snprintf(r.file_path, sizeof(r.file_path), "%s",
                                     sr.file_path);
                            snprintf(r.marker, sizeof(r.marker), "%s", sr.marker);
                            r.offset = sr.offset;
                            r.skip = sr.skip;
                            r.format = sr.format;
                            r.count = achievement_count;
                            r.valid = true;

                            recipe_save(&r);

                            flag_count = load_save_flags(g->title_id,
                                                         g->steam_appid, flags,
                                                         MAX_ACHIEVEMENTS);

                            unlocked_count = 0;
                            for (int i = 0; i < achievement_count; i++)
                                if (achievement_unlocked(g->steam_appid, i,
                                                         &achievements[i],
                                                         flags, flag_count))
                                    unlocked_count++;

                            char json[640];
                            snprintf(json, sizeof(json),
                                "{\n"
                                "  \"title_id\": \"%016llX\",\n"
                                "  \"steam_appid\": \"%s\",\n"
                                "  \"file_path\": \"%s\",\n"
                                "  \"marker\": \"%s\",\n"
                                "  \"offset\": %d,\n"
                                "  \"skip\": %d,\n"
                                "  \"format\": %d,\n"
                                "  \"count\": %d,\n"
                                "  \"verified\": true,\n"
                                "  \"source\": \"nx-stach-scanner\",\n"
                                "  \"created\": %llu\n"
                                "}\n",
                                (unsigned long long)g->title_id,
                                g->steam_appid,
                                sr.file_path, sr.marker,
                                sr.offset, sr.skip, sr.format,
                                achievement_count,
                                (unsigned long long)time(NULL));

                            char name[64];
                            snprintf(name, sizeof(name), "%016llX_%s.json",
                                     (unsigned long long)g->title_id,
                                     g->steam_appid);

                            char rmsg[120] = "локально";

                            if (gh)
                                github_upload_file(&cfg, name, json,
                                                   rmsg, sizeof(rmsg));

                            snprintf(toast, sizeof(toast), "%s. Рецепт: %s",
                                     sr.note, rmsg);
                            toast_frames = 300;
                        } else {
                            snprintf(toast, sizeof(toast), "%s", sr.note);
                            toast_frames = 220;
                        }
                    }
                }

'''

s = s[:start] + BLOCK + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
