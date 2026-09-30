/* Root module 293A (0x293A6-0x295CA): sound device detection. */

int far f_293A_0029(void);
int far f_293A_002D(void);
int far f_293A_0059(void);
int far f_293A_0087(void);
int far f_293A_0121(void);
int far f_293A_015E(void);
int far f_293A_017C(void);
int far f_293A_017F(void);

extern int far fd_50F6_01F0[];

int (far *fd_55B3_74DA[])(void) = {
    f_293A_0029, f_293A_0029, f_293A_002D, f_293A_0059, f_293A_0087,
    f_293A_015E, f_293A_0121, f_293A_017C, f_293A_017F
};
int far *fd_55B3_74FE = fd_50F6_01F0;

int far f_293A_0006(void)
{
    int i;
    int found;

    found = 0;
    for (i = 8; i > 0; i--) {
        if (fd_55B3_74DA[i]()) {
            found = i;
            break;
        }
    }
    return found;
}

int far f_293A_0029(void)
{
    return 1;
}

int far f_293A_002D(void)
{
    char far *p;
    int base;

    _asm {
        mov ah, 81h
        int 1Ah
        mov base, ax
    }
    p = (char far *)0xFC000000L;
    return *p == 0x21 || base == 0xc4;
}

int far f_293A_0059(void)
{
    _asm {
        push es
        mov ax, 0C000h
        int 15h
        add bx, 2
        mov ax, es:[bx]
        pop es
        cmp ax, 0BFCh
        jne none
        mov al, 2Fh
        cli
        out 70h, al
        jmp short delay
    delay:
        in al, 71h
        sti
        test al, 10h
        je none
    }
    return 1;
none:
    return 0;
}

extern void far f_283E_000A(char reg, char value);
extern unsigned char far f_29F0_0038(int port);

int far f_293A_0087(void)
{
    int s1;
    unsigned i;

    f_283E_000A(4, 0x60);
    f_283E_000A(4, 0x80);
    s1 = f_29F0_0038(0x388);
    f_283E_000A(2, 0xff);
    f_283E_000A(4, 0x21);
    for (i = 0; i < 200; i++)
        f_29F0_0038(0x388);
    i = f_29F0_0038(0x388);
    f_283E_000A(4, 0x60);
    f_283E_000A(4, 0x80);
    if ((s1 & 0xe0) == 0 && (i & 0xe0) == 0xc0)
        return 1;
    return 0;
}

extern unsigned far fd_55B3_7564;
extern int far f_29B8_0000(void);

int far f_293A_0121(void)
{
    int found;

    found = 0;
    fd_55B3_7564 = 0x200;
    while (!found) {
        if (fd_55B3_7564 >= 0x260)
            break;
        fd_55B3_7564 += 0x10;
        found = f_29B8_0000();
    }
    return found;
}

extern int far f_29BF_0139(void);
extern int far fd_50F6_4B14;

int far f_293A_015E(void)
{
    int port;

    if ((port = f_29BF_0139()) == 0)
        return 0;
    fd_50F6_4B14 = port;
    return 1;
}

int far f_293A_017C(void)
{
    return 0;
}

extern void far f_29F0_002A(int port, char value);

int far f_293A_017F(void)
{
    int i;
    int tries;
    int ok;
    int ready;

    ok = 0;
    ready = 0;
    if (!(f_29F0_0038(0x331) & 0x80))
        f_29F0_0038(0x330);
    for (i = 0; i < 5000; i++) {
        if (!(f_29F0_0038(0x331) & 0x40)) {
            ok = 1;
            break;
        }
    }
    if (ok) {
        f_29F0_002A(0x331, 0xff);
        for (tries = 0; tries < 3; tries++) {
            for (i = 0; i < 5000; i++) {
                if (!(f_29F0_0038(0x331) & 0x80)) {
                    ready = 1;
                    break;
                }
            }
            if (ready) {
                if (f_29F0_0038(0x330) == 0xfe)
                    return 1;
                ready = 0;
            }
        }
    }
    return 0;
}
