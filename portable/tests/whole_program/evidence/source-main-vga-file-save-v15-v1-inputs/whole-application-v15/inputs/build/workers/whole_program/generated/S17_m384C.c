#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/menu_globals.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/ui_model/menus/source_record_view.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
extern int32_t f_171C_1C1C(SimHandle handle);
/* Overlay section S17, code frame 384C: menu bar start-up (menu data fix-up, item
 * rectangles, menu colours). */
extern void  f_1B28_006A(int16_t a);
extern void  f_1B73_0046(void);
extern void  f_1B73_0235(void);
extern void  f_1B73_0AA3(void);
extern void  f_1B73_0218(int16_t a, int16_t b);
extern void  f_1FD2_03EB(struct Rect  *r, int16_t ticks);

void  o17_384C_0000(void)
{
    f_1B28_006A(0);
    f_1B73_0046();
    f_1B73_0235();
    f_1B73_0AA3();
    f_1B73_0218(0x10, 0x10);
    f_1FD2_03EB(&g_5A9C, 0xff00);
}

extern SimHandle db_LoadObject(int16_t object, int16_t kind);
extern char ***fd_55B3_6054;
extern void  db_UnhookObject(int16_t object, int16_t kind);
extern int16_t  f_1FD2_0663(int16_t draw);
extern int16_t  *fd_50F6_46BC;
extern int16_t  *fd_50F6_46A8;
void  o17_384C_0184(int16_t x, int16_t len, int16_t id);

/* LIFE-2: draw is a real later call argument. Initializing it before the
 * pointer-fixup loops reproduces the frame and spill homes. Its spelling and
 * original width are unknown; int, unsigned and unsigned char controls match. */
int16_t  o17_384C_0039(int16_t id)
{
    SimHandle h;
    char **r;
    int16_t i;
    int16_t draw;
h = db_LoadObject(id, 6);
    if (h == 0L)
        return 0;
    if (portable_menu_source_record_view_bind_handle(
            &g_menu_view, h, f_171C_1C1C(h)) !=
        PORTABLE_MENU_SOURCE_RECORD_OK) {
        db_UnhookObject(id, 6);
        return 0;
    }
    fd_55B3_6054 = portable_menu_source_record_tables(&g_menu_view);
    db_UnhookObject(id, 6);
    draw = 0;
    /* Native sidecar replaces the DOS offset relocation traversal. */
    f_1FD2_0663(draw);
    for (i = 0, r = fd_55B3_6054[0]; *r; i++, r++)
        o17_384C_0184(fd_50F6_46A8[i], fd_50F6_46BC[i], i - 0x200);
    return 1;
}

extern int16_t  g_5FEA;
extern int16_t  g_5FEC;
extern int16_t  g_5FEE;

void  o17_384C_0143(int16_t a, int16_t b, int16_t c)
{
    g_5FEA = a;
    g_5FEC = b;
    g_5FEE = c;
}

extern int16_t  g_5FE6;
extern int16_t  g_5FE8;

void  o17_384C_0169(int16_t a, int16_t b)
{
    g_5FE6 = a;
    g_5FE8 = b;
}


void  o17_384C_0184(int16_t x, int16_t len, int16_t id)
{
    struct Rect r;

    r.top = 1;
    r.bottom = SIM_GRAPHICS_SOURCE_g_3DDC + 1;
    r.left = x;
    r.right = SIM_GRAPHICS_SOURCE_g_3DDE * len + x;
    f_1FD2_03EB(&r, id);
}

#pragma pack(pop)
