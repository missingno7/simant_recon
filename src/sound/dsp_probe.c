/* Root module 29B8 (0x29B80-0x29BF7): sound card DSP reset and detection. */

int fd_55B3_7564 = 0;

extern void far f_29F0_002A(int port, char value);
extern unsigned char far f_29F0_0038(int port);

int far f_29B8_0000(void)
{
    int i;
    unsigned char c;

    f_29F0_002A(fd_55B3_7564 + 6, 1);
    for (i = 0; i < 9999; i++)
        ;
    f_29F0_002A(fd_55B3_7564 + 6, 0);
    for (i = 0; i < 9999; i++)
        ;
    for (i = 0; i < 200 && !(c & 0x80); i++)
        c = f_29F0_0038(fd_55B3_7564 + 0xe);
    if (f_29F0_0038(fd_55B3_7564 + 0xa) == 0xaa)
        return 1;
    return 0;
}
