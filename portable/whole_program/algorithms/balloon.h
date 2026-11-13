#ifndef SIMANT_WHOLE_BALLOON_ASM_H
#define SIMANT_WHOLE_BALLOON_ASM_H
#include <stdint.h>
/* The destination is the source mask's four-byte width/height prefix followed
 * by two interleaved monochrome planes. Source font images use native Bitmap
 * pointers. Callers supply complete, disjoint live spans without 64K wrap. */
void CopyChar(const uint8_t *pattern, int16_t x, int16_t y, char *dest);
void CopyCharRep(const uint8_t *pattern, int16_t x, int16_t y, char *dest, int16_t count);
void MoveTextToBalloon(const char *image, char *dest, int16_t x, int16_t y);
void MaskMono2Tandy(const char *source, char *dest);
void exchange(char *dest, char *source, int16_t count);
#endif
