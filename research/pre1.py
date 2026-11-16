import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- library: кэш-только + 48 слотов ----------
p = os.path.join(ROOT, "source", "library.c")
s = open(p, encoding="utf-8").read()

s = s.replace("#define CACHE_SLOTS 24", "#define CACHE_SLOTS 48", 1)

if "library_cover_cached" not in s:
    s = s.rstrip() + """

// Только из кэша: ничего не декодирует (безопасно в кадре).
const u32 *library_cover_cached(u64 title_id)
{
    title_id &= TITLE_ID_MASK;

    for (int i = 0; i < CACHE_SLOTS; i++)
        if (covers[i].pixels && covers[i].title_id == title_id)
            return covers[i].pixels;

    return NULL;
}
"""
    open(p, "w", encoding="utf-8").write(s)
    print("library ok")

p = os.path.join(ROOT, "source", "library.h")
s = open(p, encoding="utf-8").read()
if "library_cover_cached" not in s:
    s = s.replace("u32 library_cover_color(u64 title_id);",
                  "u32 library_cover_color(u64 title_id);\nconst u32 *library_cover_cached(u64 title_id);", 1)
    open(p, "w", encoding="utf-8").write(s)
    print("library.h ok")
