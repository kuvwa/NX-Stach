import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

old = """            if (entries[i].application_id != title_id)
                continue;

            FsSaveDataAttribute attr;"""

new = """            if (entries[i].application_id != title_id)
                continue;

            matched++;

            if (report)
                fprintf(report, "container save_id=%016llX idx=%u type=%u\\n",
                        (unsigned long long)entries[i].save_data_id,
                        (unsigned)entries[i].save_data_index,
                        (unsigned)entries[i].save_data_type);

            FsSaveDataAttribute attr;"""

if old not in s:
    raise SystemExit("anchor not found")

s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
