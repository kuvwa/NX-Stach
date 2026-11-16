import os

ROOT = r"C:\Users\kuvwa\NX-Stach"
s = open(os.path.join(ROOT, "NX-Stach.nro"), "rb").read()

checks = [
    b'"appid": "219150"',
    b'"appid": "274170"',
    b'"appid": "360740"',
    b'"appid": "557340"',
    b'unlocked_achievements.dat',
    b'trophyFlag=',
    b'achievementUnlocked',
    b'ACH_COMBO_BEGINNER',
]

for c in checks:
    print(("OK   " if c in s else "MISS "), c.decode())

print("icons in nro:", s.count(b"JFIF"))
print("nro MB:", round(len(s) / 1048576, 2))
