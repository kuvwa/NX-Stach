import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

pairs = [
    ("Search...", "Поиск..."),
    ("Search game", "Поиск игры"),
    ("Nothing found on Steam", "В Steam ничего не найдено"),
    ("Nothing found", "Ничего не найдено"),
    ("Achievements not connected", "Достижения не подключены"),
    ("Find this game on Steam to load achievements, icons and descriptions",
     "Найди игру в Steam — подтянем достижения, иконки и описания"),
    ("Import from Steam by name", "Импортировать из Steam по названию"),
    ("Searching Steam...", "Поиск в Steam..."),
    ("Icon %d / %d", "Иконка %d / %d"),
    ("Import: %s", "Импорт: %s"),
    ("Downloading achievements...", "Скачиваем каталог достижений..."),
    ("Loading... %d / %d", "Загрузка... %d / %d"),
    ("Imported: %d achievements", "Импортировано: %d достижений"),
    ("Failed to download achievements", "Не удалось скачать достижения"),
    ("Found on Steam: %d", "Найдено в Steam: %d"),
    ("Achievements: %d / %d   |   Time played: %u h %u m",
     "Достижения: %d / %d   |   Время в игре: %u ч %u м"),
    ("Achievements: %d / %d", "Достижения: %d / %d"),
    ("Achievements unlocked: %d/%d (%d%%)",
     "Получено достижений: %d/%d (%d%%)"),
    ("Locked only", "Только невыполненные"),
    ("UNLOCKED ACHIEVEMENTS", "ПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ"),
    ("LOCKED ACHIEVEMENTS", "НЕПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ"),
    ("Earned %s", "Получено %s"),
    ("(added manually)", "(добавлено вручную)"),
]

for en, ru in pairs:
    old = '"%s"' % en
    new = 'L("%s", "%s")' % (en, ru)
    if old not in s:
        print("MISS:", en)
        continue
    s = s.replace(old, new)

open(p, "w", encoding="utf-8").write(s)
print("strings done")
