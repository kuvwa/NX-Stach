import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:200])
    s = s.replace(old, new, 1)


rep('#include "history.h"', '#include "history.h"\n#include "recipe.h"\n#include "scanner.h"\n#include "upload.h"')

# --- рецепты вместо жёсткой таблицы ---
old_block = s[s.find("typedef struct {\n    const char *appid;\n    u64 title_id;\n    const char *save_path;\n    int flag_offset;\n} SaveSource;"):s.find("static bool achievement_unlocked(")]

new_block = '''static int load_save_flags(u64 title_id, u8 *flags, int max_flags)
{
    Recipe recipe;

    if (!recipe_load(title_id, &recipe))
        return -1;

    return recipe_read_flags(&recipe, flags, max_flags);
}

'''

s = s.replace(old_block, new_block, 1)

rep("""    if (flag_count > 0) {
        int slot = index + save_flag_offset;
        return slot >= 0 && slot < flag_count && flags[slot] != 0;
    }""",
    """    if (flag_count > 0)
        return index >= 0 && index < flag_count && flags[index] != 0;""")

rep("""flag_count = load_save_flags(game->steam_appid, flags,
                                                     MAX_ACHIEVEMENTS);""",
    """flag_count = load_save_flags(game->title_id, flags,
                                                     MAX_ACHIEVEMENTS);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
