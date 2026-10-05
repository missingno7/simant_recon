#include "source_memory.h"
#include <stdlib.h>

extern SimSourceHandle fd_50F6_3836;
extern SimSourceHandle fd_50F6_3934;
extern SimSourceHandle fd_50F6_3938;
extern SimSourceHandle fd_50F6_385A;
extern SimSourceHandle fd_50F6_385E;
char fd_50F6_3862[100];
extern char *fd_50F6_38B2;
extern void *fd_50F6_3B48;
extern void *fd_50F6_3B4C;
extern SimSourceHandle fd_50F6_3B5C;
extern SimSourceHandle fd_50F6_3B60[45];
SimSourceRect *fd_50F6_3C14;
int16_t *fd_50F6_46A8;
int16_t *fd_50F6_46BC;
extern SimSourceEvent fd_50F6_49FA;
extern SimSourceEvent fd_50F6_4A0A;
extern uint8_t g_8EC0[24];
uint8_t *g_8ED8;

extern SimSourceRect *g_5AAC;
static size_t clip_capacity_bytes;
static int16_t *menu_words;
static size_t menu_capacity_bytes;
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
    /* Canonical bases differ by 20 DOS bytes: ten fixed-width words.
     * This services the actual request; full historical extent is open. */
    if (count > SIZE_MAX / sizeof(*menu_words) - 10u)
        return 0;
    if (!reserve((void **)&menu_words, &menu_capacity_bytes,
                 (count + 10u) * sizeof(*menu_words)))
        return 0;
    fd_50F6_46A8 = menu_words;
    fd_50F6_46BC = menu_words + 10;
    return 1;
}

int16_t sim_source_runtime_reserve_mono_patterns(size_t bytes)
{
    return reserve((void **)&g_8ED8, &mono_capacity_bytes, bytes);
}


