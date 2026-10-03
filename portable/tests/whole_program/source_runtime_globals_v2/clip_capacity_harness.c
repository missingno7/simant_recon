#include "source_runtime_globals.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>

SimSourceRect *g_5AAC;

int main(void)
{
    assert(sim_source_runtime_reserve_clip_rects(sizeof(SimSourceRect) * 4));
    fd_50F6_3C14[1].left = 0x1234;
    g_5AAC = &fd_50F6_3C14[1];
    assert(sim_source_runtime_reserve_clip_rects(sizeof(SimSourceRect) * 256));
    assert(g_5AAC == &fd_50F6_3C14[1]);
    assert(g_5AAC->left == 0x1234);
    g_5AAC[255].top = (int16_t)0x8000;
    assert(g_5AAC[255].top == (int16_t)0x8000);
    assert(!sim_source_runtime_reserve_clip_rects(SIZE_MAX));
    assert(g_5AAC == &fd_50F6_3C14[1] && g_5AAC->left == 0x1234);
    return 0;
}
