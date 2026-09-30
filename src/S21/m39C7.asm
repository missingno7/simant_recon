; Video adapter identification (overlay section S21, code frame 39C7; linear 39C70-39E48).
;
; Genuine assembly: the routine is R. Wilton's VIDEO_ID probe ("Programmer's Guide to PC &
; PS/2 Video Systems", 1987) adapted to SimAnt.  Near procedures are reached through a
; table of (flag byte, near address) triples in DGROUP (lodsb / lodsw / call ax), return
; results in carry and in registers, use in/out/loop/loope/xlat/repne scasb, and the far
; entries save "push si; push di" (MSC always saves DI first, rule ASM-2) without a BP
; frame.  None of this is MSC 6.00 output (rules ASM-1, ASM-2).

; The adapter tables live in DGROUP 35D2-3601 (48 bytes: Device0/Device1, EGADisplays,
; DCCtable and TestSequence, whose triples hold the near offsets of FindPS2/FindEGA/FindCGA/
; FindMono).  They belong to this object, but the gate cannot yet bind near code offsets in
; a _DATA placement, so they are referenced here and stay unrecovered data debt.
_DATA           segment word public 'DATA'
                extrn   _g_35D2:word
                extrn   _g_35D6:byte
                extrn   _g_35DC:byte
                extrn   _g_35F6:byte
                extrn   _g_35F9:byte
                extrn   _g_35FC:byte
                extrn   _g_35FF:byte
_DATA           ends
DGROUP          group   _DATA

Device0         equ     _g_35D2
EGADisplays     equ     _g_35D6
DCCtable        equ     _g_35DC
TestSequence    equ     _g_35F6
EGAflag         equ     _g_35F9
CGAflag         equ     _g_35FC
Monoflag        equ     _g_35FF

VIDEO_TEXT      segment word public 'CODE'
                assume  cs:VIDEO_TEXT, ds:DGROUP

                public  _o21_39C7_0000
                public  _o21_39C7_003C
                public  _o21_39C7_008C
                public  _o21_39C7_00B8
                public  _o21_39C7_00C8
                public  _o21_39C7_010B
                public  _o21_39C7_0125
                public  _o21_39C7_0156
                public  _o21_39C7_016D

; int far o21_39C7_0000(void): probe all adapters, return Device0 (type | display << 8)
_o21_39C7_0000  proc    far
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
_o21_39C7_0000  endp

; PS/2 video BIOS: INT 10h function 1Ah returns the display combination code
FindPS2         proc    near
_o21_39C7_003C  label   near
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
_o21_39C7_008C  label   near
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
_o21_39C7_00B8  label   near
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
_o21_39C7_00C8  label   near
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
_o21_39C7_010B  label   near
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
_o21_39C7_0125  label   near
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
_o21_39C7_0156  label   near
                lea     bx, [di]
                cmp     byte ptr [bx], 0
                je      StoreDevice
                lea     bx, [di+2]
StoreDevice:    mov     [bx], ax
                ret
FoundDevice     endp

TandyName       db      'TANDY', 0
TandyNamePtr    dd      TandyName

; int far o21_39C7_016D(void): 1 if the BIOS segment F000h contains "TANDY"/"tandy"
_o21_39C7_016D  proc    far
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
_o21_39C7_016D  endp

VIDEO_TEXT      ends
                end
