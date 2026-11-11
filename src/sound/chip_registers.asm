; Sound chip register interface with read-back check (root module, code frame
; 29BF; linear 0x29BF8-0x29D6A).
;
; Genuine assembly (sound driver library): near procedures that pass values
; in AL/AH/CX/DL and report errors in the carry flag, LOOP counters,
; "jmp $+2" I/O delays, C entry points that address their arguments through
; "add bp,6" and return with pop bp/retf (no mov sp,bp), unreferenced helper
; code (f_29BF_0048).  MSC 6.00 produces none of these (rule ASM-1).

DGROUP          group   _DATA

_DATA           segment word public 'DATA'
; index/data port pairs; entry 0 = the probed base port, entry 1 = base + 1
g_75B2          dw      220h
g_75B4          dw      221h
                dw      4 dup (0)
                dw      12 dup (0)
g_75D6          db      0FFh
g_75D7          db      0
g_75D8          db      3 dup (0)
g_75DB          db      0
                db      2 dup (0)
g_75DE          db      0F0h
; candidate base ports probed by f_29BF_0139
g_75DF          dw      220h, 240h, 280h, 2C0h
_DATA           ends

CHIP_TEXT       segment word public 'CODE'
                assume  cs:CHIP_TEXT, ds:DGROUP

                public  _f_29BF_0008
                public  _f_29BF_003F
                public  _f_29BF_0048
                public  _f_29BF_0059
                public  _f_29BF_00B7
                public  _f_29BF_00C1
                public  _f_29BF_00CE
                public  _f_29BF_00E6
                public  _f_29BF_0108
                public  _f_29BF_0139
                public  _f_29BF_014B

; int far f_29BF_0008(int port): initialise the chip at PORT
_f_29BF_0008    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                mov     ax, DGROUP
                mov     ds, ax
                mov     ax, [bp]
                mov     g_75B2, ax
                add     ax, 1
                mov     g_75B4, ax
                call    _f_29BF_003F
                mov     ax, 0EFFh
                call    _f_29BF_0108
                mov     ax, 0FF0h
                call    _f_29BF_0108
                push    ax
                mov     al, 0A0h
                call    _f_29BF_00C1
                pop     ax
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_29BF_0008    endp

_f_29BF_003F    proc    near
                mov     al, 0F0h
                mov     g_75DE, al
                call    _f_29BF_0059
                ret
_f_29BF_003F    endp

; not referenced: DL -> registers 6, 7, 8
_f_29BF_0048    proc    near
                mov     cx, 0
                mov     dl, 4
                call    _f_29BF_00CE
                inc     cx
                call    _f_29BF_00CE
                inc     cx
                call    _f_29BF_00CE
                ret
_f_29BF_0048    endp

; reset: clear the shadow bytes and every register (CF set on a write failure)
_f_29BF_0059    proc    near
                mov     bx, offset DGROUP:g_75D8
                mov     cx, 6
                mov     al, 0
clear_shadow:   mov     [bx], al
                inc     bx
                loop    clear_shadow
                push    ax
                mov     al, 0A0h
                call    _f_29BF_00C1
                pop     ax
                jb      reset_done
                mov     al, 0C0h
                mov     ah, 7
                call    _f_29BF_0108
                mov     al, 0
                mov     ah, 0Eh
                call    _f_29BF_0108
                mov     ah, 0
                mov     al, 0
                mov     cx, 0Fh
                call    _f_29BF_00B7
                push    ax
                mov     al, 0B0h
                call    _f_29BF_00C1
                pop     ax
                mov     ah, 0
                mov     al, 0
                mov     cx, 0Ah
                call    _f_29BF_00B7
                mov     al, 0
                mov     ah, 0Fh
                call    _f_29BF_0108
                mov     al, 0
                call    _f_29BF_00C1
                mov     al, 0F8h
                mov     g_75D6, al
                mov     ah, 7
                call    _f_29BF_0108
                mov     al, g_75DE
                mov     ah, 0Fh
                call    _f_29BF_0108
reset_done:     ret
_f_29BF_0059    endp

; write AL to CX consecutive registers starting at AH
_f_29BF_00B7    proc    near
                call    _f_29BF_0108
                jb      fill_done
                inc     ah
                loop    _f_29BF_00B7
fill_done:      ret
_f_29BF_00B7    endp

; register 0Dh := AL | g_75DB (AL remembered in g_75D7)
_f_29BF_00C1    proc    near
                mov     g_75D7, al
                or      al, g_75DB
                mov     ah, 0Dh
                call    _f_29BF_0108
                ret
_f_29BF_00C1    endp

; register 6 + CL := DL, bracketed by mode 0B0h / 0A0h
_f_29BF_00CE    proc    near
                mov     al, dl
                mov     ah, 6
                add     ah, cl
                push    ax
                mov     al, 0B0h
                call    _f_29BF_00C1
                pop     ax
                call    _f_29BF_0108
                push    ax
                mov     al, 0A0h
                call    _f_29BF_00C1
                pop     ax
                ret
_f_29BF_00CE    endp

; void far f_29BF_00E6(int reg, int value)
_f_29BF_00E6    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                mov     ax, DGROUP
                mov     ds, ax
                mov     ax, [bp+2]
                mov     bx, [bp]
                xor     ah, ah
                mov     ah, bl
                call    _f_29BF_0108
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_29BF_00E6    endp

; write AL to register AH and read it back; CF = 1 after ten failed tries
_f_29BF_0108    proc    near
                push    ax
                push    bx
                push    cx
                push    dx
                mov     cx, 10
                xchg    al, ah
                mov     bl, al
write_try:      mov     dx, g_75B2
                out     dx, al
                jmp     short $+2
                mov     al, ah
                mov     dx, g_75B4
                out     dx, al
                jmp     short $+2
                mov     bh, al
                in      al, dx
                jmp     short $+2
                cmp     al, bh
                je      write_ok
                mov     al, bl
                loop    write_try
                stc
                jmp     short write_done
write_ok:       clc
write_done:     pop     dx
                pop     cx
                pop     bx
                pop     ax
                ret
_f_29BF_0108    endp

; int far f_29BF_0139(void): probe the candidate ports, return the base found or 0
_f_29BF_0139    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    ds
                mov     ax, DGROUP
                mov     ds, ax
                call    _f_29BF_014B
                pop     ds
                pop     bp
                ret
_f_29BF_0139    endp

_f_29BF_014B    proc    near
                push    si
                mov     si, 0
probe_next:     mov     ax, g_75DF[si]
                mov     bx, 0
set_ports:      mov     g_75B2[bx], ax
                inc     ax
                add     bx, 2
                cmp     bx, 0Ch
                jne     set_ports
                call    _f_29BF_003F
                jae     probe_found
                add     si, 2
                cmp     si, 8
                jne     probe_next
                xor     ax, ax
                jmp     short probe_done
probe_found:    mov     ax, g_75DF[si]
probe_done:     pop     si
                ret
_f_29BF_014B    endp

CHIP_TEXT       ends
                end
