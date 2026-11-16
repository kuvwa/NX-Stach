import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:150])
    s = s.replace(old, new, 1)


# --- тап по достижению: ручная отметка ---
rep("""                } else if (tap_y >= 276 && tap_y <= 332) {""",
    """                } else if (achievement_count > 0 && flag_count <= 0 &&
                           tap_y >= LIST_TOP && tap_y <= LIST_BOTTOM) {
                    Game *g = &games[view[selected]];
                    int rel = tap_y - LIST_TOP + (int)list_scroll;

                    for (int i = 0; i < list_row_count; i++) {
                        ListRow *row = &list_rows[i];

                        if (rel < row->y || rel >= row->y + row->height)
                            continue;

                        if (row->kind != 1)
                            break;

                        const char *id = achievements[row->ach].id;

                        if (save_is_unlocked(g->steam_appid, id)) {
                            save_lock(g->steam_appid, id);
                        } else {
                            save_unlock(g->steam_appid, id);
                            history_mark(g->steam_appid, id,
                                         (u64)time(NULL));
                            history_save();
                        }

                        unlocked_count = 0;
                        for (int k = 0; k < achievement_count; k++)
                            if (achievement_unlocked(g->steam_appid, k,
                                                     &achievements[k],
                                                     flags, flag_count))
                                unlocked_count++;

                        break;
                    }

                    consumed = true;
                } else if (tap_y >= 276 && tap_y <= 332) {""")

# --- подсказка внизу ---
rep("""            char foot[96];""",
    """            char foot[96];""") if False else None

rep("""            set_text_color(140, 145, 155);
            draw_text(face_small, pixels, x + 28, y + h - 16, foot);
            reset_text_color();""",
    """            set_text_color(140, 145, 155);
            draw_text(face_small, pixels, x + 28, y + h - 16, foot);
            reset_text_color();""") if False else None

open(p, "w", encoding="utf-8").write(s)
print("ok")
