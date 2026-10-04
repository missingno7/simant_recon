struct MiscPoint { int x; int y; };
extern struct MiscPoint far fd_50F6_07CA;
extern struct MiscPoint far fd_50F6_0852;
extern struct MiscPoint far fd_50F6_08DE;
extern struct MiscPoint far fd_50F6_08EC;
extern struct MiscPoint far fd_50F6_09F2;
extern char far fd_50F6_0B0A[4];
extern char far * far fd_50F6_0B22;
extern unsigned char far fd_50F6_1114[30 * 40];
extern int far fd_50F6_15C4[30][40];
extern int far puts(char far *text);
extern int far printf(char far *format, ...);

unsigned char far miscPtrBytes[8] = {0,0,0,0,0x51,0x62,0x73,0x84};
struct MiscSaveRec { int size; int count; void far *data; };
struct MiscSaveRec far miscSave07CA = {4, 1, (void far *)&fd_50F6_07CA};
void far Dump(char far *name, unsigned char far *data, unsigned length)
{
    unsigned i;
    printf("RAW %s %u ", name, length);
    for (i = 0; i < length; i++) printf("%02X", data[i]);
    puts("");
}
int main(void)
{
    unsigned x, y, i;
    unsigned char far *p;
    if (fd_50F6_07CA.x || fd_50F6_07CA.y) goto fail;
    if (fd_50F6_0852.x || fd_50F6_0852.y) goto fail;
    if (fd_50F6_08DE.x || fd_50F6_08DE.y) goto fail;
    if (fd_50F6_08EC.x || fd_50F6_08EC.y) goto fail;
    if (fd_50F6_09F2.x || fd_50F6_09F2.y) goto fail;
    if (fd_50F6_0B0A[0] || fd_50F6_0B0A[1] || fd_50F6_0B0A[2] || fd_50F6_0B0A[3]) goto fail;
    if (fd_50F6_0B22 != 0 || miscSave07CA.size != 4 || miscSave07CA.count != 1 ||
        miscSave07CA.data != (void far *)&fd_50F6_07CA) goto fail;
    for (y = 0; y < 30; y++) for (x = 0; x < 40; x++)
        if (fd_50F6_15C4[y][x]) goto fail;
    for (i = 0; i < 1200; i++) if (fd_50F6_1114[i]) goto fail;
    puts("STARTUP-ZERO 9 symbols / 3628 source-typed bytes; SaveRec 07CA=4/1");
    fd_50F6_07CA.x = -1; fd_50F6_07CA.y = 0x2345;
    fd_50F6_0852.x = -2; fd_50F6_0852.y = 0x1234;
    fd_50F6_08DE.x = -3; fd_50F6_08DE.y = 0x3456;
    fd_50F6_08EC.x = -4; fd_50F6_08EC.y = 0x4567;
    fd_50F6_09F2.x = -5; fd_50F6_09F2.y = 0x5678;
    fd_50F6_0B0A[0]=0xA0; fd_50F6_0B0A[1]=0xA1; fd_50F6_0B0A[2]=0xA2; fd_50F6_0B0A[3]=0xA3;
    fd_50F6_0B22 = (char far *)miscPtrBytes;
    if (fd_50F6_0B22 != (char far *)miscPtrBytes || fd_50F6_0B22[4] != 0x51) goto fail;
    for (i = 0; i < 1200; i++) fd_50F6_1114[i] = (unsigned char)((i * 7 + 3) & 255);
    for (y = 0; y < 30; y++) for (x = 0; x < 40; x++)
        fd_50F6_15C4[y][x] = (int)(y * 40 + x) - 600;
    puts("TYPED-WRITES signed Point fields, four-byte cheat buffer, far-pointer slot, 30x40 byte/int maps");
    if (fd_50F6_07CA.x != (-1) || fd_50F6_07CA.y != 0x2345) goto fail;
    if (fd_50F6_0852.x != (-2) || fd_50F6_0852.y != 0x1234) goto fail;
    if (fd_50F6_08DE.x != (-3) || fd_50F6_08DE.y != 0x3456) goto fail;
    if (fd_50F6_08EC.x != (-4) || fd_50F6_08EC.y != 0x4567) goto fail;
    if (fd_50F6_09F2.x != (-5) || fd_50F6_09F2.y != 0x5678) goto fail;
    if (fd_50F6_07CA.x >= 0 || fd_50F6_07CA.x != -1) goto fail;
    p = (unsigned char far *)fd_50F6_0B0A;
    if (p[0] != 0xA0 || p[3] != 0xA3) goto fail;
    if (fd_50F6_15C4[0][0] != -600 || fd_50F6_15C4[29][39] != 599) goto fail;
    if (fd_50F6_1114[0] != 3 || fd_50F6_1114[1199] != ((1199 * 7 + 3) & 255)) goto fail;
    Dump("fd_50F6_07CA", (unsigned char far *)&(fd_50F6_07CA), 4);
    Dump("fd_50F6_0852", (unsigned char far *)&(fd_50F6_0852), 4);
    Dump("fd_50F6_08DE", (unsigned char far *)&(fd_50F6_08DE), 4);
    Dump("fd_50F6_08EC", (unsigned char far *)&(fd_50F6_08EC), 4);
    Dump("fd_50F6_09F2", (unsigned char far *)&(fd_50F6_09F2), 4);
    Dump("fd_50F6_0B0A", (unsigned char far *)&(fd_50F6_0B0A), 4);
    Dump("fd_50F6_0B22", (unsigned char far *)&(fd_50F6_0B22), 4);
    Dump("fd_50F6_1114", (unsigned char far *)&(fd_50F6_1114), 1200);
    Dump("fd_50F6_15C4", (unsigned char far *)&(fd_50F6_15C4), 2400);
    puts("PASS"); return 0;
fail: puts("FAIL positive typed owner fixture"); return 1;
}
