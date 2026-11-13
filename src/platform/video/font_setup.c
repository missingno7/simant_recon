/*
 * Loads the fonts required by the display modes and provides empty driver hooks. The graphics
 * selector chooses these setup functions along with the raster driver.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 20 (S20); segment 39C7; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Og /Oe /Gs /Zi.
 */

void far o20_39C7_0000(void)
{
}

void far o20_39C7_0001(void)
{
}

void far o20_39C7_0002(void)
{
}

void far o20_39C7_0003(void)
{
}

void far o20_39C7_0004(void)
{
}

void far o20_39C7_0005(void)
{
}

void far o20_39C7_0006(void)
{
}

void far o20_39C7_0007(void)
{
}

extern char far * far * far db_LoadObject(int object, int kind);
extern char far * near g_3DA8;
extern char far * near g_3DA4;
extern void far db_UnhookObject(int object, int kind);

void far gfx_load_fonts_hercules(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern int far printf(char far *format, ...);
extern void far Punt(char far *fmt, ...);

void far gfx_load_fonts_tandy(void)
{
    char far * far *p;
    char far * far *q;

    p = db_LoadObject(0x14, 9);
    g_3DA4 = *p;
    q = db_LoadObject(0x13, 9);
    g_3DA8 = *q;
    if (q == 0 || p == 0) {
        printf("Could not find fonts");
        Punt("Could not find fonts!");
    }
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x13, 9);
}

void far gfx_load_fonts_mono_480(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

void far gfx_load_fonts_mono_350_400(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern void far WinPrintf(char far *fmt, ...);

void far gfx_load_font_planar_320(void)
{
    char far * far *p;

    p = db_LoadObject(0x13, 9);
    if (p) {
        WinPrintf("\nFont loaded!");
        g_3DA8 = *p;
        db_UnhookObject(0x13, 9);
    }
}

void far o20_39C7_0211(void)
{
}

void far gfx_load_fonts_vga256(void)
{
    char far * far *p;
    char far * far *q;

    p = db_LoadObject(0x14, 9);
    g_3DA4 = *p;
    q = db_LoadObject(0x13, 9);
    g_3DA8 = *q;
    if (q == 0 || p == 0) {
        printf("Could not find fonts");
        Punt("Could not find fonts!");
    }
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x13, 9);
}

void far o20_39C7_02A8(void)
{
}
