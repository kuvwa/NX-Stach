import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

MARK = "        /* ------------------------------ отрисовка ------------------------------ */"

if MARK not in s:
    raise SystemExit("render mark not found")

IMPORT = r'''        /* --------------------------- импорт каталога --------------------------- */
        if (import_request && import_title_index >= 0 &&
            import_title_index < game_count && steam_result_count > 0) {
            import_request = 0;
            steam_mode = 0;

            Game *g = &games[import_title_index];
            int appid = steam_results[steam_selected].appid;

            char appid_text[32];
            snprintf(appid_text, sizeof(appid_text), "%d", appid);

            char title_line[220];
            snprintf(title_line, sizeof(title_line), "Импорт: %s",
                     steam_results[steam_selected].name);

            draw_progress(&fb, face, face_small, title_line,
                          "Скачиваем каталог достижений...", 6);

            char *json_buf = malloc(512 * 1024);
            int json_len = json_buf
                ? steam_fetch_achievements(appid, json_buf, 512 * 1024) : -1;

            SteamAchievement tmp[MAX_ACHIEVEMENTS];
            int tmp_count = 0;

            if (json_len > 0) {
                mkdir("sdmc:/switch/NX-Stach", 0777);
                mkdir("sdmc:/switch/NX-Stach/catalog", 0777);
                mkdir("sdmc:/switch/NX-Stach/catalog/icons", 0777);

                char dir[200];
                snprintf(dir, sizeof(dir),
                         "sdmc:/switch/NX-Stach/catalog/icons/%s", appid_text);
                mkdir(dir, 0777);

                char path[220];
                snprintf(path, sizeof(path),
                         "sdmc:/switch/NX-Stach/catalog/%s.json", appid_text);

                FILE *f = fopen(path, "wb");
                if (f) {
                    fwrite(json_buf, 1, (size_t)json_len, f);
                    fclose(f);
                }

                tmp_count = steam_parse_achievements(json_buf, tmp, MAX_ACHIEVEMENTS);
            }

            free(json_buf);

            if (tmp_count > 0) {
                unsigned char *icon = malloc(256 * 1024);

                for (int i = 0; i < tmp_count; i++) {
                    char line[160];
                    snprintf(line, sizeof(line), "Иконки %d / %d", i + 1, tmp_count);

                    draw_progress(&fb, face, face_small, title_line, line,
                                  10 + 85 * i / tmp_count);

                    if (!icon) break;

                    int got = steam_fetch_icon(appid, tmp[i].icon, icon, 256 * 1024);

                    if (got > 0) {
                        char ipath[340];
                        snprintf(ipath, sizeof(ipath),
                                 "sdmc:/switch/NX-Stach/catalog/icons/%s/%.96s.jpg",
                                 appid_text, tmp[i].id);

                        FILE *fi = fopen(ipath, "wb");
                        if (fi) {
                            fwrite(icon, 1, (size_t)got, fi);
                            fclose(fi);
                        }
                    }
                }

                free(icon);

                games_json_set_appid(g->title_id, g->name, appid_text);
                snprintf(g->steam_appid, sizeof(g->steam_appid), "%s", appid_text);

                achievement_count = load_catalog(g->steam_appid, achievements,
                                                 MAX_ACHIEVEMENTS);
                flag_count = load_save_flags(g->steam_appid, flags, MAX_ACHIEVEMENTS);

                unlocked_count = 0;
                for (int i = 0; i < achievement_count; i++)
                    if (achievement_unlocked(g->steam_appid, i, &achievements[i],
                                             flags, flag_count))
                        unlocked_count++;

                ach_icons_load(g->steam_appid, achievement_count, achievements);
                playtime_minutes = game_playtime_minutes(g->title_id);
                build_header_bg(g->title_id);

                list_scroll = list_target = 0.0f;
                only_locked = 0;
                screen = 1;

                snprintf(toast, sizeof(toast), "Готово: %d достижений",
                         achievement_count);
                toast_frames = 180;
            } else {
                snprintf(toast, sizeof(toast), "Не удалось скачать достижения");
                toast_frames = 180;
            }
        }

'''

s = s.replace(MARK, IMPORT + MARK, 1)
open(p, "w", encoding="utf-8").write(s)
print("import block ok")
