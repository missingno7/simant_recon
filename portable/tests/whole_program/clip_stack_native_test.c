#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/window_source_rects.h"

typedef char **Handle;
Handle g_5742, g_5746, fd_50F6_3B5C;
int16_t g_5756, g_5758;
struct Rect *g_5AAC;
struct Rect fd_50F6_3C14[256];

static Handle tracked[64];
static size_t tracked_count, allocation_count, copy_count;
static int old_header_control;

static void require(int condition, const char *what)
{
    if (!condition) { fprintf(stderr, "%s\n", what); exit(1); }
}

void Punt(char *format, ...)
{
    fprintf(stderr, "Unexpected source Punt: %s\n", format);
    exit(2);
}

static Handle checked_allocate(int32_t size, int16_t flags, char *name)
{
    Handle h = f_171C_1A9E(size, flags, name);
    require(h != NULL, "allocation failed");
    require(f_171C_1C1C(h) == size, "allocated size changed");
    tracked[tracked_count++] = h;
    ++allocation_count;
    return h;
}

static void *checked_copy(void *destination, const void *source, uint16_t size)
{
    uintptr_t dst = (uintptr_t)destination;
    size_t i;
    for (i = 0; i < tracked_count; ++i) {
        int32_t bytes = f_171C_1C1C(tracked[i]);
        uintptr_t start = 0;
        if (bytes > 0) {
            start = (uintptr_t)f_171C_1B84(tracked[i]);
            f_171C_1BBA(tracked[i]);
        }
        if (bytes > 0 && start && dst >= start && dst <= start + (size_t)bytes) {
            if ((size_t)size > start + (size_t)bytes - dst) {
                /* The old header control stops before memcpy or header writes. */
                if (old_header_control) exit(42);
                require(0, "payload exceeds actual handle allocation");
            }
            ++copy_count;
            return memcpy(destination, source, size);
        }
    }
    require(dst == (uintptr_t)fd_50F6_3C14 &&
            size <= sizeof(fd_50F6_3C14), "unregistered copy destination");
    ++copy_count;
    return memcpy(destination, source, size);
}

/* The runner emits these three actual converted source bodies. */
#define f_171C_1A9E checked_allocate
#define _fmemcpy checked_copy
#include "clip_stack_bodies.inc"
#undef _fmemcpy
#undef f_171C_1A9E

int main(int argc, char **argv)
{
    struct Rect original[12][7];
    int rows[12], level, j, round;
    (void)argv;
    old_header_control = argc > 1;
    require(sim_handles_global_configure(1024 * 1024, 128) == SIM_HANDLE_OK,
            "handle manager configuration");
    for (round = 0; round < 4; ++round) {
        for (level = 0; level < 12; ++level) {
            rows[level] = (level + round) % 6 + 1;
            for (j = 0; j < rows[level]; ++j)
                original[level][j] = (struct Rect){
                    (int16_t)(level * 7 + j), (int16_t)(round * 11 + j),
                    (int16_t)(200 - level), (int16_t)(300 - round)};
            original[level][rows[level]] = (struct Rect){0, INT16_MIN, 0, 0};
            /* First negative-control case is nonempty and therefore bounded. */
            g_5AAC = level % 4 == 3 ? NULL : original[level];
            clip_Push();
            require(g_5756 == level + 1, "push depth");
            require(f_171C_1C1C(fd_50F6_3B5C) ==
                (int32_t)(2 * sizeof(Handle) + (level % 4 == 3 ? 0 :
                    (rows[level] + 1) * sizeof(struct Rect))), "native header extent");
        }
        for (level = 11; level >= 0; --level) {
            clip_Pop();
            require(g_5756 == level, "pop depth");
            if (level % 4 == 3)
                require(g_5AAC == NULL, "null clipping state restore");
            else {
                require(g_5AAC == fd_50F6_3C14, "normalized restored payload");
                require(memcmp(g_5AAC, original[level],
                    (rows[level] + 1) * sizeof(struct Rect)) == 0,
                    "restored clip contents");
            }
        }
        f_1E57_0009();
        require(fd_50F6_3B5C == NULL && g_5742 == NULL, "stack cleanup");
    }
    require(allocation_count == 48 && copy_count == 72, "operation counts");
    printf("PASS: 48 pushes, 48 pops, 72 bounded payload copies; header=%zu\n",
           2 * sizeof(Handle));
    return 0;
}
