/*
 * Module at root frame 277D: six empty far functions (6 bytes, one RETF each).
 * The Win16 build implements WinPrintf and sibling debug formatters; in this
 * DOS release they compile to empty bodies.  Only WinPrintf is named (xver HIGH);
 * the siblings keep address names until independent evidence identifies them.
 * Compiled with /Gs: with stack checking each would be an 8-byte frame.
 */

int far WinPrintf(char far *format, ...)
{
}

void far f_277D_000B(void)
{
}

void far f_277D_000C(void)
{
}

void far f_277D_000D(void)
{
}

void far f_277D_000E(void)
{
}

void far f_277D_000F(void)
{
}
