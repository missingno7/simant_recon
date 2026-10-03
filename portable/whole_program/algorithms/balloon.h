#ifndef SIMANT_WHOLE_BALLOON_ASM_H
#define SIMANT_WHOLE_BALLOON_ASM_H
#include <stdint.h>
/* The destination is the source mask's four-byte width/height prefix followed
 * by two interleaved monochrome planes. Source font images use native Bitmap
 * pointers. Callers supply complete, disjoint live spans without 64K wrap. */
void f_1699_0000(const uint8_t *pattern, int16_t x, int16_t y, char *dest);
void f_1699_0050(const uint8_t *pattern, int16_t x, int16_t y, char *dest, int16_t count);
void f_1699_00A6(const char *image, char *dest, int16_t x, int16_t y);
void f_1699_0110(const char *source, char *dest);
void f_1699_01AA(char *dest, char *source, int16_t count);
#endif
