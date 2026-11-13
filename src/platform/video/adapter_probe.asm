; Probes video adapters and identifies the active display subsystem. It checks BIOS services,
; CRTC ports and the Tandy ROM signature.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: overlay section 21 (S21); segment 39C7; complete original translation unit.
; Windows: none (DOS only), based on the platform-specific code or DOS release data.
; Build profile: masm510; /Mx.
;
; Genuine assembly: the routine is R. Wilton's VIDEO_ID probe ("Programmer's Guide to PC &
; PS/2 Video Systems", 1987) adapted to SimAnt.  Near procedures are reached through a
; table of (flag byte, near address) triples in DGROUP (lodsb / lodsw / call ax), return
; results in carry and in registers, use in/out/loop/loope/xlat/repne scasb, and the far
; entries save "push si; push di" (MSC always saves DI first, rule ASM-2) without a BP
; frame.  None of this is MSC 6.00 output (rules ASM-1, ASM-2).

DGROUP          group   _DATA

_DATA           segment word public 'DATA'
Device0         dw      0               ; subsystem type (low byte), display type (high byte)
Device1         dw      0
EGADisplays     db      2, 3, 1, 2, 3, 1        ; EGA switch setting -> display type
DCCtable        db      0, 0                    ; INT 10h AX=1A00h display combination codes
                db      1, 1
                db      2, 2
                db      0, 0
                db      3, 3
                db      3, 1
                db      0, 0
                db      5, 4
                db      5, 5
                db      0, 0
                db      4, 3
                db      4, 4
                db      4, 5
TestSequence    db      0
                dw      FindPS2
EGAflag         db      0
                dw      FindEGA
CGAflag         db      0
                dw      FindCGA
Monoflag        db      0
                dw      FindMono
_DATA           ends

VIDEO_TEXT      segment word public 'CODE'
                assume  cs:VIDEO_TEXT, ds:DGROUP

                public  _gfx_probe_display_adapters
                public  _gfx_probe_bios_display_codes
                public  _gfx_probe_ega_adapter
                public  _gfx_probe_cga_adapter
                public  _gfx_probe_mono_adapter
                public  _gfx_probe_crtc_readback
                public  _gfx_order_active_adapter_first
                public  _gfx_record_probed_adapter
                public  _gfx_bios_has_tandy_signature

; int far gfx_probe_display_adapters(void): probe all adapters, return Device0 (type | display << 8)
; Probe display adapters and return the active subsystem/display word.
_gfx_probe_display_adapters  proc    far
                push    si
                push    di
                mov     di, offset DGROUP:Device0
                xor     ax, ax
                mov     [di], ax
                mov     [di+2], ax
                mov     CGAflag, 1
                mov     EGAflag, 1
                mov     Monoflag, 1
                mov     TestSequence, 1
                mov     cx, 4
                mov     si, offset DGROUP:TestSequence
NextTest:       lodsb
                test    al, al
                lodsw
                jz      SkipTest
                push    si
                push    cx
                call    ax
                pop     cx
                pop     si
SkipTest:       loop    NextTest
                call    FindActive
                mov     ax, [di]
                pop     di
                pop     si
                ret
_gfx_probe_display_adapters  endp

; PS/2 video BIOS: INT 10h function 1Ah returns the display combination code
FindPS2         proc    near
; Translate BIOS display-combination codes into device records at DI.
_gfx_probe_bios_display_codes  label   near
                mov     ax, 1A00h
                int     10h
                cmp     al, 1Ah
                jne     PS2Done
                mov     cx, bx
                xor     bh, bh
                or      ch, ch
                jz      PS2Active
                mov     bl, ch
                add     bx, bx
                mov     ax, word ptr DCCtable[bx]
                mov     [di+2], ax
                mov     bl, cl
                xor     bh, bh
PS2Active:      add     bx, bx
                mov     ax, word ptr DCCtable[bx]
                mov     [di], ax
                mov     CGAflag, 0
                mov     EGAflag, 0
                mov     Monoflag, 0
                lea     bx, [di]
                cmp     byte ptr [bx], 1
                je      PS2Mono
                lea     bx, [di+2]
                cmp     byte ptr [bx], 1
                jne     PS2Done
PS2Mono:        mov     word ptr [bx], 0
                mov     Monoflag, 1
PS2Done:        ret
FindPS2         endp

; EGA BIOS: INT 10h function 12h, BL=10h returns the EGA configuration
FindEGA         proc    near
; Probe EGA BIOS configuration and record its display type.
_gfx_probe_ega_adapter  label   near
                mov     bl, 10h
                mov     ah, 12h
                int     10h
                cmp     bl, 10h
                je      EGADone
                mov     al, cl
                shr     al, 1
                mov     bx, offset DGROUP:EGADisplays
                xlat
                mov     ah, al
                mov     al, 3
                call    FoundDevice
                cmp     ah, 1
                je      EGAMono
                mov     CGAflag, 0
                jmp     short EGADone
EGAMono:        mov     Monoflag, 1
EGADone:        ret
FindEGA         endp

