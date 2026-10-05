#ifndef SIMANT_PLATFORM_SOURCE_MEMORY_H
#define SIMANT_PLATFORM_SOURCE_MEMORY_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef char **SimSourceHandle;
typedef struct SimSourceEvent { int16_t what, message, x4, modifiers, h, v, code, xE; } SimSourceEvent;
typedef struct SimSourceRect { int16_t left, top, right, bottom; } SimSourceRect;
extern SimSourceHandle fd_50F6_3836, fd_50F6_3934, fd_50F6_3938;
extern SimSourceHandle fd_50F6_385A, fd_50F6_385E, fd_50F6_3B5C;
extern char fd_50F6_3862[100];
extern char *fd_50F6_38B2;
extern void *fd_50F6_3B48, *fd_50F6_3B4C;
extern SimSourceHandle fd_50F6_3B60[45];
extern SimSourceRect *fd_50F6_3C14;
extern int16_t *fd_50F6_46A8, *fd_50F6_46BC;
/* Monochrome small-icon handle has no identified native producer. */
extern char **fd_50F6_46D2;
extern SimSourceEvent fd_50F6_49FA, fd_50F6_4A0A;
extern uint8_t g_8EC0[24];
extern uint8_t *g_8ED8;
int16_t sim_source_runtime_reserve_clip_rects(size_t bytes);
int16_t sim_source_runtime_reserve_menu_titles(size_t count);
int16_t sim_source_runtime_reserve_mono_patterns(size_t bytes);
#ifdef __cplusplus
}
#endif
#endif

