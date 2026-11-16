import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)


rep('#include "recipe.h"', '#include "recipe.h"\n#include "steamsearch.h"')
rep("#include <math.h>", "#include <math.h>\n#include <sys/stat.h>")

# состояние
rep("""    int only_locked = 0;""",
    """    int only_locked = 0;

    SteamSearchResult steam_results[STEAM_MAX_RESULTS];
    int steam_result_count = 0;
    int steam_selected = 0;
    int steam_mode = 0;
    int import_request = 0;
    u32 *steam_icons[STEAM_MAX_RESULTS];""")

helpers = r'''static void draw_progress(Framebuffer *fb, FT_Face face, FT_Face face_small,
                          const char *title, const char *line, int percent)
{
    u32 stride;
    u32 *px = (u32 *)framebufferBegin(fb, &stride);
    fb_width = stride / sizeof(u32);

    fill_bg(px, COLOR_BG);

    clip_left = 0;
    clip_right = W;
    clip_top = 0;
    clip_bottom = H;

    draw_text(face, px, 55, 300, title);

    set_text_color(170, 175, 185);
    draw_text(face_small, px, 55, 340, line);
    reset_text_color();

    round_rect(px, 55, 370, 1170, 16, 8, COLOR_TRACK);

    if (percent > 0)
        round_rect(px, 55, 370, 1170 * percent / 100, 16, 8, COLOR_ACCENT);

    framebufferEnd(fb);
}

// маленькая иконка игры из Steam (обложка-капсула, центральный кроп 44x44)
static u32 *steam_fetch_capsule(int appid)
{
    char path[192];
    snprintf(path, sizeof(path),
             "/store_item_assets/steam/apps/%d/capsule_231x87.jpg", appid);

    unsigned char *buf = malloc(256 * 1024);

    if (!buf)
        return NULL;

    u32 *out = NULL;

    if (net_https_get("shared.akamai.steamstatic.com", path,
                      (char *)buf, 256 * 1024)) {
        size_t len = net_last_body_length();
        int w = 0, h = 0, c = 0;

        stbi_uc *img = stbi_load_from_memory(buf, (int)len, &w, &h, &c, 4);

        if (img && w > 0 && h > 0) {
            const int side = 44;
            int crop = h < w ? h : w;
            int ox = (w - crop) / 2;
            int oy = (h - crop) / 2;

            out = malloc((size_t)side * side * sizeof(u32));

            if (out) {
                for (int y = 0; y < side; y++) {
                    int sy = oy + y * crop / side;

                    for (int x = 0; x < side; x++) {
                        int sx = ox + x * crop / side;
                        const stbi_uc *src = img + ((size_t)sy * w + sx) * 4;

                        out[(size_t)y * side + x] =
                            RGBA8_MAXALPHA(src[0], src[1], src[2]);
                    }
                }
            }
        }

        if (img) stbi_image_free(img);
    }

    free(buf);
    return out;
}

'''

rep("/* --------------------------------- main --------------------------------- */",
    helpers + "/* --------------------------------- main --------------------------------- */")

open(p, "w", encoding="utf-8").write(s)
print("ok")
