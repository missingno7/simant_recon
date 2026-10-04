extern int far fd_50F6_0EB6[32];
extern int far HistogramProbeAlias[32];
extern int far puts(char far *text);
int main(void)
{
    int i;
    int value;
    unsigned char far *raw;
    if (sizeof(fd_50F6_0EB6[0]) != 2 || sizeof(fd_50F6_0EB6) != 64) {
        puts("REJECTED_SIZE"); return 0;
    }
    if ((void far *)&fd_50F6_0EB6[0] != (void far *)&HistogramProbeAlias[0]) {
        puts("REJECTED_BASE"); return 0;
    }
for (i = 0; i < 32; i++) {
        if (fd_50F6_0EB6[i] != 0) { puts("REJECTED_CRT_ZERO"); return 0; }
    }
    fd_50F6_0EB6[0] = -1;
    for (i = 1; i < 32; i++) fd_50F6_0EB6[i] = 0x0102 + i * 7;
    raw = (unsigned char far *)&fd_50F6_0EB6[0];
    if (fd_50F6_0EB6[0] != -1 || raw[0] != 0xff || raw[1] != 0xff) {
        puts("REJECTED_SIGNED_OR_RAW"); return 0;
    }
    for (i = 1; i < 32; i++) {
        value = 0x0102 + i * 7;
        if (fd_50F6_0EB6[i] != value || raw[2 * i] != (value & 0xff) ||
            raw[2 * i + 1] != ((value >> 8) & 0xff)) {
            puts("REJECTED_WORD_OR_RAW"); return 0;
        }
    }
    puts("PASS"); return 0;
}
