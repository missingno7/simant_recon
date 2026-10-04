struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};
struct EventBases {
    void far *current;
    void far *previous;
};

extern struct Event far fd_50F6_49FA;
extern struct Event far fd_50F6_4A0A;
extern struct EventBases far eventBases;
extern int far puts(char far *text);

#define EVENT_OFF(e, f) ((unsigned)((char far *)&((e).f) - (char far *)&(e)))

int far main(void)
{
    volatile unsigned char far *currentBytes;
    volatile unsigned char far *previousBytes;
    unsigned char expected[18];
    unsigned int i;

    currentBytes = (volatile unsigned char far *)&fd_50F6_49FA;
    previousBytes = (volatile unsigned char far *)&fd_50F6_4A0A;

    
    if (sizeof(struct Event) != 16) {
        puts("FAIL Event size");
        return 11;
    }
    if (EVENT_OFF(fd_50F6_49FA, what) != 0 ||
        EVENT_OFF(fd_50F6_49FA, message) != 2 ||
        EVENT_OFF(fd_50F6_49FA, x4) != 4 ||
        EVENT_OFF(fd_50F6_49FA, modifiers) != 6 ||
        EVENT_OFF(fd_50F6_49FA, h) != 8 ||
        EVENT_OFF(fd_50F6_49FA, v) != 10 ||
        EVENT_OFF(fd_50F6_49FA, code) != 12 ||
        EVENT_OFF(fd_50F6_49FA, xE) != 14) {
        puts("FAIL Event field offsets");
        return 12;
    }

    if (eventBases.current != (void far *)&fd_50F6_49FA ||
        eventBases.previous != (void far *)&fd_50F6_4A0A) {
        puts("REJECTED: symbolic base mismatch");
        return 13;
    }

    for (i = 0; i < 16; i++) {
        if (currentBytes[i] != 0 || previousBytes[i] != 0) {
            puts("REJECTED: nonzero initialized Event at CRT entry");
            return 14;
        }
    }
    if (previousBytes[14] != 1) {
        puts("FAIL initializer contrast");
        return 15;
    }

    for (i = 0; i < 16; i++) {
        expected[i] = (unsigned char)((i * 29 + 0x37) & 0xff);
        currentBytes[i] = expected[i];
    }
    fd_50F6_4A0A = fd_50F6_49FA;
    for (i = 0; i < 16; i++) {
        if (currentBytes[i] != expected[i] || previousBytes[i] != expected[i]) {
            puts("FAIL whole-record copy or byte canary");
            return 16;
        }
    }
    if (currentBytes[0] != 0x37 || currentBytes[15] != expected[15] ||
        previousBytes[0] != 0x37 || previousBytes[15] != expected[15]) {
        puts("FAIL first/last byte canary");
        return 17;
    }

    puts("REJECTED");
    return 0;
}
