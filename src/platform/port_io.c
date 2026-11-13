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

/*
 * Disable interrupts around sample state changes; does not save FLAGS.
 */
void far snd_sample_interrupts_disable(void)
{
    _asm cli
}

/*
 * Enable interrupts after sample state changes; does not restore FLAGS.
 */
void far snd_sample_interrupts_enable(void)
{
    _asm sti
}

/*
 * Disable interrupts for sound control updates; does not save FLAGS.
 */
void far snd_control_interrupts_disable(void)
{
    _asm cli
}

/*
 * Enable interrupts after sound control updates; does not restore FLAGS.
 */
void far snd_control_interrupts_enable(void)
{
    _asm sti
}

/*
 * Write the low byte of value to the specified I/O port.
 */
void far snd_port_write_byte(int port, int value)
{
    _asm {
        mov dx, port
        mov al, byte ptr value
        out dx, al
    }
}

/*
 * Read one byte from the specified I/O port.
 */
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
