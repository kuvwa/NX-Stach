import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "audio.c")
s = open(p, encoding="utf-8").read()

if "void audio_update(void)" not in s:
    s = s.rstrip() + """

void audio_update(void)
{
    // поток не нужен: буферы пинг-понга отдаются сразу
}

void audio_debug(int *last_id, int *last_rc, int *total)
{
    *last_id = dbg_last_id;
    *last_rc = dbg_last_rc;
    *total = dbg_total;
}
"""

open(p, "w", encoding="utf-8").write(s)
print("ok")
