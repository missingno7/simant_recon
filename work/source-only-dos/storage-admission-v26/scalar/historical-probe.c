extern int far fd_50F6_04E0;
extern int far fd_50F6_04F2;
extern int far fd_50F6_0502;
extern int far fd_50F6_0510;
extern int far fd_50F6_059E;
extern int far fd_50F6_06AC;
extern long far fd_50F6_0736;
extern int far fd_50F6_08DC;
extern int far fd_50F6_08E8;
extern int far fd_50F6_0D9A;
extern int far fd_50F6_0FF8;
extern int far fd_50F6_1004;
extern int far fd_50F6_1006;
extern int far fd_50F6_103A;
extern int far fd_50F6_103C;
extern int far fd_50F6_1044;
extern int far fd_50F6_1046;
extern int far fd_50F6_1048;
extern int far fd_50F6_104A;

struct SaveRec { int size; int count; void far *data; };
struct SaveRec far V26Save[14] = {
    {2, 1, (void far *)&fd_50F6_04E0},
    {2, 1, (void far *)&fd_50F6_04F2},
    {2, 1, (void far *)&fd_50F6_0502},
    {2, 1, (void far *)&fd_50F6_0510},
    {2, 1, (void far *)&fd_50F6_059E},
    {2, 1, (void far *)&fd_50F6_06AC},
    {4, 1, (void far *)&fd_50F6_0736},
    {2, 1, (void far *)&fd_50F6_08DC},
    {2, 1, (void far *)&fd_50F6_08E8},
    {2, 1, (void far *)&fd_50F6_1004},
    {2, 1, (void far *)&fd_50F6_1006},
    {2, 1, (void far *)&fd_50F6_103C},
    {2, 1, (void far *)&fd_50F6_1044},
    {2, 1, (void far *)&fd_50F6_1048},
};
extern int far puts(char far *text);
int main(void)
{
    unsigned char far *p;
    if (fd_50F6_04E0 != 0 || fd_50F6_04F2 != 0 || fd_50F6_0502 != 0 || fd_50F6_0510 != 0 || fd_50F6_059E != 0 || fd_50F6_06AC != 0 || fd_50F6_0736 != 0 || fd_50F6_08DC != 0 || fd_50F6_08E8 != 0 || fd_50F6_0D9A != 0 || fd_50F6_0FF8 != 0 || fd_50F6_1004 != 0 || fd_50F6_1006 != 0 || fd_50F6_103A != 0 || fd_50F6_103C != 0 || fd_50F6_1044 != 0 || fd_50F6_1046 != 0 || fd_50F6_1048 != 0 || fd_50F6_104A != 0) goto fail;
    if (V26Save[0].size != 2 || V26Save[0].count != 1 || V26Save[0].data != (void far *)&fd_50F6_04E0) goto fail;
    if (V26Save[1].size != 2 || V26Save[1].count != 1 || V26Save[1].data != (void far *)&fd_50F6_04F2) goto fail;
    if (V26Save[2].size != 2 || V26Save[2].count != 1 || V26Save[2].data != (void far *)&fd_50F6_0502) goto fail;
    if (V26Save[3].size != 2 || V26Save[3].count != 1 || V26Save[3].data != (void far *)&fd_50F6_0510) goto fail;
    if (V26Save[4].size != 2 || V26Save[4].count != 1 || V26Save[4].data != (void far *)&fd_50F6_059E) goto fail;
    if (V26Save[5].size != 2 || V26Save[5].count != 1 || V26Save[5].data != (void far *)&fd_50F6_06AC) goto fail;
    if (V26Save[6].size != 4 || V26Save[6].count != 1 || V26Save[6].data != (void far *)&fd_50F6_0736) goto fail;
    if (V26Save[7].size != 2 || V26Save[7].count != 1 || V26Save[7].data != (void far *)&fd_50F6_08DC) goto fail;
    if (V26Save[8].size != 2 || V26Save[8].count != 1 || V26Save[8].data != (void far *)&fd_50F6_08E8) goto fail;
    if (V26Save[9].size != 2 || V26Save[9].count != 1 || V26Save[9].data != (void far *)&fd_50F6_1004) goto fail;
    if (V26Save[10].size != 2 || V26Save[10].count != 1 || V26Save[10].data != (void far *)&fd_50F6_1006) goto fail;
    if (V26Save[11].size != 2 || V26Save[11].count != 1 || V26Save[11].data != (void far *)&fd_50F6_103C) goto fail;
    if (V26Save[12].size != 2 || V26Save[12].count != 1 || V26Save[12].data != (void far *)&fd_50F6_1044) goto fail;
    if (V26Save[13].size != 2 || V26Save[13].count != 1 || V26Save[13].data != (void far *)&fd_50F6_1048) goto fail;
    fd_50F6_04E0 = 4608;
    fd_50F6_04F2 = 4611;
    fd_50F6_0502 = 4614;
    fd_50F6_0510 = 4617;
    fd_50F6_059E = 4620;
    fd_50F6_06AC = 4623;
    fd_50F6_0736 = 0x11223344L;
    fd_50F6_08DC = 4629;
    fd_50F6_08E8 = 4632;
    fd_50F6_0D9A = 4635;
    fd_50F6_0FF8 = 4638;
    fd_50F6_1004 = 4641;
    fd_50F6_1006 = 4644;
    fd_50F6_103A = 4647;
    fd_50F6_103C = 4650;
    fd_50F6_1044 = 4653;
    fd_50F6_1046 = 4656;
    fd_50F6_1048 = 4659;
    fd_50F6_104A = 4662;
    if (fd_50F6_04E0 != 4608 || fd_50F6_04F2 != 4611 || fd_50F6_0502 != 4614 || fd_50F6_0510 != 4617 || fd_50F6_059E != 4620 || fd_50F6_06AC != 4623 || fd_50F6_0736 != 287454020 || fd_50F6_08DC != 4629 || fd_50F6_08E8 != 4632 || fd_50F6_0D9A != 4635 || fd_50F6_0FF8 != 4638 || fd_50F6_1004 != 4641 || fd_50F6_1006 != 4644 || fd_50F6_103A != 4647 || fd_50F6_103C != 4650 || fd_50F6_1044 != 4653 || fd_50F6_1046 != 4656 || fd_50F6_1048 != 4659 || fd_50F6_104A != 4662) goto fail;
    p = (unsigned char far *)&fd_50F6_04E0;
    if (p[0] != 0x00 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_04F2;
    if (p[0] != 0x03 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_0502;
    if (p[0] != 0x06 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_0510;
    if (p[0] != 0x09 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_059E;
    if (p[0] != 0x0c || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_06AC;
    if (p[0] != 0x0f || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_0736;
    if (p[0] != 0x44 || p[1] != 0x33 || p[2] != 0x22 || p[3] != 0x11) goto fail;
    p = (unsigned char far *)&fd_50F6_08DC;
    if (p[0] != 0x15 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_08E8;
    if (p[0] != 0x18 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_0D9A;
    if (p[0] != 0x1b || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_0FF8;
    if (p[0] != 0x1e || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_1004;
    if (p[0] != 0x21 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_1006;
    if (p[0] != 0x24 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_103A;
    if (p[0] != 0x27 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_103C;
    if (p[0] != 0x2a || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_1044;
    if (p[0] != 0x2d || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_1046;
    if (p[0] != 0x30 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_1048;
    if (p[0] != 0x33 || p[1] != 0x12) goto fail;
    p = (unsigned char far *)&fd_50F6_104A;
    if (p[0] != 0x36 || p[1] != 0x12) goto fail;
    fd_50F6_04E0 = -1;
    if (fd_50F6_04E0 != -1 || fd_50F6_04E0 >= 0) goto fail;
    p = (unsigned char far *)&fd_50F6_04E0;
    if (p[0] != 0xff || p[1] != 0xff) goto fail;
    fd_50F6_0736 = -1L;
    if (fd_50F6_0736 != -1L || fd_50F6_0736 >= 0L) goto fail;
    p = (unsigned char far *)&fd_50F6_0736;
    if (p[0] != 0xff || p[1] != 0xff || p[2] != 0xff || p[3] != 0xff) goto fail;
    puts("PASS"); return 0;
fail: puts("FAIL"); return 1;
}