; CGA: a 6845 CRTC at port 3D4h
FindCGA         proc    near
; Record a CGA device when the 3D4h CRTC probe succeeds.
_gfx_probe_cga_adapter  label   near
                mov     dx, 3D4h
                call    Find6845
                jc      CGADone
                mov     al, 2
                mov     ah, 2
                call    FoundDevice
CGADone:        ret
FindCGA         endp

; MDA / Hercules: a 6845 CRTC at port 3B4h, then the vertical-sync bit of status port 3BAh
FindMono        proc    near
; Probe the monochrome CRTC and distinguish MDA/Hercules status patterns.
_gfx_probe_mono_adapter  label   near
                mov     dx, 3B4h
                call    Find6845
                jc      MonoDone
                mov     dl, 0BAh
                in      al, dx
                mov     ah, al
                and     ah, 80h
                mov     cx, 8000h
MonoWait:       in      al, dx
                and     al, 80h
                cmp     al, ah
                loope   MonoWait
                jne     Herc
                mov     al, 1
                mov     ah, 1
                call    FoundDevice
                jmp     short MonoDone
Herc:           in      al, dx
                mov     dl, al
                mov     ah, 3
                and     dl, 70h
                mov     al, 82h
                cmp     dl, 50h
                je      HercFound
                mov     ah, 1
                mov     al, 81h
                cmp     dl, 10h
                je      HercFound
                mov     al, 80h
HercFound:      call    FoundDevice
MonoDone:       ret
FindMono        endp

; DX = CRTC address port: carry set if no 6845 answers (cursor-low register read-back)
Find6845        proc    near
; Test CRTC register 0Fh at DX, restore it, and set carry on failure.
_gfx_probe_crtc_readback  label   near
                mov     al, 0Fh
                out     dx, al
                inc     dx
                in      al, dx
                mov     ah, al
                mov     al, 66h
                out     dx, al
                mov     cx, 300h
Wait6845:       loop    Wait6845
                in      al, dx
                xchg    ah, al
                out     dx, al
                cmp     ah, 66h
                je      Found6845
                stc
Found6845:      ret
Find6845        endp

; order Device0/Device1 so that Device0 is the active subsystem
FindActive      proc    near
; Order the two DI device words using the active BIOS video mode.
_gfx_order_active_adapter_first  label   near
                cmp     word ptr [di+2], 0
                je      ActiveDone
                cmp     byte ptr [di], 4
                jge     ActiveDone
                cmp     byte ptr [di+2], 4
                jge     ActiveDone
                mov     ah, 0Fh
                int     10h
                and     al, 7
                cmp     al, 7
                je      ActiveMono
                cmp     byte ptr [di+1], 1
                jne     ActiveDone
                jmp     short ActiveSwap
ActiveMono:     cmp     byte ptr [di+1], 1
                je      ActiveDone
ActiveSwap:     mov     ax, [di]
                xchg    ax, [di+2]
                mov     [di], ax
ActiveDone:     ret
FindActive      endp

; AX = subsystem/display: store it in the first free device word
FoundDevice     proc    near
; Store the subsystem/display word in AX in the first available device slot.
_gfx_record_probed_adapter  label   near
                lea     bx, [di]
                cmp     byte ptr [bx], 0
                je      StoreDevice
                lea     bx, [di+2]
StoreDevice:    mov     [bx], ax
                ret
FoundDevice     endp

TandyName       db      'TANDY', 0
TandyNamePtr    dd      TandyName

; int far gfx_bios_has_tandy_signature(void): 1 if the BIOS segment F000h contains "TANDY"/"tandy"
; Return whether the BIOS ROM contains a case variant of TANDY.
_gfx_bios_has_tandy_signature  proc    far
                push    ds
                push    si
                push    di
                mov     ax, 0F000h
                mov     es, ax
                xor     di, di
                mov     cx, 0FFFFh
                mov     al, 'T'
UpperNext:      repne scasb
                jcxz    TryLower
                cmp     word ptr es:[di], 'NA'
                je      UpperDY
                cmp     word ptr es:[di], 'na'
                jne     UpperNext
UpperDY:        cmp     word ptr es:[di+2], 'YD'
                je      UpperFound
                cmp     word ptr es:[di+2], 'yd'
                jne     UpperNext
UpperFound:     jmp     IsTandy
TryLower:       xor     di, di
                mov     al, 't'
                mov     cx, 0FFFFh
LowerNext:      repne scasb
                jcxz    NotTandy
                cmp     word ptr es:[di], 'NA'
                je      LowerDY
                cmp     word ptr es:[di], 'na'
                jne     LowerNext
LowerDY:        cmp     word ptr es:[di+2], 'YD'
                je      LowerFound
                cmp     word ptr es:[di+2], 'yd'
                jne     LowerNext
LowerFound:     jmp     IsTandy
NotTandy:       xor     ax, ax
                jmp     short TandyDone
IsTandy:        mov     ax, 1
TandyDone:      pop     di
                pop     si
                pop     ds
                ret
_gfx_bios_has_tandy_signature  endp

VIDEO_TEXT      ends
                end
