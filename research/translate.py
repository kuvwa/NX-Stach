import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "main.c")
s = open(p, encoding="utf-8").read()

pairs = [
    ('"Поиск игры"', '"Search game"'),
    ('"ПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ"', '"UNLOCKED ACHIEVEMENTS"'),
    ('"НЕПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ"', '"LOCKED ACHIEVEMENTS"'),
    ('"Поиск в Steam..."', '"Searching Steam..."'),
    ('"Иконка %d / %d"', '"Icon %d / %d"'),
    ('"В Steam ничего не найдено"', '"Nothing found on Steam"'),
    ('"Импорт: %s"', '"Import: %s"'),
    ('"Скачиваем каталог достижений..."', '"Downloading achievements..."'),
    ('"Загрузка... %d / %d"', '"Loading... %d / %d"'),
    ('"Импортировано: %d достижений"', '"Imported: %d achievements"'),
    ('"Не удалось скачать достижения"', '"Failed to download achievements"'),
    ('"Поиск..."', '"Search..."'),
    ('"Ничего не найдено"', '"Nothing found"'),
    ('"Достижения не подключены"', '"Achievements not connected"'),
    ('"Найди игру в Steam — подтянем достижения, иконки и описания"',
     '"Find this game on Steam to load achievements, icons and descriptions"'),
    ('"Импортировать из Steam по названию"', '"Import from Steam by name"'),
    ('"Получено %s"', '"Earned %s"'),
    ('"Достижения: %d / %d   |   Время в игре: %u ч %u м"',
     '"Achievements: %d / %d   |   Time played: %u h %u m"'),
    ('"Достижения: %d / %d"', '"Achievements: %d / %d"'),
    ('"Получено достижений: %d/%d (%d%%)"',
     '"Achievements unlocked: %d/%d (%d%%)"'),
    ('"Только невыполненные"', '"Locked only"'),
    ('"Найдено в Steam: %d"', '"Found on Steam: %d"'),
]

for old, new in pairs:
    if old not in s:
        print("MISS:", old)
        continue
    s = s.replace(old, new)

open(p, "w", encoding="utf-8").write(s)
print("done")
