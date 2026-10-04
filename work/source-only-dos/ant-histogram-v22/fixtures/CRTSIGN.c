extern unsigned int far fd_50F6_0EB6[32];
extern int far HistogramProbeAlias[32];
extern int far puts(char far *text);
int main(void)
{
    if ((void far *)&fd_50F6_0EB6[0] != (void far *)&HistogramProbeAlias[0]) {
        puts("REJECTED_BASE"); return 0;
    }
    fd_50F6_0EB6[0] = -1;
    if (fd_50F6_0EB6[0] < 0) { puts("FAIL_UNEXPECTED_SIGNED"); return 0; }
    puts("REJECTED_UNSIGNED_VIEW"); return 0;
}
