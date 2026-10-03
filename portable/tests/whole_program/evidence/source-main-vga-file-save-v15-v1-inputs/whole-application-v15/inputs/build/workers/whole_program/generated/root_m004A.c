#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module 004A: map view scrolling (view origin fd_50F6_0508 clamped to
 * 0..fd_50F6_0F36/0F38) and per-plane view centre bookkeeping. */

typedef struct {
    int16_t x;
    int16_t y;
} Point;

int16_t  f_004A_000A(int16_t n);
int16_t  f_004A_0052(int16_t n);
int16_t  f_004A_008A(int16_t n);
int16_t  f_004A_00D2(int16_t n);
int16_t  f_004A_010A(int16_t step);
int16_t  f_004A_0172(int16_t step);
int16_t  f_004A_01E9(int16_t step);
int16_t  f_004A_0253(int16_t step);
void  f_004A_02AD(void);
void  f_004A_038B(void);
void  f_004A_040E(void);

extern int16_t  fd_50F6_0F36;
extern void  f_00F8_0385(void);

int16_t  f_004A_000A(int16_t n)
{
     int16_t moved;

    moved = 0;
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x += n;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x > fd_50F6_0F36) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x = fd_50F6_0F36;
    } else {
        if (n == 1)
            f_00F8_0385();
        moved = 1;
    }
    f_004A_038B();
    return moved;
}

extern void  f_00F8_039D(void);

int16_t  f_004A_0052(int16_t n)
{
     int16_t moved;

    moved = 0;
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x -= n;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x < 0) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x = 0;
    } else {
        if (n == 1)
            f_00F8_039D();
        moved = 1;
    }
    f_004A_038B();
    return moved;
}

extern int16_t  fd_50F6_0F38;
extern void  f_00F8_037D(void);

int16_t  f_004A_008A(int16_t n)
{
     int16_t moved;

    moved = 0;
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y += n;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y > fd_50F6_0F38) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y = fd_50F6_0F38;
    } else {
        if (n == 1)
            f_00F8_037D();
        moved = 1;
    }
    f_004A_040E();
    return moved;
}

extern void  f_00F8_0375(void);

int16_t  f_004A_00D2(int16_t n)
{
     int16_t moved;

    moved = 0;
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y -= n;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y < 0) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y = 0;
    } else {
        if (n == 1)
            f_00F8_0375();
        moved = 1;
    }
    f_004A_040E();
    return moved;
}

extern void  f_00F8_036D(void);
extern void  f_00F8_038D(void);

int16_t  f_004A_010A(int16_t step)
{
     int16_t moved;

    moved = 0;
    if (--(*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y < 0) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y = 0;
    } else {
        if (step == 1)
            f_00F8_036D();
        moved = 1;
    }
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x++;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x > fd_50F6_0F36) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x = fd_50F6_0F36;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

extern void  f_00F8_0365(void);

int16_t  f_004A_0172(int16_t step)
{
     int16_t moved;

    moved = 0;
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y++;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y > fd_50F6_0F38) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y = fd_50F6_0F38;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x++;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x > fd_50F6_0F36) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x = fd_50F6_0F36;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

int16_t  f_004A_01E9(int16_t step)
{
     int16_t moved;

    moved = 0;
    (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y++;
    if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y > fd_50F6_0F38) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y = fd_50F6_0F38;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    if (--(*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x < 0) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x = 0;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

int16_t  f_004A_0253(int16_t step)
{
     int16_t moved;

    moved = 0;
    if (--(*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y < 0) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y = 0;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    if (--(*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x < 0) {
        (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x = 0;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

extern int16_t  fd_50F6_0FB6;
extern int16_t  fd_50F6_0FFA;
extern void  UpdateEdit(void);
extern void  f_0250_0ED2(void);

void  f_004A_02AD(void)
{
    switch (native_state_MapPlane.signed_value) {
    case 1:
        (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    case 2:
        (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    case 3:
        (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}

void  f_004A_038B(void)
{
    switch (native_state_MapPlane.signed_value) {
    case 1:
        (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        break;
    case 2:
        (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        break;
    case 3:
        (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}

void  f_004A_040E(void)
{
    switch (native_state_MapPlane.signed_value) {
    case 1:
        (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    case 2:
        (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    case 3:
        (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}

int16_t ( *g_1832[8])(int16_t step) = {
    f_004A_00D2, f_004A_010A, f_004A_000A, f_004A_0172,
    f_004A_008A, f_004A_01E9, f_004A_0052, f_004A_0253
};

#pragma pack(pop)
