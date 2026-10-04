extern char far * near sys_errlist[];
extern int near sys_nerr;
extern char near g_8CCB;

static char far *g_567A[] = {
    "Write-protection error",
    "Unknown unit",
    "Drive not ready",
    "Unknown command",
    "Data error (bad CRC)",
    "Bad request structure length",
    "seek error",
    "unknown media type",
    "sector not found",
    "printer out of paper",
    "write fault",
    "read fault",
    "general failure",
    "abort request"
};

static int g_56B2 = 12;

char far * far f_1C62_06A6(int err)
{
    if (err > sys_nerr || err < 0)
        return g_567A[g_8CCB];
    return sys_errlist[err];
}

extern int far printf(char far *format, ...);

int main(void)
{
    int i;
    int signed_probe;

    if (sizeof(g_8CCB) != 1) {
        printf("SELECTOR FAIL width=%u\n", sizeof(g_8CCB));
        return 1;
    }
    if (g_8CCB != 0) {
        printf("SELECTOR FAIL init=%d\n", (int)g_8CCB);
        return 1;
    }
    
    if (f_1C62_06A6(0) != sys_errlist[0] || f_1C62_06A6(sys_nerr) != sys_errlist[sys_nerr]) {
        printf("SELECTOR FAIL crt_range\n");
        return 1;
    }
    for (i = 0; i < 14; i++) {
        g_8CCB = i;
        if (f_1C62_06A6(-1) != g_567A[i] || f_1C62_06A6(sys_nerr + 1) != g_567A[i]) {
            printf("SELECTOR FAIL index=%d\n", i);
            return 1;
        }
    }
    *((unsigned char near *)&g_8CCB) = 0x80;
    signed_probe = g_8CCB;
    if (signed_probe != -128) {
        printf("SELECTOR FAIL signed=%d\n", signed_probe);
        return 1;
    }
    g_8CCB = 0;
    printf("SELECTOR PASS width=1 signed=%d entries=14 init=0\n", signed_probe);
    return 0;
}
