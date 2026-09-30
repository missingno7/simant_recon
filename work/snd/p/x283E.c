/* ASM-1 contrast for module 283E: the same bodies as MSC functions with inline asm */
void far f_283E_000A(char reg, char value)
{
    _asm {
        mov dx, 388h
        mov ah, reg
        mov al, value
    }
}
void far f_283E_0020(void)
{
    _asm {
        push ax
        mov al, ah
        out dx, al
        mov cx, 10
    l1: in al, dx
        loop l1
    }
}
