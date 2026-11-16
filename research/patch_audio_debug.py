import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- audio.h: отладочные данные ---
p = os.path.join(ROOT, "source", "audio.h")
s = open(p, encoding="utf-8").read()
if "audio_debug" not in s:
    s = s.rstrip() + """

// Отладка: последний проигранный звук и код возврата.
void audio_debug(int *last_id, int *last_rc, int *total);
"""
    open(p, "w", encoding="utf-8").write(s)
    print("audio.h ok")

# --- audio.c: учёт ---
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

if "static int dbg_last_id" not in s:
    s = s.replace("static bool ready = false;",
                  "static bool ready = false;\n\nstatic int dbg_last_id = -1;\nstatic int dbg_last_rc = 0;\nstatic int dbg_total = 0;", 1)

    s = s.replace("""    AudioOutBuffer *released = NULL;
    Result rc = audoutPlayBuffer(&out_buf, &released);""",
                  """    AudioOutBuffer *released = NULL;
    Result rc = audoutPlayBuffer(&out_buf, &released);

    dbg_last_id = (int)id;
    dbg_last_rc = (int)rc;
    dbg_total++;""", 1)

    s = s.rstrip() + """

void audio_debug(int *last_id, int *last_rc, int *total)
{
    *last_id = dbg_last_id;
    *last_rc = dbg_last_rc;
    *total = dbg_total;
}
"""
    open(p, "w", encoding="utf-8").write(s)
    print("audio.c ok")

# --- main.c: вывод в углу ---
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

if "audio_debug(" not in s:
    old = """        framebufferEnd(&fb);"""
    new = """        {
            int aid = -1, arc = 0, atot = 0;
            audio_debug(&aid, &arc, &atot);

            char dbg[80];
            snprintf(dbg, sizeof(dbg), "sfx %d rc %d n %d", aid, arc, atot);

            set_text_color(120, 200, 255);
            draw_text(face_small, pixels, 8, 20, dbg);
            reset_text_color();
        }

        framebufferEnd(&fb);"""
    if old in s:
        s = s.replace(old, new, 1)
        open(p, "w", encoding="utf-8").write(s)
        print("main.c ok")
