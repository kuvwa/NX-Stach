import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- library.c: жёсткие границы для иконки ---
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

old = """    int width = 0, height = 0, channels = 0;
    stbi_uc *image = stbi_load_from_memory(
        control_buffer->icon, (int)(actual - sizeof(NacpStruct)),
        &width, &height, &channels, 4);"""

new = """    if (actual <= sizeof(NacpStruct) ||
        actual > sizeof(NsApplicationControlData))
        return NULL;

    size_t icon_len = (size_t)(actual - sizeof(NacpStruct));

    if (icon_len > sizeof(control_buffer->icon))
        icon_len = sizeof(control_buffer->icon);

    int width = 0, height = 0, channels = 0;
    stbi_uc *image = stbi_load_from_memory(
        control_buffer->icon, (int)icon_len,
        &width, &height, &channels, 4);"""

if old not in s:
    raise SystemExit("icon block not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("library ok")

# --- main.c: писать файл каждые 3 плитки ---
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

old = """                beat("tile", i);"""
new = """                beat("tile", i);

                if ((i % 3) == 0)
                    beat_flush();"""

if old not in s:
    raise SystemExit("tile beat not found")

s = s.replace(old, new, 1)

# убрать троттлинг у beat_flush (частота теперь задаётся вызывающим)
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
