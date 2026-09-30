/* ASM-1b probe: prologue/epilogue MSC 6.00AX gives a function whose body is inline
   assembly using SI, DI and DS with a local frame (compare S00 module 35A6). */
void far blit(char far *src, char far *dst, int shift, int row)
{
    int w, h, n, a, b;
    _asm {
        push ds
        lds si, src
        les di, dst
        lodsw
        mov w, ax
        mov h, ax
        mov n, ax
        mov a, ax
        mov b, ax
        pop ds
    }
}
