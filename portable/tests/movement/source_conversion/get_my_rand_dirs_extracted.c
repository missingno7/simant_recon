#include "recovered_state.h"
#include <stdint.h>
#include <stddef.h>



int16_t  o25_3BA4_1686(int16_t  *rot, int16_t  *dir, int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t flag;
    int16_t d;
    int16_t left;
    int16_t best;
    int16_t threshold;
    char ok[8];
    int16_t i;
    int16_t right;
    int16_t nx;
    int16_t ny;
    int16_t dis;

    best = -1;
    threshold = f_0BE8_0B83(x, y, a, b);
    if (threshold > 0) {
        best = -2;
        flag = (fd_50F6_0A8E == 2) ? 1 : 0;
        for (i = 0; i < 8; i++) {
            nx = fd_3D57_0000[i] + x;
            ny = fd_3D57_0008[i] + y;
            if ((nx != fd_50F6_0AB6 || ny != fd_50F6_0AC6)
                && TileCanBeMovedOn(plane, nx, ny, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8, flag)) {
                best = i;
                ok[i] = 1;
            } else
                ok[i] = 0;
        }
        if (best < 0)
            return best;
        best = -1;
        right = left = *dir;
        if (*rot == 0) {
            for (i = 0; i < 8; i++) {
                if (ok[right]) {
                    best = right;
                    *dir = f_0BE8_0B21(x, y, a, b) - 1;
                    *rot = 1;
                    break;
                }
                if (ok[left]) {
                    best = left;
                    *dir = f_0BE8_0B21(x, y, a, b) - 1;
                    *rot = -1;
                    break;
                }
                right = (right + 1) & 7;
                left = (left - 1) & 7;
            }
        } else {
            for (i = 0; i < 8; i++) {
                if (*rot > 0) {
                    if (ok[right]) {
                        d = right;
                        goto found;
                    }
                } else if (ok[left]) {
                    right = left;
                    goto found;
                }
                right = (right + 1) & 7;
                left = (left - 1) & 7;
            }
        }
    }
    return best;
found:
    dis = f_0BE8_0B83(fd_3D57_0000[right] + x, fd_3D57_0008[right] + y, a, b);
    if (dis <= threshold) {
        *dir = f_0BE8_0B21(x, y, a, b) - 1;
        *rot = 0;
    }
    return right;
}