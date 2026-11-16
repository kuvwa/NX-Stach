import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:140])
    s = s.replace(old, new, 1)


# 1) стартовая сборка списка
rep("""    for (int i = 0; i < game_count; i++)
        view[view_count++] = i;""",
    """    rebuild_view(view, &view_count, games, game_count, search);""")

# 2) поиск через тап
rep("""                        view_count = 0;
                        selected = 0;
                        grid_scroll = grid_target = 0.0f;

                        for (int i = 0; i < game_count; i++)
                            if (text_contains(games[i].name, search))
                                view[view_count++] = i;""",
    """                        selected = 0;
                        grid_scroll = grid_target = 0.0f;

                        rebuild_view(view, &view_count, games, game_count,
                                     search);""")

# 3) сброс поиска через B
rep("""                view_count = 0;
                for (int i = 0; i < game_count; i++)
                    view[view_count++] = i;""",
    """                rebuild_view(view, &view_count, games, game_count, search);""")

# 4) поиск через Y
rep("""                    view_count = 0;
                    selected = 0;
                    grid_scroll = grid_target = 0.0f;

                    for (int i = 0; i < game_count; i++)
                        if (text_contains(games[i].name, search))
                            view[view_count++] = i;""",
    """                    selected = 0;
                    grid_scroll = grid_target = 0.0f;

                    rebuild_view(view, &view_count, games, game_count, search);""")

# 5) X — закрепить/открепить
rep("""            if (!consumed && screen == 0 && (kDown & HidNpadButton_Y)) {""",
    """            if (!consumed && screen == 0 && (kDown & HidNpadButton_X) &&
                view_count > 0) {
                u64 id = games[view[selected]].title_id;

                pin_toggle(id);
                rebuild_view(view, &view_count, games, game_count, search);

                for (int i = 0; i < view_count; i++)
                    if (games[view[i]].title_id == id) {
                        selected = i;
                        break;
                    }

                snprintf(toast, sizeof(toast),
                         is_pinned(id) ? L("Pinned", "Закреплено")
                                       : L("Unpinned", "Откреплено"));
                toast_frames = 120;

                consumed = true;
            }

            if (!consumed && screen == 0 && (kDown & HidNpadButton_Y)) {""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
