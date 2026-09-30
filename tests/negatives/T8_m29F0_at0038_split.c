/* AUDIT T8: an invented second object of frame 29F0 holding only its last function */
unsigned char far f_29F0_0038(int port)
{
    unsigned char value;

    _asm {
        mov dx, port
        in al, dx
        mov value, al
    }
    return value;
}
