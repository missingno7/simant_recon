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

void far snd_sample_interrupts_disable(void)
{
    _asm cli
}

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
