/*
 * Contains six empty debug entry points in the DOS release. WinPrintf has a named Win16
 * counterpart; the other stub identities remain uncertain.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 277D; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory. Some pairs are HIGH
 * confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Gs /Zi.
 *
 * Each stub is one RETF. Only WinPrintf has a named counterpart (HIGH);
 * the siblings keep address names. Without /Gs each stub would be eight bytes.
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
