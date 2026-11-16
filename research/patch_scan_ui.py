import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

SCAN = r'''                if ((kDown & HidNpadButton_Y) && achievement_count > 0) {
                    Game *g = &games[view[selected]];

                    draw_progress(&fb, face, face_small, g->name,
                                  "Сканируем сейв игры...", 20);

                    ScanResult sr = scan_save_for_achievements(g->title_id,
                                                               achievement_count);

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

                        flag_count = load_save_flags(g->title_id, flags,
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
                            sr.offset, sr.skip, sr.format, achievement_count,
                            (unsigned long long)time(NULL));

                        char name[64];
                        snprintf(name, sizeof(name), "%016llX.json",
                                 (unsigned long long)g->title_id);

                        GithubConfig cfg;
                        char msg[160];

                        if (github_load_config(&cfg))
                            github_upload_file(&cfg, name, json, msg, sizeof(msg));
                        else
                            snprintf(msg, sizeof(msg),
                                     "сохранено локально (нет config.json)");

                        snprintf(toast, sizeof(toast), "%s. %s", sr.note, msg);
                        toast_frames = 300;
                    } else {
                        snprintf(toast, sizeof(toast), "%s", sr.note);
                        toast_frames = 200;
                    }
                }

'''

old = """                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }

                if (kDown & HidNpadButton_Down) list_target += ROW_H;
                if (kDown & HidNpadButton_Up) list_target -= ROW_H;"""

new = SCAN + """                if (kDown & HidNpadButton_B) {
                    screen = 0;
                    ach_icons_clear();
                }

                if (kDown & HidNpadButton_Down) list_target += ROW_H;
                if (kDown & HidNpadButton_Up) list_target -= ROW_H;"""

if old not in s:
    raise SystemExit("nav block not found")

s = s.replace(old, new, 1)

# кнопка «Сканировать» в шапке
old2 = """            set_text_color(160, 165, 175);
            draw_text(face_small, pixels, 200, 110, stats);
            reset_text_color();"""

new2 = """            set_text_color(160, 165, 175);
            draw_text(face_small, pixels, 200, 110, stats);
            reset_text_color();

            {
                const char *label = "Сканировать сейв";
                int lw = measure_text(face_small, label);
                int bw = lw + 78;
                int bx = W - 55 - bw;
                int by = 34;

                round_rect(pixels, bx, by, bw, 40, 12, COLOR_PANEL);

                round_rect(pixels, bx + 12, by + 8, 24, 24, 12,
                           RGBA8_MAXALPHA(72, 77, 86));

                set_text_color(236, 241, 250);
                draw_text(face_small, pixels, bx + 18, by + 26, "Y");
                draw_text(face_small, pixels, bx + 46, by + 26, label);
                reset_text_color();
            }"""

if old2 not in s:
    raise SystemExit("stats block not found")

s = s.replace(old2, new2, 1)

# тап по кнопке
old3 = """                } else if (tap_y >= 276 && tap_y <= 332) {"""
new3 = """                } else if (tap_y >= 30 && tap_y <= 78 && tap_x >= 980) {
                    kDown |= HidNpadButton_Y;
                } else if (tap_y >= 276 && tap_y <= 332) {"""

if old3 not in s:
    raise SystemExit("tap block not found")

s = s.replace(old3, new3, 1)

open(p, "w", encoding="utf-8").write(s)
print("ok")
