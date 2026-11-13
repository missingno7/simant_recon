/* AUDIT T6b: first function dropped, extent starts at the second */
/*
 * Port and interrupt-flag helpers (root module, code frame 29F0; linear 0x29F0A-0x29F4C).
 * C functions whose bodies are MSC inline assembly.
 */

void far snd_sample_interrupts_enable(void)
{
    _asm sti
}

void far snd_control_interrupts_disable(void)
{
    _asm cli
}

void far snd_control_interrupts_enable(void)
{
    _asm sti
}

void far snd_port_write_byte(int port, int value)
{
    _asm {
        mov dx, port
        mov al, byte ptr value
        out dx, al
    }
}

unsigned char far snd_port_read_byte(int port)
{
    unsigned char value;

    _asm {
        mov dx, port
        in al, dx
        mov value, al
    }
    return value;
}
