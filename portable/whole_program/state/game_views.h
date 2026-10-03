#ifndef SIMANT_NATIVE_GAME_VIEWS_H
#define SIMANT_NATIVE_GAME_VIEWS_H
#include <stdint.h>

typedef union {
    int16_t words[4];
    uint8_t raw[8];
} SimGameRectStorage;

/* Source S16 names 10CC as Handle[] and uses only element zero, while 00BA
 * assigns the same cell as one Handle. This native one-cell array preserves
 * both source views. All six source handles are runtime initialized. */
extern char **native_game_fd_50F6_10CC[1];
extern char **native_game_fd_50F6_10DA;
extern char **native_game_fd_50F6_10E2;
extern char **native_game_fd_50F6_10E6;
extern char **native_game_fd_50F6_10EA;
extern char **native_game_fd_50F6_10EE;
extern SimGameRectStorage native_game_fd_50F6_10D2;
extern SimGameRectStorage native_game_fd_50F6_1104;
extern SimGameRectStorage native_game_fd_50F6_110C;
_Static_assert(sizeof(SimGameRectStorage) == 8, "source rectangle size");
#endif
