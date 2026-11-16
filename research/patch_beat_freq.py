import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

s = s.replace("""                beat("tile", i);""",
              """                beat("tile", i);

                if ((i % 3) == 0)
                    beat_flush();""", 1)

s = s.replace("""static int g_beat_tick = 0;

static void beat_flush(void)
{
    if (++g_beat_tick % 12 != 0)
        return;
""", """static void beat_flush(void)
{
""", 1)

open(p, "w", encoding="utf-8").write(s)
print("main ok")
