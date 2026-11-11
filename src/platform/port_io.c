/*
 * Provides byte port input and output helpers. It also wraps interrupt flag save, disable and
 * restore operations using MSC inline assembly.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 29F0; complete original translation unit.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 * Build profile: msc600ax; /AL /Os /Gs /Zi.
 *
 * The C function bodies use MSC inline assembly.
 */

void far f_29F0_000A(void)
{
    _asm cli
}

void far f_29F0_0012(void)
{
    _asm sti
}

void far f_29F0_001A(void)
{
    _asm cli
}

void far f_29F0_0022(void)
{
    _asm sti
}

void far f_29F0_002A(int port, int value)
{
    _asm {
        mov dx, port
        mov al, byte ptr value
        out dx, al
    }
}

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
