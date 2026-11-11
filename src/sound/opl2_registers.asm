; Writes and resets AdLib OPL2 registers. It includes the status port delays and PIT based reset
; wait.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: resident code; segment 283E; complete original translation unit.
; Windows: none (DOS only), based on the platform-specific code or DOS release data.
; Build profile: masm510; /Mx.
;
; Genuine assembly (sound driver library): a register-called far procedure
; (snd_opl_write_regs: AH = register, AL = value, DX = index port) with status-port
; delay loops (in al,dx / loop), C entry points that address their arguments
; through "add bp,6" and never restore SP, and a PIT channel-0 polling loop.
; MSC 6.00 emits none of these shapes (no register-argument far functions,
; no loop instruction, every BP frame of a C function with inline asm ends
; with mov sp,bp: rule ASM-1).

ADLIB_PORT      equ     388h

ADLIB_TEXT      segment word public 'CODE'
                assume  cs:ADLIB_TEXT

                public  _snd_opl_write
                public  _snd_opl_write_regs
                public  _snd_opl_probe_tone

; void far snd_opl_write(char reg, char value): write one OPL2 register
_snd_opl_write    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                mov     dx, ADLIB_PORT
                mov     ah, [bp]
                mov     al, [bp+2]
                call    far ptr _snd_opl_write_regs
                pop     bp
                ret
_snd_opl_write    endp

; register call: AH = OPL2 register, AL = value, DX = index port
_snd_opl_write_regs    proc    far
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
_snd_opl_write_regs    endp

; void far snd_opl_probe_tone(void): reset the OPL2 and wait about 2 ms (PIT channel 0)
_snd_opl_probe_tone    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                mov     dx, ADLIB_PORT
                mov     ax, 2021h
                call    _snd_opl_write_regs
                mov     ax, 60F0h
                call    _snd_opl_write_regs
                mov     ax, 80F0h
                call    _snd_opl_write_regs
                mov     ax, 0C001h
                call    _snd_opl_write_regs
                mov     ax, 0E000h
                call    _snd_opl_write_regs
                mov     ax, 433Fh
                call    _snd_opl_write_regs
                mov     ax, 0B001h
                call    _snd_opl_write_regs
                mov     ax, 0A08Fh
                call    _snd_opl_write_regs
                mov     ax, 0B02Eh
                call    _snd_opl_write_regs
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
                call    _snd_opl_write_regs
                mov     ax, 0A000h
                call    _snd_opl_write_regs
                sti
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_snd_opl_probe_tone    endp

ADLIB_TEXT      ends
                end
