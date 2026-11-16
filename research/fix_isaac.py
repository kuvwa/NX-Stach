import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


# 1) чёрный список обложек (у этих игр битый образ-иконка)
rep("const u32 *library_cover(u64 title_id) {",
    """static bool cover_blacklisted(u64 title_id)
{
    static const u64 bad[] = {
        0x010021C000B6A000ULL,   // The Binding of Isaac: Afterbirth+
    };

    for (unsigned i = 0; i < sizeof(bad) / sizeof(bad[0]); i++)
        if (bad[i] == title_id)
            return true;

    return false;
}

const u32 *library_cover(u64 title_id) {
    if (cover_blacklisted(title_id & TITLE_ID_MASK))
        return NULL;""")

# 2) жёсткие границы длины JPEG
rep("""    int width = 0, height = 0, channels = 0;

    stbi_uc *image = stbi_load_from_memory(
        control_buffer->icon, (int)(actual - sizeof(NacpStruct)),
        &width, &height, &channels, 4);""",
    """    if (actual <= sizeof(NacpStruct) ||
        actual > sizeof(NsApplicationControlData))
        return NULL;

    size_t icon_len = (size_t)(actual - sizeof(NacpStruct));

    if (icon_len > sizeof(control_buffer->icon))
        icon_len = sizeof(control_buffer->icon);

    int width = 0, height = 0, channels = 0;

    stbi_uc *image = stbi_load_from_memory(
        control_buffer->icon, (int)icon_len,
        &width, &height, &channels, 4);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
