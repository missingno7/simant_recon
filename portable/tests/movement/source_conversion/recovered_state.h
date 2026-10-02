#ifndef SOURCE_CONVERSION_RECOVERED_STATE_H
#define SOURCE_CONVERSION_RECOVERED_STATE_H

#include <stdint.h>

/* Narrow typed fixture view for the globals read by the extracted body. */
extern int16_t fd_50F6_0A8E;
extern int16_t fd_50F6_0AF8;
extern int16_t fd_50F6_0AD6;
extern int16_t fd_50F6_0AE8;
extern int16_t fd_50F6_0AB6;
extern int16_t fd_50F6_0AC6;
extern int8_t fd_3D57_0000[8];
extern int8_t fd_3D57_0008[8];

/* Identifier-shaped DOS entry aliases for original source helpers. */
int16_t f_0BE8_0B21(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
int32_t f_0BE8_0B83(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
int16_t TileCanBeMovedOn(int16_t plane, int16_t x, int16_t y,
                         int16_t from_plane, int16_t from_x, int16_t from_y,
                         int16_t digging);

#endif
