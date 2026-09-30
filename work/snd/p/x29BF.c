/* ASM-1 contrast for module 29BF: a near helper with an inline-asm body */
extern unsigned near g_75B2;
static void near f_29BF_00B7(void)
{
    _asm {
    l1: mov dx, g_75B2
        out dx, al
        jmp short l2
    l2: inc ah
        loop l1
        stc
    }
}
void far f_29BF_00E6(int reg, int value) { f_29BF_00B7(); }
