#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include <ctype.h>
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Overlay section S20, code frame 39C7: display driver font loaders and empty hooks. */

void  o20_39C7_0000(void)
{
}

void  o20_39C7_0001(void)
{
}

void  o20_39C7_0002(void)
{
}

void  o20_39C7_0003(void)
{
}

void  o20_39C7_0004(void)
{
}

void  o20_39C7_0005(void)
{
}

void  o20_39C7_0006(void)
{
}

void  o20_39C7_0007(void)
{
}

extern char  *  *  db_LoadObject(int16_t object, int16_t kind);
extern char  *  g_3DA8;
extern char  *  g_3DA4;
extern void  db_UnhookObject(int16_t object, int16_t kind);

void  o20_39C7_0008(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}
extern void  Punt(char  *fmt, ...);

void  o20_39C7_0069(void)
{
    char  *  *p;
    char  *  *q;

    p = db_LoadObject(0x14, 9);
    g_3DA4 = *p;
    q = db_LoadObject(0x13, 9);
    g_3DA8 = *q;
    if (q == 0 || p == 0) {
        dos_printf("Could not find fonts");
        Punt("Could not find fonts!");
    }
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x13, 9);
}

void  o20_39C7_00FF(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

void  o20_39C7_0160(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern void  WinPrintf(char  *fmt, ...);

void  o20_39C7_01C1(void)
{
    char  *  *p;

    p = db_LoadObject(0x13, 9);
    if (p) {
        WinPrintf("\nFont loaded!");
        g_3DA8 = *p;
        db_UnhookObject(0x13, 9);
    }
}

void  o20_39C7_0211(void)
{
}

void  o20_39C7_0212(void)
{
    char  *  *p;
    char  *  *q;

    p = db_LoadObject(0x14, 9);
    g_3DA4 = *p;
    q = db_LoadObject(0x13, 9);
    g_3DA8 = *q;
    if (q == 0 || p == 0) {
        dos_printf("Could not find fonts");
        Punt("Could not find fonts!");
    }
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x13, 9);
}

void  o20_39C7_02A8(void)
{
}

#pragma pack(pop)
