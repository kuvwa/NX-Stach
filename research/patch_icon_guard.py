import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
