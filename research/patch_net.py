import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch(path, pairs):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()

    for old, new in pairs:
        if old not in s:
            raise SystemExit("NOT FOUND in %s:\n%s" % (path, old[:160]))
        s = s.replace(old, new, 1)

    open(p, "w", encoding="utf-8").write(s)
    print("patched", path)


patch("source/net.h", [
("const char *net_last_error(void);",
 "const char *net_last_error(void);\nsize_t net_last_body_length(void);"),
]) if "net_last_error" in open(os.path.join(ROOT, "source", "net.h"), encoding="utf-8").read() else None

# net.h может не содержать объявления — добавим в конец
p = os.path.join(ROOT, "source", "net.h")
s = open(p, encoding="utf-8").read()
if "net_last_body_length" not in s:
    s = s.rstrip() + "\n\nsize_t net_last_body_length(void);\n"
    open(p, "w", encoding="utf-8").write(s)
    print("net.h appended")

patch("source/net.c", [
("""static const char *last_error = "NOT_STARTED";""",
 """static const char *last_error = "NOT_STARTED";
static size_t last_body_length = 0;

size_t net_last_body_length(void) { return last_body_length; }"""),

("""    response[body_length] = '\\0';
    success = body_length > 0;""",
 """    response[body_length] = '\\0';
    last_body_length = body_length;
    success = body_length > 0;"""),
])

# strings.h для strncasecmp
p = os.path.join(ROOT, "source", "steamsearch.c")
s = open(p, encoding="utf-8").read()
if "#include <strings.h>" not in s:
    s = s.replace("#include <ctype.h>", "#include <ctype.h>\n#include <strings.h>", 1)
    open(p, "w", encoding="utf-8").write(s)
    print("steamsearch strings.h")
