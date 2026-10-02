#include "recovered_state.h"
#include <stdint.h>
#include <stddef.h>


int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    int16_t dx;
    int16_t dy;

    dy = y2 - y1;
    dx = x2 - x1;
    if (dx == 0) {
        if (dy == 0)
            return 0;
        if (dy < 0)
            return 1;
        return 5;
    }
    if (dx > 0) {
        if (dy < 0)
            return 2;
        if (dy == 0)
            return 3;
        return 4;
    }
    if (dy > 0)
        return 6;
    if (dy == 0)
        return 7;
    return 8;
}
#include "recovered_state.h"
#include <stdint.h>
#include <stddef.h>


int32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    return (int32_t)(y2 - y1) * (y2 - y1) + (int32_t)(x2 - x1) * (x2 - x1);
}