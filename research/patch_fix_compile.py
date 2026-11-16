import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- net_last_body_length обратно ---
p = os.path.join(ROOT, "source", "net.h")
s = open(p, encoding="utf-8").read()
if "net_last_body_length" not in s:
    s = s.rstrip() + "\n\nsize_t net_last_body_length(void);\n"
    open(p, "w", encoding="utf-8").write(s)
    print("net.h ok")

p = os.path.join(ROOT, "source", "net.c")
s = open(p, encoding="utf-8").read()
if "net_last_body_length" not in s:
    s = s.replace('static const char *last_error = "NOT_STARTED";',
                  'static const char *last_error = "NOT_STARTED";\n'
                  'static size_t last_body_length = 0;\n\n'
                  'size_t net_last_body_length(void) { return last_body_length; }', 1)
    s = s.replace("    response[body_length] = '\\0';\n    success = body_length > 0;",
                  "    response[body_length] = '\\0';\n    last_body_length = body_length;\n    success = body_length > 0;", 1)
    open(p, "w", encoding="utf-8").write(s)
    print("net.c ok")

# --- scanner вызов в main ---
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()
s = s.replace("""                    ScanResult sr = scan_save_for_achievements(g->title_id,
                                                               achievement_count);""",
              """                    ScanResult sr = scan_save_for_achievements(g->title_id,
                                                               achievement_count,
                                                               g_ach_names,
                                                               g_ach_name_count);""", 1)
open(p, "w", encoding="utf-8").write(s)
print("main ok")
