/*
 * Port and interrupt-flag helpers (root module, code frame 29F0; linear 0x29F0A-0x29F4C).
 * C functions whose bodies are MSC inline assembly.
 */

void far f_29F0_000A(void)
{
    _asm _emit 0xFA  /* AUDIT T4b: opcode byte instead of the instruction */
}

void far f_29F0_0012(void)
{
    _asm sti
}

void far f_29F0_001A(void)
{
    _asm _emit 0xFA  /* AUDIT T4b: opcode byte instead of the instruction */
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
