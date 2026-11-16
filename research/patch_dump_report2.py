import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "gamesave.c")
s = open(p, encoding="utf-8").read()

bad = """            if (entries[i].application_id != title_id)
                continue;

            matched++;

            if (report)
                fprintf(report, "container app=%016llX save_id=%016llX idx=%u type=%u\\n",
                        (unsigned long long)entries[i].application_id,
                        (unsigned long long)entries[i].save_data_id,
                        (unsigned)entries[i].save_data_index,
                        (unsigned)entries[i].save_data_type);

            *space = (FsSaveDataSpaceId)entries[i].save_data_space_id;"""

good = """            if (entries[i].application_id != title_id)
                continue;

            *space = (FsSaveDataSpaceId)entries[i].save_data_space_id;"""

if bad not in s:
    raise SystemExit("damaged block not found")

s = s.replace(bad, good, 1)

open(p, "w", encoding="utf-8").write(s)
print("fixed")
