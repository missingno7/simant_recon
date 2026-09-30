/* ASM-1 experiment for module 195A: the same bodies as MSC functions with inline _asm. */
extern unsigned char near g_360C;
void far f_195A_02B7(void);

void far f_195A_000C(void)
{
    _asm {
        mov ah, 46h
        int 67h
        and ah, ah
        jne done
        mov g_360C, al
    done:
    }
}

void far f_195A_00AC(void far *map)
{
    _asm {
        push ds
        push si
        mov ax, 4E01h
        lds si, map
        int 67h
        and ah, ah
        je ok
        call f_195A_02B7
    ok:
        xor al, al
        pop si
        pop ds
    }
}

void far f_195A_00AD(void far *map)
{
    _asm {
        mov ax, 4E01h
        lds si, map
        int 67h
        and ah, ah
        je ok
        call f_195A_02B7
    ok:
        xor al, al
    }
}

int far f_195A_004B(int handle)
{
    _asm {
        mov ah, 43h
        mov bx, handle
        int 67h
        and ah, ah
        je ok
        call f_195A_02B7
    ok:
        mov ax, dx
    }
}
