#include <stdio.h>
#include "source/steam.h"

int main(void) {
    const char *json =
        "{\"response\":{\"games\":["
        "{\"appid\":570,\"name\":\"Dota 2\",\"playtime_forever\":120},"
        "{\"appid\":730,\"name\":\"Counter-Strike 2\",\"playtime_forever\":500}"
        "]}}";

    SteamGame games[10];
    int count = steam_parse_games(json, games, 10);

    printf("Найдено игр: %d\n", count);

    for (int i = 0; i < count; i++) {
        printf("%s | %s | %d минут\n",
               games[i].appid, games[i].name, games[i].playtime);
    }

    return 0;
}
