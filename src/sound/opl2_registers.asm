; AdLib (YM3812 / OPL2) register access (root module, code frame 283E;
; linear 0x283EA-0x284A4).
;
; Genuine assembly (sound driver library): a register-called far procedure
; (f_283E_0020: AH = register, AL = value, DX = index port) with status-port
; delay loops (in al,dx / loop), C entry points that address their arguments
; through "add bp,6" and never restore SP, and a PIT channel-0 polling loop.
; MSC 6.00 emits none of these shapes (no register-argument far functions,
; no loop instruction, every BP frame of a C function with inline asm ends
; with mov sp,bp: rule ASM-1).

ADLIB_PORT      equ     388h

ADLIB_TEXT      segment word public 'CODE'
                assume  cs:ADLIB_TEXT

                public  _f_283E_000A
                public  _f_283E_0020
                public  _f_283E_0035

; void far f_283E_000A(char reg, char value): write one OPL2 register
_f_283E_000A    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                mov     dx, ADLIB_PORT
                mov     ah, [bp]
                mov     al, [bp+2]
                call    far ptr _f_283E_0020
                pop     bp
                ret
_f_283E_000A    endp

; register call: AH = OPL2 register, AL = value, DX = index port
_f_283E_0020    proc    far
                push    ax
                mov     al, ah
                out     dx, al
                mov     cx, 10
reg_delay:      in      al, dx
                loop    reg_delay
                inc     dx
                pop     ax
                out     dx, al
                dec     dx
                mov     cx, 40
data_delay:     in      al, dx
                loop    data_delay
                ret
_f_283E_0020    endp

; void far f_283E_0035(void): reset the OPL2 and wait about 2 ms (PIT channel 0)
_f_283E_0035    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                mov     dx, ADLIB_PORT
                mov     ax, 2021h
                call    _f_283E_0020
                mov     ax, 60F0h
                call    _f_283E_0020
                mov     ax, 80F0h
                call    _f_283E_0020
                mov     ax, 0C001h
                call    _f_283E_0020
                mov     ax, 0E000h
                call    _f_283E_0020
                mov     ax, 433Fh
                call    _f_283E_0020
                mov     ax, 0B001h
                call    _f_283E_0020
                mov     ax, 0A08Fh
                call    _f_283E_0020
                mov     ax, 0B02Eh
                call    _f_283E_0020
                cli
                mov     al, 0
                out     43h, al
                in      al, 40h
                mov     bl, al
                in      al, 40h
                mov     bh, al
wait_pit:       mov     al, 0
                out     43h, al
                in      al, 40h
                mov     cl, al
                in      al, 40h
                mov     ch, al
                neg     cx
                add     cx, bx
                cmp     cx, 952h
                jb      wait_pit
                mov     ax, 0B020h
                call    _f_283E_0020
                mov     ax, 0A000h
                call    _f_283E_0020
                sti
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_283E_0035    endp

ADLIB_TEXT      ends
                end
