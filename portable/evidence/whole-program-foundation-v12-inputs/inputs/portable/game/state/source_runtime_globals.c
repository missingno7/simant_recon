#include "source_runtime_globals.h"
#include <stdlib.h>

SimSourceHandle fd_50F6_3836;
SimSourceHandle fd_50F6_3934;
SimSourceHandle fd_50F6_3938;
SimSourceHandle fd_50F6_385A;
SimSourceHandle fd_50F6_385E;
char fd_50F6_3862[100];
char *fd_50F6_38B2;
void *fd_50F6_3B48;
void *fd_50F6_3B4C;
SimSourceHandle fd_50F6_3B5C;
SimSourceHandle fd_50F6_3B60[45];
SimSourceRect *fd_50F6_3C14;
int16_t *fd_50F6_46A8;
int16_t *fd_50F6_46BC;
char **fd_50F6_46D2;
SimSourceEvent fd_50F6_49FA;
SimSourceEvent fd_50F6_4A0A;
uint8_t g_8EC0[24];
uint8_t *g_8ED8;

extern SimSourceRect *g_5AAC;
static size_t clip_capacity_bytes;
static size_t menu_x_capacity_bytes;
static size_t menu_width_capacity_bytes;
static size_t mono_capacity_bytes;

static int reserve(void **slot, size_t *capacity, size_t need)
{
    void *next;
    if (need <= *capacity)
        return 1;
    next = realloc(*slot, need ? need : 1);
    if (!next)
        return 0;
    *slot = next;
    *capacity = need;
    return 1;
}

int16_t sim_source_runtime_reserve_clip_rects(size_t bytes)
{
    uintptr_t old_base = (uintptr_t)(void *)fd_50F6_3C14;
    uintptr_t current = (uintptr_t)(void *)g_5AAC;
    size_t offset = 0;
    int rebase = fd_50F6_3C14 != NULL && current >= old_base &&
                 current - old_base <= clip_capacity_bytes;
    if (rebase)
        offset = (size_t)(current - old_base);
    if (!reserve((void **)&fd_50F6_3C14, &clip_capacity_bytes, bytes))
        return 0;
    if (rebase)
        g_5AAC = (SimSourceRect *)((uint8_t *)fd_50F6_3C14 + offset);
    return 1;
}

int16_t sim_source_runtime_reserve_menu_titles(size_t count)
{
    if (count > SIZE_MAX / sizeof(*fd_50F6_46A8))
        return 0;
    if (!reserve((void **)&fd_50F6_46A8, &menu_x_capacity_bytes, count * sizeof(*fd_50F6_46A8)))
        return 0;
    if (!reserve((void **)&fd_50F6_46BC, &menu_width_capacity_bytes, count * sizeof(*fd_50F6_46BC)))
        return 0;
    return 1;
}

int16_t sim_source_runtime_reserve_mono_patterns(size_t bytes)
{
    return reserve((void **)&g_8ED8, &mono_capacity_bytes, bytes);
}


