struct SaveRec {
    int size;
    int count;
    void far *data;
};

extern int far fd_50F6_0468;
extern int far fd_50F6_0370;
extern int far fd_50F6_024E;
extern struct SaveRec far flagRecords[];
extern int far puts(char far *text);

int far main(void)
{
    unsigned char far *p024e;
    unsigned char far *p0370;
    unsigned char far *p0468;
    unsigned char saved[6];
    int i;
    int j;
    int k;

    p024e = (unsigned char far *)&fd_50F6_024E;
    p0370 = (unsigned char far *)&fd_50F6_0370;
    p0468 = (unsigned char far *)&fd_50F6_0468;
    if (fd_50F6_0468 != 0 || fd_50F6_0370 != 0 || fd_50F6_024E != 0 ||
        p024e[0] != 0 || p024e[1] != 0 || p0370[0] != 0 || p0370[1] != 0 ||
        p0468[0] != 0 || p0468[1] != 0) {
        puts("FAIL startup zero-fill");
        return 1;
    }

    fd_50F6_0468 = 1;
    fd_50F6_0370 = -1;
    fd_50F6_024E = -1;
    if (fd_50F6_0468 != 1 || fd_50F6_0370 != -1 || fd_50F6_024E != -1 ||
        p0468[0] != 1 || p0468[1] != 0 || p0370[0] != 0xff || p0370[1] != 0xff ||
        p024e[0] != 0xff || p024e[1] != 0xff) {
        puts("FAIL signed word byte view");
        return 2;
    }

    k = 0;
    for (i = 0; flagRecords[i].count != 0; i++) {
        unsigned char far *data;
        if (flagRecords[i].size != 2 || flagRecords[i].count != 1) {
            puts("FAIL SaveRec2 shape");
            return 3;
        }
        if ((i == 0 && flagRecords[i].data != (void far *)&fd_50F6_024E) ||
            (i == 1 && flagRecords[i].data != (void far *)&fd_50F6_0370) ||
            (i == 2 && flagRecords[i].data != (void far *)&fd_50F6_0468) || i > 2) {
            puts("FAIL SaveRec2 address");
            return 4;
        }
        data = (unsigned char far *)flagRecords[i].data;
        for (j = 0; j < flagRecords[i].size * flagRecords[i].count; j++)
            saved[k++] = data[j];
    }
    if (i != 3 || k != 6) {
        puts("FAIL SaveRec2 terminator");
        return 5;
    }

    fd_50F6_0468 = 0x2345;
    fd_50F6_0370 = 0x3456;
    fd_50F6_024E = 0x4567;
    k = 0;
    for (i = 0; flagRecords[i].count != 0; i++) {
        unsigned char far *data;
        data = (unsigned char far *)flagRecords[i].data;
        for (j = 0; j < flagRecords[i].size * flagRecords[i].count; j++)
            data[j] = saved[k++];
    }
    if (fd_50F6_0468 != 1 || fd_50F6_0370 != -1 || fd_50F6_024E != -1) {
        puts("FAIL SaveRec2 restore");
        return 6;
    }
    puts("PASS");
    return 0;
}
