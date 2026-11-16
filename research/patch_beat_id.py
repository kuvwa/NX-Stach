import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:160])
    s = s.replace(old, new, 1)


rep("""static const char *g_stage = "init";
static int g_detail = -1;""",
    """static const char *g_stage = "init";
static int g_detail = -1;
static unsigned long long g_detail_id = 0;""")

rep("""    fprintf(f, "stage=%s detail=%d\\n", g_stage, g_detail);""",
    """    fprintf(f, "stage=%s detail=%d id=%016llX\\n", g_stage, g_detail,
            g_detail_id);""")

rep("""                beat("tile", i);

                if ((i % 3) == 0)
                    beat_flush();

                int game_index = view[i];""",
    """                int game_index = view[i];

                g_detail_id = (unsigned long long)games[game_index].title_id;
                beat("tile", i);

                if ((i % 3) == 0 || i == selected)
                    beat_flush();""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
