#include "unsupported_video_profiles.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static _Noreturn void unsupported_video_profile_entry(const char *symbol)
{
    (void)fprintf(stderr, "unsupported native video profile entry: %s\n", symbol);
    (void)fflush(stderr);
    _Exit(70);
}

#define REJECT_NOARGS(symbol) \
    void symbol(void) { unsupported_video_profile_entry(#symbol); }

REJECT_NOARGS(o01_3126_0000)
REJECT_NOARGS(o01_3126_0068)
REJECT_NOARGS(o01_3126_007D)
REJECT_NOARGS(o01_3126_010A)
void o01_3126_1343(int16_t x, int16_t y, char *tile, char *life, int16_t n)
{
    (void)x; (void)y; (void)tile; (void)life; (void)n;
    unsupported_video_profile_entry("o01_3126_1343");
}
void o01_3126_14B6(char *tile, char *life, int16_t n)
{
    (void)tile; (void)life; (void)n;
    unsupported_video_profile_entry("o01_3126_14B6");
}

REJECT_NOARGS(o01_328E_000A)
REJECT_NOARGS(o01_328E_009D)
void o01_328E_012C(char *src, char *dst, int16_t y)
{
    (void)src; (void)dst; (void)y;
    unsupported_video_profile_entry("o01_328E_012C");
}
void o01_328E_01D5(char *src, char *dst, int16_t y)
{
    (void)src; (void)dst; (void)y;
    unsupported_video_profile_entry("o01_328E_01D5");
}

REJECT_NOARGS(o01_32B5_000E)
void o01_32B5_000F(char *image, char *buffer, int16_t shift, int16_t flag)
{
    (void)image; (void)buffer; (void)shift; (void)flag;
    unsupported_video_profile_entry("o01_32B5_000F");
}
REJECT_NOARGS(o01_32B5_00AA)
REJECT_NOARGS(o01_32B5_0152)
REJECT_NOARGS(o01_32B5_024F)

REJECT_NOARGS(o02_3126_0000)
REJECT_NOARGS(o03_3126_0140)

REJECT_NOARGS(o03_3253_0008)
void o03_3253_002F(char *src, char *dst, int16_t mult)
{
    (void)src; (void)dst; (void)mult;
    unsupported_video_profile_entry("o03_3253_002F");
}

REJECT_NOARGS(o03_3258_040C)
void o03_3258_040D(char *image, char *buffer, int16_t shift, int16_t flag)
{
    (void)image; (void)buffer; (void)shift; (void)flag;
    unsupported_video_profile_entry("o03_3258_040D");
}
REJECT_NOARGS(o03_3258_04CE)
REJECT_NOARGS(o03_3258_05A7)
void o03_3258_0690(int16_t x, int16_t y, char *tile, char *life, int16_t mask)
{
    (void)x; (void)y; (void)tile; (void)life; (void)mask;
    unsupported_video_profile_entry("o03_3258_0690");
}
void o03_3258_0F04(char *tile, char *life, int16_t mask)
{
    (void)tile; (void)life; (void)mask;
    unsupported_video_profile_entry("o03_3258_0F04");
}
REJECT_NOARGS(o03_3258_175F)

#undef REJECT_NOARGS
