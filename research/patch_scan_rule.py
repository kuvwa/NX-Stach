import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "scanner.c")
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND:\n" + old[:160])
    s = s.replace(old, new, 1)


# если маркер «unlocked…» — первый флаг служебный
rep("""                res.skip = (digits == expected_count + 1) ? 1 : 0;
                res.format = 0;
                res.count = digits;
                res.unlocked = unlocked;
                snprintf(res.note, sizeof(res.note),
                         "Маркер «%s», %d флагов", marker, digits);""",
    """                res.skip = (digits == expected_count + 1) ? 1 : 0;

                {
                    char low[64];
                    size_t k = 0;

                    for (; marker[k] && k < sizeof(low) - 1; k++)
                        low[k] = (char)((marker[k] >= 'A' && marker[k] <= 'Z')
                                        ? marker[k] + 32 : marker[k]);
                    low[k] = '\\0';

                    if (strstr(low, "unlock"))
                        res.skip = 1;
                }

                res.format = 0;
                res.count = digits;
                res.unlocked = unlocked;
                snprintf(res.note, sizeof(res.note),
                         "Маркер «%s», %d флагов", marker, digits);""")

open(p, "w", encoding="utf-8").write(s)
print("ok")
