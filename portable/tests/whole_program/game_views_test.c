#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/state/game_views.h"
#include "portable/whole_program/platform/handles.h"

struct Rect { int16_t left, top, right, bottom; };
static unsigned calls, clips;
static SimHandle expected;
#define require(ok) do { if (!(ok)) { fprintf(stderr, "control failure line %d\n", __LINE__); exit(20); } } while (0)
void clip_Push(void) { require(calls++ == 0); }
void clip_SetWin(int16_t win) { require(calls++ == 1 && win == 0x1900); }
void hanim_RemoveAllAnimObjects(SimHandle h) { require(calls++ == 2 && h == expected); }
void hanim_RenderAnimSet(SimHandle h) { require(calls++ == 3 && h == expected); }
void hanim_RemoveAnimSet(SimHandle h) {
    require(calls++ == 4 && h == expected);
    f_171C_1C0A(h);
}
void clip_Pop(void) { require(calls++ == 5); }
int16_t win_IsWinOpen(int16_t win) { require(win == 0x1902); return 1; }
void win_GetObjRect(int16_t obj, struct Rect *r) {
    if (obj == 0x1902) { r->left = -17; r->top = 101; r->right = 32700; r->bottom = 211; }
    else { require(obj == 0x15); r->left = 13; r->top = -8; r->right = 71; r->bottom = 112; }
}
void EraseYardCursor(void) {
    require(native_game_fd_50F6_10D2.words[0] == -16);
    require(native_game_fd_50F6_10D2.words[1] == 101);
}
void f_1E57_08F5(struct Rect *r) {
    require(r[0].left == -29 && r[0].top == 47 && r[0].right == 640 && r[0].bottom == 350);
    require(r[1].left == 13 && r[1].top == -8 && r[1].right == 71 && r[1].bottom == 112);
    require(r[2].top == INT16_MIN);
    ++clips;
}
#include "game_view_bodies.inc"

int main(void) {
    require(sim_handles_global_configure(65536, 32) == SIM_HANDLE_OK);
    expected = f_171C_1A9E(24, 1, "view state control");
    require(expected != NULL);
    native_game_fd_50F6_10DA = expected;
    win_YardClosed();
    require(calls == 6 && native_game_fd_50F6_10DA == NULL);
    win_YardClosed();
    require(calls == 6);
    native_game_fd_50F6_110C.words[0] = -29;
    native_game_fd_50F6_110C.words[1] = 47;
    native_game_fd_50F6_110C.words[2] = 640;
    native_game_fd_50F6_110C.words[3] = 350;
    f_0250_5058();
    require(clips == 1 && native_game_fd_50F6_1104.words[0] == 13);
    expected = f_171C_1A9E(8, 1, "shared header cell");
    require(expected != NULL);
    require(f_171C_1B84(expected) != NULL);
    native_game_fd_50F6_10CC[0] = f_171C_1BBA(expected);
    require(f_171C_1C1C(native_game_fd_50F6_10CC[0]) == 8);
    f_171C_1C0A(native_game_fd_50F6_10CC[0]);
    native_game_fd_50F6_10CC[0] = NULL;
    puts("PASS: source cleanup order, shared handle identity, rectangle/word aliases and clip sentinel");
    return 0;
}
