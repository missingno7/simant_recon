#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module 15D9: centred ribbon text and the ribbon/yard message setter (Win16 EditMessage). */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t x;
    int16_t y;
};

extern void  f_24AB_02AD(int16_t font);
extern struct Pt  win_StringSize(char  *text);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);
extern void  clip_SubExclude(struct Rect  *rect);

void  f_15D9_0006(char  *text, struct Rect  *r, int16_t y)
{
    struct Rect rc;
    struct Pt size;

    f_24AB_02AD(SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140 ? 0 : 2);
    size = win_StringSize(text);
    rc.top = y;
    rc.left = (r->right - size.x + r->left) / 2;
    rc.right = rc.left + size.x;
    rc.bottom = y + size.y;
    f_24AB_038D(rc.left, y, text);
    clip_SubExclude(&rc);
    f_24AB_02AD(0);
}

extern int16_t  fd_3D57_07A8[];
extern char  *  g_19C6;
extern int32_t  g_19CA;
extern int32_t  TickCount(void);
extern int16_t  g_19CE;
extern int32_t  fd_55B3_299E;
extern char  *  fd_55B3_299A;
extern int16_t  fd_55B3_29A2;

void  EditMessage(char  *message, int32_t duration, int16_t mode)
{
    if (mode == 0 && (fd_3D57_07A8[4] == 0 || g_19C6 != 0L)) {
        if (message != 0L || g_19CA != 0x7fffffffL)
            return;
    }
    if (duration >= 0L)
        g_19CA = TickCount() + (duration * 3L) / 2L;
    else
        g_19CA = 0x7fffffffL;
    if (message != g_19C6) {
        g_19C6 = message;
        g_19CE = 1;
    }
    if (duration >= 0L)
        fd_55B3_299E = TickCount() + (duration * 3L) / 2L;
    else
        fd_55B3_299E = 0x7fffffffL;
    if (message != fd_55B3_299A) {
        fd_55B3_299A = message;
        fd_55B3_29A2 = 1;
    }
}

#pragma pack(pop)
