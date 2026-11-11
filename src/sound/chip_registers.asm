; Sound chip register interface with read-back check (root module, code frame
; 29BF; linear 0x29BF8-0x29D6A).
;
; Genuine assembly (sound driver library): near procedures that pass values
; in AL/AH/CX/DL and report errors in the carry flag, LOOP counters,
; "jmp $+2" I/O delays, C entry points that address their arguments through
; "add bp,6" and return with pop bp/retf (no mov sp,bp), unreferenced helper
; code (snd_regchip_init_channels).  MSC 6.00 produces none of these (rule ASM-1).

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
; candidate base ports probed by snd_regchip_detect
g_75DF          dw      220h, 240h, 280h, 2C0h
_DATA           ends

CHIP_TEXT       segment word public 'CODE'
                assume  cs:CHIP_TEXT, ds:DGROUP

                public  _snd_regchip_initialize
                public  _snd_regchip_reset_default
                public  _snd_regchip_init_channels
                public  _snd_regchip_reset
                public  _snd_regchip_fill_registers
                public  _snd_regchip_set_mode
                public  _snd_regchip_channel_write
                public  _snd_regchip_write
                public  _snd_regchip_write_checked
                public  _snd_regchip_detect
                public  _snd_regchip_probe_ports

; int far snd_regchip_initialize(int port): initialise the chip at PORT
_snd_regchip_initialize    proc    far
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
                call    _snd_regchip_reset_default
                mov     ax, 0EFFh
                call    _snd_regchip_write_checked
                mov     ax, 0FF0h
                call    _snd_regchip_write_checked
                push    ax
                mov     al, 0A0h
                call    _snd_regchip_set_mode
                pop     ax
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_snd_regchip_initialize    endp

_snd_regchip_reset_default    proc    near
                mov     al, 0F0h
                mov     g_75DE, al
                call    _snd_regchip_reset
                ret
_snd_regchip_reset_default    endp

; not referenced: DL -> registers 6, 7, 8
_snd_regchip_init_channels    proc    near
                mov     cx, 0
                mov     dl, 4
                call    _snd_regchip_channel_write
                inc     cx
                call    _snd_regchip_channel_write
                inc     cx
                call    _snd_regchip_channel_write
                ret
_snd_regchip_init_channels    endp

; reset: clear the shadow bytes and every register (CF set on a write failure)
_snd_regchip_reset    proc    near
                mov     bx, offset DGROUP:g_75D8
                mov     cx, 6
                mov     al, 0
clear_shadow:   mov     [bx], al
                inc     bx
                loop    clear_shadow
                push    ax
                mov     al, 0A0h
                call    _snd_regchip_set_mode
                pop     ax
                jb      reset_done
                mov     al, 0C0h
                mov     ah, 7
                call    _snd_regchip_write_checked
                mov     al, 0
                mov     ah, 0Eh
                call    _snd_regchip_write_checked
                mov     ah, 0
                mov     al, 0
                mov     cx, 0Fh
                call    _snd_regchip_fill_registers
                push    ax
                mov     al, 0B0h
                call    _snd_regchip_set_mode
                pop     ax
                mov     ah, 0
                mov     al, 0
                mov     cx, 0Ah
                call    _snd_regchip_fill_registers
                mov     al, 0
                mov     ah, 0Fh
                call    _snd_regchip_write_checked
                mov     al, 0
                call    _snd_regchip_set_mode
                mov     al, 0F8h
                mov     g_75D6, al
                mov     ah, 7
                call    _snd_regchip_write_checked
                mov     al, g_75DE
                mov     ah, 0Fh
                call    _snd_regchip_write_checked
reset_done:     ret
_snd_regchip_reset    endp

; write AL to CX consecutive registers starting at AH
_snd_regchip_fill_registers    proc    near
                call    _snd_regchip_write_checked
                jb      fill_done
                inc     ah
                loop    _snd_regchip_fill_registers
fill_done:      ret
_snd_regchip_fill_registers    endp

; register 0Dh := AL | g_75DB (AL remembered in g_75D7)
_snd_regchip_set_mode    proc    near
                mov     g_75D7, al
                or      al, g_75DB
                mov     ah, 0Dh
                call    _snd_regchip_write_checked
                ret
_snd_regchip_set_mode    endp

; register 6 + CL := DL, bracketed by mode 0B0h / 0A0h
_snd_regchip_channel_write    proc    near
                mov     al, dl
                mov     ah, 6
                add     ah, cl
                push    ax
                mov     al, 0B0h
                call    _snd_regchip_set_mode
                pop     ax
                call    _snd_regchip_write_checked
                push    ax
                mov     al, 0A0h
                call    _snd_regchip_set_mode
                pop     ax
                ret
_snd_regchip_channel_write    endp

; void far snd_regchip_write(int reg, int value)
_snd_regchip_write    proc    far
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
                call    _snd_regchip_write_checked
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_snd_regchip_write    endp

; write AL to register AH and read it back; CF = 1 after ten failed tries
_snd_regchip_write_checked    proc    near
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
_snd_regchip_write_checked    endp

; int far snd_regchip_detect(void): probe the candidate ports, return the base found or 0
_snd_regchip_detect    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    ds
                mov     ax, DGROUP
                mov     ds, ax
                call    _snd_regchip_probe_ports
                pop     ds
                pop     bp
                ret
_snd_regchip_detect    endp

_snd_regchip_probe_ports    proc    near
                push    si
                mov     si, 0
probe_next:     mov     ax, g_75DF[si]
                mov     bx, 0
set_ports:      mov     g_75B2[bx], ax
                inc     ax
                add     bx, 2
                cmp     bx, 0Ch
                jne     set_ports
                call    _snd_regchip_reset_default
                jae     probe_found
                add     si, 2
                cmp     si, 8
                jne     probe_next
                xor     ax, ax
                jmp     short probe_done
probe_found:    mov     ax, g_75DF[si]
probe_done:     pop     si
                ret
_snd_regchip_probe_ports    endp

CHIP_TEXT       ends
                end
