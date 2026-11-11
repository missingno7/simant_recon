/* Overlay section S20, code frame 39C7: display driver font loaders and empty hooks. */

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

void far o20_39C7_0008(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern int far printf(char far *format, ...);
extern void far Punt(char far *fmt, ...);

void far o20_39C7_0069(void)
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

void far o20_39C7_00FF(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

void far o20_39C7_0160(void)
{
    g_3DA8 = *db_LoadObject(0x14, 9);
    g_3DA4 = *db_LoadObject(0x15, 9);
    db_UnhookObject(0x14, 9);
    db_UnhookObject(0x15, 9);
}

extern void far WinPrintf(char far *fmt, ...);

void far o20_39C7_01C1(void)
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

void far o20_39C7_0212(void)
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
