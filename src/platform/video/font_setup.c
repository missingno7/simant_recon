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
extern char far * near gfx_primary_font_offset;
extern char far * near gfx_secondary_font;
extern void far db_UnhookObject(int object, int kind);

/*
 * Load font objects 14h/15h for the Hercules driver.
 */
void far gfx_load_fonts_hercules(void)
{
    gfx_primary_font_offset = *db_LoadObject(0x14, 9);
    gfx_secondary_font = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern int far printf(char far *format, ...);
extern void far Punt(char far *fmt, ...);

/*
 * Load font objects 14h/13h for the Tandy driver.
 */
void far gfx_load_fonts_tandy(void)
{
    char far * far *p;
    char far * far *q;

    p = db_LoadObject(0x14, 9);
    gfx_secondary_font = *p;
    q = db_LoadObject(0x13, 9);
    gfx_primary_font_offset = *q;
    if (q == 0 || p == 0) {
        printf("Could not find fonts");
        Punt("Could not find fonts!");
    }
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x13, 9);
}

/*
 * Load font objects 14h/15h for the 480-line monochrome driver.
 */
void far gfx_load_fonts_mono_480(void)
{
    gfx_primary_font_offset = *db_LoadObject(0x14, 9);
    gfx_secondary_font = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

/*
 * Load font objects 14h/15h for the 350/400-line monochrome drivers.
 */
void far gfx_load_fonts_mono_350_400(void)
{
    gfx_primary_font_offset = *db_LoadObject(0x14, 9);
    gfx_secondary_font = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern void far WinPrintf(char far *fmt, ...);

/*
 * Install font object 13h for the 320-pixel planar driver if available.
 */
void far gfx_load_font_planar_320(void)
{
    char far * far *p;

    p = db_LoadObject(0x13, 9);
    if (p) {
        WinPrintf("\nFont loaded!");
        gfx_primary_font_offset = *p;
        db_UnhookObject(0x13, 9);
    }
}

void far o20_39C7_0211(void)
{
}

/*
 * Load font objects 14h/13h for the 256-colour VGA driver.
 */
void far gfx_load_fonts_vga256(void)
{
    char far * far *p;
    char far * far *q;

    p = db_LoadObject(0x14, 9);
    gfx_secondary_font = *p;
    q = db_LoadObject(0x13, 9);
    gfx_primary_font_offset = *q;
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
