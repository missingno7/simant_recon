; Mouse, keyboard and timer services: INT 33h mouse driver interface, mouse event
; queue, hot-box (screen region) lists, cursor drawing, and the INT 08h / INT 09h /
; INT 15h(4Fh) handlers.  Root module, code frame 1B73, linear 1B736-1C62B
; (the object starts at frame offset 0006, after module 1B4E).
;
; Genuine assembly (rules ASM-1, ASM-2): interrupt handlers that end in iret or chain
; with jmp dword ptr cs:[old vector] and switch to private stacks in DGROUP, variables
; and an iret stub in the code segment (the stub is installed as the INT 33h vector by
; writing the IVT directly), "in al,60h", near procs returning flags (stc/clc), far
; procs entered with push cs / call near, frames saved "push si; push di", dead code
; after unconditional jumps (081D, 089A) and a NOP-aligned entry label (0D4B).
; DGROUP data (queues, stacks, tables) is referenced by address name; the module's own
; _DATA contribution is not reconstructed here.

_DATA	segment word public 'DATA'
	extrn	_fd_55B3_3DE6:byte
	extrn	_fd_55B3_3DE8:byte
	extrn	_g_21A4:byte
	extrn	_g_3D10:byte
	extrn	_g_3D14:byte
	extrn	_g_3D18:byte
	extrn	_g_3D1C:byte
	extrn	_g_3DB2:byte
	extrn	_g_3DB4:byte
	extrn	_g_3DD2:byte
	extrn	_g_3DD4:byte
	extrn	_g_3DE0:byte
	extrn	_g_3DE2:byte
	extrn	_g_3DE4:byte
	extrn	_g_432A:byte
	extrn	_g_432B:byte
	extrn	_g_432C:byte
	extrn	_g_432E:byte
	extrn	_g_4331:byte
	extrn	_g_4332:byte
	extrn	_g_4333:byte
	extrn	_g_4334:byte
	extrn	_g_4336:byte
	extrn	_g_4338:byte
	extrn	_g_433A:byte
	extrn	_g_433C:byte
	extrn	_g_433E:byte
	extrn	_g_4340:byte
	extrn	_g_4342:byte
	extrn	_g_4344:byte
	extrn	_g_4346:byte
	extrn	_g_4348:byte
	extrn	_g_434A:byte
	extrn	_g_434E:byte
	extrn	_g_4352:byte
	extrn	_g_4356:byte
	extrn	_g_435A:byte
	extrn	_g_4362:byte
	extrn	_g_4363:byte
	extrn	_g_4364:byte
	extrn	_g_4365:byte
	extrn	_g_4366:byte
	extrn	_g_4368:byte
	extrn	_g_4369:byte
	extrn	_g_4D8E:byte
	extrn	_g_4D92:byte
	extrn	_g_4D96:byte
	extrn	_g_4D9A:byte
	extrn	_g_4D9E:byte
	extrn	_g_4DA0:byte
	extrn	_g_4DA2:byte
	extrn	_g_4DA4:byte
	extrn	_g_4DA5:byte
	extrn	_g_53B0:byte
	extrn	_g_53B2:byte
	extrn	_g_53B4:byte
	extrn	_g_53B6:byte
	extrn	_g_53B8:byte
	extrn	_g_53BA:byte
	extrn	_g_53BC:byte
	extrn	_g_53BD:byte
	extrn	_g_53CD:byte
	extrn	_g_5484:byte
	extrn	_g_549A:byte
	extrn	_g_5AAC:byte
	extrn	_g_5AAE:byte
	extrn	_g_5FF0:byte
	extrn	_g_5FF2:byte
	extrn	_g_5FF4:byte
	extrn	_g_5FF6:byte
	extrn	_g_5FF8:byte
	extrn	_g_5FF9:byte
	extrn	_g_5FFA:byte
	extrn	_g_5FFE:byte
	extrn	_g_9120:byte
	extrn	_g_9122:byte
	extrn	_g_9124:byte
	extrn	_g_9128:byte
	extrn	_g_9148:byte
	extrn	_g_9160:byte
	extrn	_g_9164:byte
	extrn	_g_9168:byte
	extrn	_g_9184:byte
	extrn	_g_4FAA:byte
	extrn	_g_51AC:byte
	extrn	_g_53AE:byte
	extrn	_g_544D:byte
	extrn	_g_54A0:byte
	extrn	_g_54B0:byte
	extrn	_g_53BE:byte
	extrn	_g_5A9C:byte
	extrn	_g_5460:byte
_DATA	ends
DGROUP	group	_DATA

	extrn	_Punt:far
	extrn	_fd_5071_0728:byte
	extrn	_f_1B4E_003B:far
	extrn	_f_1B4E_005E:far
	extrn	_f_277D_000B:far
	extrn	_puts:far

MOUSE_TEXT	segment word public 'CODE'
	assume	cs:MOUSE_TEXT, ds:DGROUP

	public	_TickCount
	public	_f_1B73_0024
	public	_f_1B73_0025
	public	_f_1B73_0046
	public	_f_1B73_00D9
	public	_f_1B73_0122
	public	_f_1B73_0196
	public	_f_1B73_01CB
	public	_f_1B73_01D5
	public	_f_1B73_01E1
	public	_f_1B73_0218
	public	_f_1B73_0228
	public	_f_1B73_0235
	public	_f_1B73_02A9
	public	_f_1B73_030F
	public	_f_1B73_032A
	public	_f_1B73_032E
	public	_f_1B73_036E
	public	_f_1B73_03EE
	public	_f_1B73_0445
	public	_f_1B73_04BB
	public	_f_1B73_050E
	public	_f_1B73_050F
	public	_f_1B73_0510
	public	_f_1B73_0511
	public	_f_1B73_0518
	public	_f_1B73_051F
	public	_f_1B73_065A
	public	_f_1B73_06E3
	public	_f_1B73_0747
	public	_f_1B73_09E9
	public	_f_1B73_09F7
	public	_f_1B73_09FF
	public	_f_1B73_0A1B
	public	_f_1B73_0A30
	public	_f_1B73_0A40
	public	_f_1B73_0A6C
	public	_f_1B73_0A89
	public	_f_1B73_0AA3
	public	_f_1B73_0AC3
	public	_f_1B73_0B00
	public	_f_1B73_0B5B
	public	_f_1B73_0BC5
	public	_f_1B73_0BFF
	public	_f_1B73_0C42
	public	_f_1B73_0C80
	public	_f_1B73_0CB3
	public	_f_1B73_0CEF
	public	_f_1B73_0D4C
	public	_f_1B73_0DA4
	public	_f_1B73_0EEE

; code-segment variables (addressed cs:, shared with the interrupt handlers)
tmr_countdown	dw	0		; INT 08h: decremented by 5 per tick, floor 0
mickey_mode	db	0		; set when the driver reports version 7.00: handler works in mickeys
		db	0
old_int08	dd	0
tick_phase	dw	0		; ticks since the last keyboard cursor step
kbd_hook_on	db	1		; keyboard handlers active
tick_count_on	db	1		; TickCount advances
tick_count	dd	0		; returned by TickCount
kbd_busy	db	0		; INT 09h/15h reentrancy
		db	0
mouse_busy	db	0		; event handler reentrancy
timer_busy	db	0		; INT 08h reentrancy
shift_state	db	0		; bit 0/1: right/left shift (from the scan codes), bit 7: button bit
last_shift	db	0
old_int09	dd	0
old_int15	dd	0

; INT 33h vector target installed when no mouse driver is loaded
_f_1B73_0024	proc	far
	iret
_f_1B73_0024	endp

; remove the INT 33h iret stub from the IVT if it is still installed
_f_1B73_0025	proc	far
	xor ax, ax
	mov es, ax
	cmp word ptr es:[0CCh], offset _f_1B73_0024
	jne L0045
	cmp word ptr es:[0CEh], MOUSE_TEXT
	jne L0045
	xor ax, ax
	mov word ptr es:[0CEh], ax
	mov word ptr es:[0CCh], ax
L0045:
	retf
_f_1B73_0025	endp

; mouse init: detect the INT 33h driver (installing the iret stub if the vector is empty), set range, centre the cursor
_f_1B73_0046	proc	far
	mov ax, 24h
	xor bx, bx
	int 33h
	cmp bx, 700h
	je L005A
	test byte ptr _g_432A, 0FFh
	je L006A
L005A:
	mov byte ptr cs:mickey_mode, 1
	xor ax, ax
	mov es, ax
	mov byte ptr es:[449h], 50h
L006A:
	xor ax, ax
	mov es, ax
	mov ax, word ptr es:[0CCh]
	or ax, word ptr es:[0CEh]
	jne L0087
	mov ax, MOUSE_TEXT
	mov word ptr es:[0CEh], ax
	mov ax, offset _f_1B73_0024
	mov word ptr es:[0CCh], ax
L0087:
	xor ax, ax
	int 33h
	and ax, ax
	je L00BA
	xor cx, cx
	mov dx, word ptr _g_3DB4
	sub dx, 4
	mov ax, 8
	int 33h
	xor cx, cx
	mov dx, word ptr _g_3DB2
	sub dx, 4
	mov ax, 7
	int 33h
	xor cx, cx
	mov ax, 24h
	int 33h
	mov al, 2
	and ch, ch
	je L00BA
	mov al, ch
L00BA:
	mov byte ptr _g_4DA4, al
	push ax
	mov ax, word ptr _g_3DB4
	shr ax, 1
	mov word ptr _g_9122, ax
	mov ax, word ptr _g_3DB2
	shr ax, 1
	mov word ptr _g_9124, ax
	call near ptr _f_1B73_09F7
	pop ax
	mov word ptr _g_435A, 1
	retf
_f_1B73_0046	endp

_f_1B73_00D9	proc	far
	push di
	inc word ptr _g_4352
	jne L00E4
	inc word ptr _g_4352+2
L00E4:
	mov byte ptr _g_4332, 0
	mov al, byte ptr _g_4365
	and al, al
	jne L0120
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	push ds
	lds di, dword ptr _g_549A
	mov ax, 0FFFFh
	xor bh, bh
	call near ptr _f_1B73_0CEF
	pop ds
	mov bx, di
	je L010C
	xor bx, bx
L010C:
	mov word ptr _g_4DA5, bx
	mov al, 1
	pushf
	call near ptr _f_1B73_0122
	inc byte ptr _g_4365
	popf
	mov byte ptr _g_4331, 0
L0120:
	pop di
	retf
_f_1B73_00D9	endp

; redraw the mouse cursor through the display driver (AL = 1 show / 2 hide)
_f_1B73_0122	proc	near
	inc byte ptr _g_4333
	push di
	lea di, _g_5AAC
	push word ptr [di]
	push word ptr [di+2]
	push word ptr _fd_55B3_3DE6
	push word ptr _fd_55B3_3DE8
	mov cx, seg _g_5A9C
	mov word ptr [di+2], cx
	mov cx, offset DGROUP:_g_5A9C
	mov word ptr [di], cx
	push word ptr _g_3DD2
	push word ptr _g_3DE4
	push word ptr _g_3DE2
	push word ptr _g_3DE0
	push ax
	call dword ptr _g_9168
	pop ax
	mov bx, word ptr _g_4DA5
	and bx, bx
	jne L0169
	push ax
	call far ptr _f_1B73_0D4C
	jmp short L0173
L0169:
	mov dx, seg _fd_5071_0728
	mov es, dx
	push ax
	call dword ptr es:[bx+8]
L0173:
	pop ax
	call dword ptr _g_9128
	add sp, 6
	call dword ptr _g_9184
	pop ax
	pop word ptr _fd_55B3_3DE8
	pop word ptr _fd_55B3_3DE6
	pop word ptr _g_5AAE
	pop word ptr _g_5AAC
	pop di
	dec byte ptr _g_4333
	retn
_f_1B73_0122	endp

_f_1B73_0196	proc	far
	mov al, 1
	mov byte ptr _g_4332, al
	test byte ptr _g_4365, 0FFh
	je L01CA
	jg L01B3
	push ds
	mov ax, offset DGROUP:_g_53BE
	push ax
	call far ptr _puts
	call far ptr _Punt
L01B3:
	inc word ptr _g_434E
	jne L01BD
	inc word ptr _g_434E+2
L01BD:
	pushf
	cli
	mov ax, 2
	call near ptr _f_1B73_0122
	dec byte ptr _g_4365
	popf
L01CA:
	retf
_f_1B73_0196	endp

_f_1B73_01CB	proc	far
	inc byte ptr _g_3DD4
	call far ptr _f_1B73_0196
	retf
_f_1B73_01CB	endp

_f_1B73_01D5	proc	far
	dec byte ptr _g_3DD4
	jne L01E0
	call far ptr _f_1B73_00D9
L01E0:
	retf
_f_1B73_01D5	endp

_f_1B73_01E1	proc	far
	push bp
	mov bp, sp
	pushf
	cli
	les bx, dword ptr [bp+0Ah]
	mov word ptr _g_4D8E, bx
	mov word ptr _g_4D8E+2, es
	mov ax, word ptr es:[bx]
	mov word ptr _g_4348, ax
	mov ax, word ptr es:[bx+2]
	mov word ptr _g_434A, ax
	les bx, dword ptr [bp+6]
	mov word ptr _g_4D92, bx
	mov word ptr _g_4D92+2, es
	mov ax, word ptr _g_435A
	and ax, ax
	je L0215
	mov byte ptr _g_4331, 1
L0215:
	popf
	pop bp
	retf
_f_1B73_01E1	endp

_f_1B73_0218	proc	far
	push bp
	mov bp, sp
	mov cx, word ptr [bp+6]
	mov dx, word ptr [bp+8]
	mov ax, 0Fh
	int 33h
	pop bp
	retf
_f_1B73_0218	endp

_f_1B73_0228	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov ax, 13h
	int 33h
	pop bp
	retf
_f_1B73_0228	endp

; install the event handler (INT 33h/0Ch) and the INT 15h, INT 09h and INT 08h handlers
_f_1B73_0235	proc	far
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[417h]
	and al, 20h
	mov byte ptr _g_433E, al
	mov ax, 1Ch
	mov bx, 2
	int 33h
	mov ax, 0Ch
	mov cx, 7Fh
	push cs
	pop es
	lea dx, ds:_f_1B73_03EE
	int 33h
	push ds
	push cs
	pop ds
	mov ax, 3515h
	int 21h
	mov word ptr cs:old_int15, bx
	mov word ptr cs:old_int15+2, es
	mov ax, 2515h
	lea dx, ds:_f_1B73_065A
	int 21h
	mov ax, 3509h
	int 21h
	mov word ptr cs:old_int09, bx
	mov word ptr cs:old_int09+2, es
	mov ax, 2509h
	lea dx, ds:_f_1B73_06E3
	int 21h
	mov ax, 3508h
	int 21h
	mov word ptr cs:old_int08, bx
	mov word ptr cs:old_int08+2, es
	mov ax, 2508h
	lea dx, ds:_f_1B73_051F
	int 21h
	pop ds
	inc byte ptr _g_53BC
	retf
_f_1B73_0235	endp

; restore the INT 15h/09h/08h vectors and remove the mouse event handler
_f_1B73_02A9	proc	far
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[417h]
	and al, 0DFh
	or al, byte ptr _g_433E
	mov byte ptr es:[417h], al
	cmp byte ptr _g_53BC, 0
	je L0301
	dec byte ptr _g_53BC
	push ds
	mov dx, word ptr cs:old_int15
	mov ds, word ptr cs:old_int15+2
	mov ax, ds
	or ax, dx
	je L02DC
	mov ax, 2515h
	int 21h
L02DC:
	mov dx, word ptr cs:old_int09
	mov ds, word ptr cs:old_int09+2
	mov ax, ds
	or ax, dx
	je L02F1
	mov ax, 2509h
	int 21h
L02F1:
	mov ax, 2508h
	mov dx, word ptr cs:old_int08
	mov ds, word ptr cs:old_int08+2
	int 21h
	pop ds
L0301:
	mov ax, 0Ch
	xor cx, cx
	int 33h
	mov word ptr _g_435A, 0
	retf
_f_1B73_02A9	endp

_f_1B73_030F	proc	far
	push bp
	mov bp, sp
	mov es, word ptr [bp+8]
	mov bx, word ptr [bp+6]
	mov ax, word ptr [bp+0Ah]
	mov cx, word ptr [bp+0Ch]
	mov dx, word ptr [bp+0Eh]
	call far ptr _f_1B73_036E
	xor ax, ax
	pop bp
	retf
_f_1B73_030F	endp

_f_1B73_032A	proc	far
	mov ax, word ptr _g_5FF2
	retf
_f_1B73_032A	endp

; dequeue one 16-byte input event into *dest; returns the remaining count
_f_1B73_032E	proc	far
	push bp
	mov bp, sp
	push si
	push di
	mov ax, word ptr _g_5FF2
	dec ax
	js L036A
	mov word ptr _g_5FF2, ax
	mov bx, word ptr _g_5FF6
	mov si, bx
	inc bx
	cmp word ptr _g_5FF0, bx
	jg L034B
	xor bx, bx
L034B:
	pushf
	cli
	mov word ptr _g_5FF6, bx
	mov bx, si
	mov si, word ptr _g_5FFE
	shl bx, 1
	shl bx, 1
	shl bx, 1
	shl bx, 1
	add si, bx
	les di, dword ptr [bp+6]
	mov cx, 8
	rep movsw
	popf
L036A:
	pop di
	pop si
	pop bp
	retf
_f_1B73_032E	endp

; enqueue an input event (AX, CX, DX, ES:BX) with shift state and BIOS tick time
_f_1B73_036E	proc	far
	pushf
	cli
	push ds
	push si
	push bx
	mov bx, DGROUP
	mov ds, bx
	mov bx, word ptr _g_5FF4
	mov si, bx
	inc bx
	cmp word ptr _g_5FF0, bx
	jg L0387
	xor bx, bx
L0387:
	cmp word ptr _g_5FF6, bx
	je L03E7
	mov word ptr _g_5FF4, bx
	mov bx, si
	inc word ptr _g_5FF2
	mov si, word ptr _g_5FFE
	shl bx, 1
	shl bx, 1
	shl bx, 1
	shl bx, 1
	add si, bx
	pop bx
	mov word ptr [si+6], ax
	mov word ptr [si+8], cx
	mov word ptr [si+0Ah], dx
	mov word ptr [si+0Ch], bx
	mov word ptr [si+0Eh], es
	push ax
	push es
	mov ax, 40h
	mov es, ax
	mov ax, word ptr es:[17h]
	mov bx, word ptr es:[6Ch]
	pop es
	test byte ptr cs:shift_state, 80h
	je L03D1
	or ax, 1
L03D1:
	mov word ptr [si+2], ax
	mov word ptr [si+4], bx
	pop ax
	test ah, 0Ah
	je L03E3
	and byte ptr cs:shift_state, 7Fh
L03E3:
	pop si
	pop ds
	popf
	retf
L03E7:
	pop bx
	pop si
	pop ds
	popf
	retf
L03EC:
	popf
	retf
_f_1B73_036E	endp

; INT 33h user event handler (mickey mode converts relative motion); falls into 0445
_f_1B73_03EE	proc	far
	test byte ptr cs:mickey_mode, 0FFh
	je _f_1B73_0445
	push ds
	push ax
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	sar si, 1
	sar di, 1
	mov ax, si
	sub ax, word ptr _g_432C
	mov word ptr _g_432C, si
	add cx, ax
	jns L041B
	xor cx, cx
L041B:
	cmp cx, word ptr _g_3DB2
	jl L0426
	mov cx, word ptr _g_3DB2
	dec cx
L0426:
	mov ax, di
	sub ax, word ptr _g_432E
	mov word ptr _g_432E, di
	add dx, ax
	jns L0436
	xor dx, bx
L0436:
	cmp dx, word ptr _g_3DB4
	jl L0441
	mov dx, word ptr _g_3DB4
	dec dx
L0441:
	pop di
	pop si
	pop ax
	pop ds
_f_1B73_03EE	endp

; mouse event: update the button/position state, hot-box tracking and the cursor
_f_1B73_0445	proc	far
	pushf
	cli
	test byte ptr cs:mouse_busy, 0FFh
	jne L03EC
	inc byte ptr cs:mouse_busy
	popf
	push si
	push di
	push ds
	mov ah, al
	mov al, bl
	mov bx, DGROUP
	mov ds, bx
	mov word ptr _g_9120, ax
	mov word ptr _g_9122, cx
	mov word ptr _g_9124, dx
	mov word ptr _g_53B4, ss
	mov word ptr _g_53B6, sp
	mov ss, bx
	mov sp, offset DGROUP:_g_4FAA
	cld
	mov al, byte ptr _g_4365
	and al, al
	jg L0488
L0481:
	mov al, 1
	mov byte ptr _g_4331, al
	jmp short L049D
L0488:
	mov al, byte ptr _g_3DD4
	or al, byte ptr cs:timer_busy
	or al, byte ptr _g_4333
	jne L0481
	push es
	call far ptr _f_1B73_04BB
	pop es
L049D:
	mov ax, word ptr _g_9120
	test byte ptr _g_5FF9, ah
	je L04AA
	call word ptr _g_5FFA
L04AA:
	mov ss, word ptr _g_53B4
	mov sp, word ptr _g_53B6
	pop ds
	pop di
	pop si
	dec byte ptr cs:mouse_busy
	retf
_f_1B73_0445	endp

_f_1B73_04BB	proc	far
	push di
	inc word ptr _g_4356
	jne L04C6
	inc word ptr _g_4356+2
L04C6:
	test byte ptr _g_4365, 0FFh
	jle L0502
	mov bx, word ptr _g_4DA5
	mov al, 2
	call near ptr _f_1B73_0122
	push ds
	push es
	mov ax, word ptr _g_9120
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	lds di, dword ptr _g_549A
	xor bh, bh
	call near ptr _f_1B73_0CEF
	pop ds
	pop es
	mov bx, di
	je L04F4
	xor bx, bx
L04F4:
	mov word ptr _g_4DA5, bx
	mov al, 1
	call near ptr _f_1B73_0122
	mov byte ptr _g_4331, 0
L0502:
	pop di
	retf
_f_1B73_04BB	endp

; long TickCount(void): timer ticks counted by the INT 08h handler
_TickCount	proc	far
	mov ax, word ptr cs:tick_count
	mov dx, word ptr cs:tick_count+2
	retf
_TickCount	endp

_f_1B73_050E	proc	far
	retf
_f_1B73_050E	endp

_f_1B73_050F	proc	far
	retf
_f_1B73_050F	endp

_f_1B73_0510	proc	far
	retf
_f_1B73_0510	endp

_f_1B73_0511	proc	far
	mov byte ptr cs:tick_count_on, 0
	retf
_f_1B73_0511	endp

_f_1B73_0518	proc	far
	mov byte ptr cs:tick_count_on, 1
	retf
_f_1B73_0518	endp

; INT 08h handler: tick counter, cursor keys repeat and cursor movement, chains to the old vector
_f_1B73_051F	proc	far
	sub word ptr cs:tmr_countdown, 5
	jae L052E
	mov word ptr cs:tmr_countdown, 0
L052E:
	cld
	test byte ptr cs:tick_count_on, 1
	je L0543
	inc word ptr cs:tick_count
	jne L0543
	inc word ptr cs:tick_count+2
L0543:
	inc word ptr cs:tick_phase
	inc byte ptr cs:timer_busy
	cmp byte ptr cs:timer_busy, 1
	je L0558
	jmp near ptr L064A
L0558:
	push bx
	push ds
	mov bx, DGROUP
	mov ds, bx
	mov word ptr _g_53B8, ss
	mov word ptr _g_53BA, sp
	mov ss, bx
	mov sp, offset DGROUP:_g_51AC
	pushf
	sti
	push ax
	push es
	push cx
	push dx
	test byte ptr cs:mouse_busy, 0FFh
	je L057D
	jmp near ptr L063B
L057D:
	test byte ptr _g_4365, 0FFh
	jle L059F
	test byte ptr _g_3DD4, 0FFh
	jne L05CB
	test byte ptr _g_4333, 0FFh
	jne L05CB
	shr byte ptr _g_4331, 1
	jae L05CB
	call far ptr _f_1B73_04BB
	jmp short L05CB
L059F:
	shr byte ptr _g_4332, 1
	jne L05CB
	mov byte ptr _g_4332, 1
	test byte ptr _g_4331, 0FFh
	jne L05B8
	test byte ptr _g_4366, 0FFh
	jne L05CB
L05B8:
	test byte ptr _g_3DD4, 0FFh
	jne L05CB
	test byte ptr _g_4333, 0FFh
	jne L05CB
	call far ptr _f_1B73_00D9
L05CB:
	mov bl, byte ptr _g_4362
	add bl, byte ptr _g_4368
	mov bh, byte ptr _g_4363
	add bh, byte ptr _g_4369
	and bx, bx
	je L063B
	jb L0600
	mov ax, word ptr cs:tick_phase
	cmp ax, 4
	je L05F4
	cmp ax, 0Ah
	je L05F4
	cmp ax, 1Ch
	jne L05F8
L05F4:
	inc byte ptr _g_4364
L05F8:
	mov cl, byte ptr _g_4364
	shl bh, cl
	shl bl, cl
L0600:
	mov al, bl
	cbw
	add ax, word ptr _g_9122
	cmp ax, 0
	jge L060E
	xor ax, ax
L060E:
	mov cx, word ptr _g_3DB2
	cmp ax, cx
	jl L0619
	mov ax, cx
	dec ax
L0619:
	mov word ptr _g_9122, ax
	mov al, bh
	cbw
	add ax, word ptr _g_9124
	cmp ax, 0
	jge L062A
	xor ax, ax
L062A:
	mov cx, word ptr _g_3DB4
	cmp ax, cx
	jl L0635
	mov ax, cx
	dec ax
L0635:
	mov word ptr _g_9124, ax
	call near ptr _f_1B73_09F7
L063B:
	pop dx
	pop cx
	pop es
	pop ax
	popf
	mov ss, word ptr _g_53B8
	mov sp, word ptr _g_53BA
	pop ds
	pop bx
L064A:
	dec byte ptr cs:timer_busy
	jmp dword ptr cs:old_int08
L0654:
	popf
L0655:
	jmp dword ptr cs:old_int15
_f_1B73_051F	endp

; INT 15h handler: AH=4Fh keyboard intercept feeds the scan code processor
_f_1B73_065A	proc	far
	jae L0655
	pushf
	cmp ah, 4Fh
	jne L0654
	cli
	test byte ptr cs:kbd_hook_on, 0FFh
	je L0654
	test byte ptr cs:kbd_busy, 0FFh
	jne L0654
	inc byte ptr cs:kbd_busy
	popf
	push ax
	push dx
	push ds
	pushf
	cld
	mov dx, DGROUP
	mov ds, dx
	mov word ptr _g_53B2, ss
	mov word ptr _g_53B0, sp
	mov ss, dx
	mov sp, offset DGROUP:_g_53AE
	mov dl, byte ptr _g_432B
	xor dl, dl
	jne L06B1
	call near ptr _f_1B73_0747
L069B:
	mov ss, word ptr _g_53B2
	mov sp, word ptr _g_53B0
	pop ax
	pop ds
	pop dx
	pop ax
	dec byte ptr cs:kbd_busy
	jmp dword ptr cs:old_int15
L06B1:
	push es
	xor dx, dx
	mov byte ptr _g_432B, dl
	mov es, dx
	mov dx, word ptr cs:old_int09
	mov word ptr es:[24h], dx
	mov dx, word ptr cs:old_int09+2
	mov word ptr es:[26h], dx
	xor dx, dx
	mov word ptr cs:old_int09+2, dx
	mov word ptr cs:old_int09, dx
	pop es
	jmp L069B
L06DD:
	popf
	jmp dword ptr cs:old_int09
_f_1B73_065A	endp

; INT 09h handler: reads port 60h and feeds the scan code processor, then chains
_f_1B73_06E3	proc	far
	pushf
	cli
	test byte ptr cs:kbd_hook_on, 0FFh
	je L06DD
	test byte ptr cs:kbd_busy, 0FFh
	jne L06DD
	inc byte ptr cs:kbd_busy
	popf
	push ax
	cld
	in al, 60h
	mov ah, al
	push dx
	push ds
	mov dx, DGROUP
	mov ds, dx
	mov word ptr _g_53B2, ss
	mov word ptr _g_53B0, sp
	mov ss, dx
	mov sp, offset DGROUP:_g_53AE
	mov byte ptr _g_432B, 1
	call near ptr _f_1B73_0747
	mov ss, word ptr _g_53B2
	mov sp, word ptr _g_53B0
	pop ds
	pop dx
	cli
	pushf
	call dword ptr cs:old_int09
	jb L073F
	push es
	mov ax, 40h
	mov es, ax
	mov ax, word ptr es:[1Ah]
	mov word ptr es:[1Ch], ax
	pop es
L073F:
	pop ax
	dec byte ptr cs:kbd_busy
	iret
_f_1B73_06E3	endp

kbd_last_scan	db	0		; previous scan code (E0h prefix test)


; scan code processor: shift/E0 tracking, key state table, key events, cursor-key mouse emulation
_f_1B73_0747	proc	near
	push es
	push di
	push bx
	push cx
	push si
	push ax
	mov bx, ds
	mov es, bx
	mov ah, al
	and al, 7Fh
	xor ah, al
	mov bl, al
	xor bh, bh
	cmp byte ptr cs:kbd_last_scan, 0E0h
	je L07A1
	mov cl, 2
	cmp al, 2Ah
	je L076F
	cmp al, 36h
	jne L07A1
	shr cl, 1
L076F:
	push bx
	xor bx, bx
	mov es, bx
	pop bx
	and ah, ah
	jns L0782
	not cl
	and byte ptr cs:shift_state, cl
	jmp short L0787
L0782:
	or byte ptr cs:shift_state, cl
L0787:
	and byte ptr cs:shift_state, 3
	mov cl, byte ptr cs:shift_state
	cmp cl, byte ptr cs:last_shift
	je L079E
	mov byte ptr cs:last_shift, cl
L079E:
	jmp L07F7
L07A1:
	cmp byte ptr [bx+_g_53CD], ah
	je L07F8
	mov byte ptr [bx+_g_53CD], ah
	rol ah, 1
	jb L07C0
	push es
	push ax
	mov bh, 0FAh
	mov bl, al
	xor ax, ax
	mov es, ax
	call far ptr _f_1B73_036E
	pop ax
	pop es
L07C0:
	xor ah, 1
	mov cx, 13h
	mov di, offset DGROUP:_g_544D
	mov bx, di
	repne scasb
	stc
	jcxz L07F8
	xor cx, cx
	mov es, cx
	sub di, bx
	mov bx, di
	mov cl, byte ptr es:[417h]
	cmp bx, 4
	jg L07ED
	test cl, 0Ch
	je L07ED
	test ah, 1
	stc
	jne L07F8
L07ED:
	shl bx, 1
	jmp word ptr [bx+_g_5460-2]
L07F3:
	stc
	cmc
	jmp short L07F8
L07F7:
	stc
L07F8:
	pop ax
	pop si
	pop cx
	pop bx
	pop di
	pop es
	mov byte ptr cs:kbd_last_scan, al
	retn
	test cl, 0Fh
	je L0811
	xor ah, ah
	mov byte ptr cs:shift_state, ah
	jmp short L0818
L0811:
	ror ah, 1
	xor byte ptr cs:shift_state, ah
L0818:
	call near ptr _f_1B73_09F7
	jmp L07F7
	mov al, 10h
	jmp short L088A
	test cl, 4
	je L07F7
	test cl, 0Bh
	jne L07F7
	test ah, 1
	je L07F7
	mov al, 1
	jmp short L088A
	test cl, 0Bh
	jne L07F7
	test ah, 1
	je L07F7
	test cl, 4
	je L0847
	mov al, 2
	jmp short L088A
L0847:
	mov al, 6
	jmp short L088A
	test ah, 1
	je L07F7
	test cl, 0Bh
	jne L07F7
	test cl, 4
	je L085E
	mov al, 3
	jmp short L088A
L085E:
	mov al, 7
	jmp short L088A
	test cl, 4
	je L07F7
	test cl, 0Bh
	jne L07F7
	test ah, 1
	je L07F7
	mov al, 4
	jmp short L088A
L0875:
	jmp L07F7
	test cl, 4
	je L0875
	test cl, 0Bh
	jne L0875
	test ah, 1
	je L0875
	mov al, 5
	jmp short L088A
L088A:
	ror ah, 1
	or al, ah
	mov bh, 0F0h
	mov bl, al
	call far ptr _f_1B73_036E
	jmp L07F7
	mov bh, 0FAh
	ror ah, 1
	or al, ah
	mov bl, al
	call far ptr _f_1B73_036E
	jmp L07F7
	nop
	and ah, ah
	je L08D3
	mov bx, word ptr _g_3DB4
	mov cl, 7
	shr bx, cl
	inc bx
	neg bl
	mov bh, bl
	xor bl, bl
	jmp short L0915
	and ah, ah
	je L08D3
	mov bx, word ptr _g_3DB4
	mov cl, 7
	shr bx, cl
	inc bx
	mov bh, bl
	xor bl, bl
	jmp short L0915
L08D3:
	mov byte ptr _g_4363, ah
	jmp short L0929
L08D9:
	mov byte ptr _g_4362, ah
	jmp short L0929
	and ah, ah
	je L08D9
	mov bx, word ptr _g_3DB2
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	or bx, 1
	jmp short L0915
	and ah, ah
	je L08D9
	mov bx, word ptr _g_3DB2
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	shr bx, 1
	or bx, 1
	neg bl
L0915:
	mov al, bl
	and al, al
	je L091F
	cbw
	mov byte ptr _g_4362, al
L091F:
	mov al, bh
	and al, al
	je L0929
	cbw
	mov byte ptr _g_4363, al
L0929:
	call near ptr L09D9
	jmp L07F3
	mov bx, word ptr _g_3DB4
	shr bx, 1
	mov word ptr _g_9124, bx
	mov bx, word ptr _g_3DB2
	shr bx, 1
	mov word ptr _g_9122, bx
	jmp near ptr L09E3
	and ah, ah
	je L09AC
	xor ax, ax
	mov bx, word ptr _g_9122
	cmp bx, 8
	jbe L0958
	mov ax, 6
L0958:
	mov word ptr _g_9122, ax
	jmp near ptr L09E3
	and ah, ah
	je L09AC
	mov ax, word ptr _g_3DB2
	dec ax
	mov bx, ax
	sub bx, 8
	cmp bx, word ptr _g_9122
	jb L0974
	sub ax, 6
L0974:
	mov word ptr _g_9122, ax
	jmp short L09E3
	and ah, ah
	je L09AC
	xor ax, ax
	mov bx, word ptr _g_9124
	cmp bx, 8
	jbe L098B
	mov ax, 6
L098B:
	mov word ptr _g_9124, ax
	jmp short L09E3
	and ah, ah
	je L09AC
	mov ax, word ptr _g_3DB4
	dec ax
	mov bx, ax
	sub bx, 8
	cmp bx, word ptr _g_9124
	jbe L09A6
	sub ax, 6
L09A6:
	mov word ptr _g_9124, ax
	call near ptr _f_1B73_09F7
L09AC:
	jmp L07F3
	mov al, byte ptr _g_9120
	and al, 0FEh
	or al, ah
	shl ah, 1
	mov bl, al
	and ah, ah
	jne _f_1B73_0A1B
	mov ah, 4
	jmp short _f_1B73_0A1B
	mov al, byte ptr _g_9120
	and al, 0FDh
	shl ah, 1
	or al, ah
	shl ah, 1
	shl ah, 1
	mov bl, al
	and ah, ah
	jne _f_1B73_0A1B
	mov ah, 10h
	jmp short _f_1B73_0A1B
L09D9:
	xor ax, ax
	mov word ptr cs:tick_phase, ax
	mov byte ptr _g_4364, al
	retn
L09E3:
	call near ptr _f_1B73_09F7
	jmp L07F3
_f_1B73_0747	endp

_f_1B73_09E9	proc	far
	push bp
	mov bp, sp
	mov cx, word ptr [bp+6]
	mov dx, word ptr [bp+8]
	call near ptr _f_1B73_09FF
	pop bp
	retf
_f_1B73_09E9	endp

_f_1B73_09F7	proc	near
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
_f_1B73_09F7	endp

_f_1B73_09FF	proc	near
	mov bl, byte ptr _g_9120
	mov al, 1
	mov ah, byte ptr _g_4DA4
	and ah, ah
	je L0A16
	push ax
	push bx
	mov ax, 4
	int 33h
	pop bx
	pop ax
L0A16:
	push cs
	call near ptr _f_1B73_0445
	retn
_f_1B73_09FF	endp

_f_1B73_0A1B	proc	near
	call near ptr L0A21
	jmp L07F3
L0A21:
	mov al, ah
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	push cs
	call near ptr _f_1B73_0445
	retn
_f_1B73_0A1B	endp

_f_1B73_0A30	proc	far
	push bp
	mov bp, sp
	mov bx, word ptr [bp+6]
	mov al, byte ptr [bx+_g_53CD]
	xor al, 80h
	xor ah, ah
	pop bp
	retf
_f_1B73_0A30	endp

_f_1B73_0A40	proc	far
	call far ptr _f_1B73_0A6C
	xor bx, bx
	mov byte ptr cs:kbd_hook_on, bl
	mov byte ptr _g_53BD, bl
	mov ax, 3
	int 33h
	mov word ptr _g_9120, bx
	xor al, al
	mov byte ptr cs:shift_state, al
	mov byte ptr _g_4362, al
	mov byte ptr _g_4363, al
	mov byte ptr _g_4368, al
	mov byte ptr _g_4369, al
	retf
_f_1B73_0A40	endp

_f_1B73_0A6C	proc	far
	push di
	mov ax, ds
	mov es, ax
	mov di, offset DGROUP:_g_53CD
	mov ax, 8080h
	mov cx, 40h
	rep stosw
	mov byte ptr cs:kbd_hook_on, 1
	mov byte ptr _g_53BD, 1
	pop di
	retf
_f_1B73_0A6C	endp

_f_1B73_0A89	proc	near
	mov cx, word ptr es:[di]
	add di, 2
	jmp short L0A9B
L0A91:
	cmp ax, word ptr es:[di+0Ch]
	je L0AA1
	dec cx
	add di, 12h
L0A9B:
	and cx, cx
	jne L0A91
	stc
	retn
L0AA1:
	clc
	retn
_f_1B73_0A89	endp

_f_1B73_0AA3	proc	far
	les bx, dword ptr _g_5484
	xor ax, ax
	mov word ptr es:[bx], ax
	les bx, dword ptr _g_5484+6
	mov word ptr es:[bx], ax
	mov byte ptr _g_5FF8, al
	lea ax, ds:_f_1B73_0CB3
	mov word ptr _g_5FFA, ax
	mov al, 1Fh
	mov byte ptr _g_5FF9, al
	retf
_f_1B73_0AA3	endp

_f_1B73_0AC3	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pushf
	push ds
	cli
	les di, dword ptr [bp+0Ah]
	mov bx, word ptr es:[di]
	cmp bx, word ptr es:[di-2]
	jge L0AF1
	inc word ptr es:[di]
	add di, 2
	mov al, 12h
	mul bl
	mov cx, 9
	add di, ax
	lds si, dword ptr [bp+6]
	rep movsw
	pop ds
	popf
	pop di
	pop si
	pop bp
	retf
L0AF1:
	popf
	mov ax, offset DGROUP:_g_54A0
	push ax
	call far ptr _puts
	call far ptr _Punt
_f_1B73_0AC3	endp

_f_1B73_0B00	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+0Ah]
	cmp di, offset _fd_5071_0728
	jne L0B17
	call far ptr _f_1B73_0196
	les di, dword ptr [bp+0Ah]
L0B17:
	pushf
	cli
	mov bx, word ptr es:[di]
	cmp bx, word ptr es:[di-2]
	jge L0AF1
	inc word ptr es:[di]
	add di, 2
	push di
	and bx, bx
	je L0B46
	mov al, 12h
	mul bl
	mov cx, ax
	mov ax, es
	mov ds, ax
	add di, cx
	add di, 10h
	mov si, di
	sub si, 12h
	std
	shr cx, 1
	rep movsw
L0B46:
	cld
	lds si, dword ptr [bp+6]
	pop di
	mov cx, 9
	rep movsw
	popf
	pop ds
	call far ptr _f_1B73_00D9
	pop di
	pop si
	pop bp
	retf
_f_1B73_0B00	endp

_f_1B73_0B5B	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	mov word ptr [bp-2], 0
	les di, dword ptr [bp+8]
	cmp di, offset _fd_5071_0728
	jne L0B84
	test byte ptr _g_4365, 0FFh
	jle L0B84
	call far ptr _f_1B73_0196
	inc word ptr [bp-2]
	les di, dword ptr [bp+8]
L0B84:
	pushf
	cli
	mov ax, word ptr [bp+6]
	mov si, di
	call near ptr _f_1B73_0A89
	jb L0BB0
	mov cx, es
	mov ds, cx
	dec word ptr [si]
	mov bx, word ptr [si]
	add si, 2
	mov al, 12h
	mul bl
	add ax, si
	sub ax, di
	je L0BB0
	mov cx, ax
	shr cx, 1
	mov si, di
	add si, 12h
	rep movsw
L0BB0:
	popf
	sti
	pop ds
	test word ptr [bp-2], 0FFh
	je L0BBF
	call far ptr _f_1B73_00D9
L0BBF:
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_f_1B73_0B5B	endp

_f_1B73_0BC5	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov ax, word ptr [bp+6]
	les di, dword ptr [bp+8]
	call near ptr _f_1B73_0A89
	jb L0BF8
	mov ax, 1
	mov bx, word ptr _g_9122
	cmp bx, word ptr es:[di]
	jl L0BF8
	cmp bx, word ptr es:[di+4]
	jg L0BF8
	mov bx, word ptr _g_9124
	cmp bx, word ptr es:[di+2]
	jl L0BF8
	cmp bx, word ptr es:[di+6]
	jle L0BFA
L0BF8:
	xor ax, ax
L0BFA:
	pop ds
	pop di
	pop si
	pop bp
	retf
_f_1B73_0BC5	endp

_f_1B73_0BFF	proc	far
	push si
	push di
	push ds
	les di, dword ptr _g_5484+12
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	mov bl, byte ptr es:[di]
	and bl, bl
	je L0C36
	add di, 2
L0C18:
	cmp cx, word ptr es:[di]
	jl L0C2F
	cmp cx, word ptr es:[di+4]
	jg L0C2F
	cmp dx, word ptr es:[di+2]
	jl L0C2F
	cmp dx, word ptr es:[di+6]
	jl L0C3A
L0C2F:
	add di, 12h
	dec bl
	jne L0C18
L0C36:
	xor ax, ax
	jmp short L0C3E
L0C3A:
	mov ax, word ptr es:[di+0Ch]
L0C3E:
	pop ds
	pop di
	pop si
	retf
_f_1B73_0BFF	endp

_f_1B73_0C42	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov ax, word ptr [bp+6]
	les di, dword ptr [bp+8]
	call near ptr _f_1B73_0A89
	jb L0C79
	mov ax, word ptr es:[di]
	mov bx, word ptr es:[di+2]
	mov cx, word ptr es:[di+4]
	mov dx, word ptr es:[di+6]
	les di, dword ptr [bp+0Ch]
	mov word ptr es:[di], ax
	mov word ptr es:[di+2], bx
	mov word ptr es:[di+4], cx
	mov word ptr es:[di+6], dx
	mov ax, 1
	jmp short L0C7B
L0C79:
	xor ax, ax
L0C7B:
	pop ds
	pop di
	pop si
	pop bp
	retf
_f_1B73_0C42	endp

_f_1B73_0C80	proc	far
	push bp
	mov bp, sp
	push di
	push si
	mov ax, word ptr [bp+6]
	les di, dword ptr _g_5484+12
	mov si, di
	call near ptr _f_1B73_0A89
	jb L0CAF
	mov ax, word ptr es:[di+2]
	add ax, word ptr es:[di+6]
	shr ax, 1
	push ax
	mov bx, word ptr es:[di]
	add bx, word ptr es:[di+4]
	shr bx, 1
	push bx
	call far ptr _f_1B73_09E9
	pop bx
	pop bx
L0CAF:
	pop si
	pop di
	pop bp
	retf
_f_1B73_0C80	endp

_f_1B73_0CB3	proc	near
	push es
	push ds
	push si
	push di
	mov si, DGROUP
	mov es, si
	mov si, offset DGROUP:_g_5484
	mov ax, word ptr es:_g_9120
	mov cx, word ptr es:_g_9122
	mov dx, word ptr es:_g_9124
L0CCD:
	lds di, dword ptr es:[si]
	mov bx, word ptr es:[si+4]
	and bl, ah
	je L0CE1
	push es
	mov bh, bl
	call near ptr _f_1B73_0CEF
	pop es
	je L0CEA
L0CE1:
	add si, 6
	cmp word ptr es:[si], 0
	jne L0CCD
L0CEA:
	pop di
	pop si
	pop ds
	pop es
	retn
_f_1B73_0CB3	endp

_f_1B73_0CEF	proc	near
	mov bl, byte ptr [di]
	and bl, bl
	je L0D47
	add di, 2
L0CF8:
	test word ptr [di+10h], ax
	je L0D40
	cmp cx, word ptr [di]
	jl L0D40
	cmp cx, word ptr [di+4]
	jg L0D40
	cmp dx, word ptr [di+2]
	jl L0D40
	cmp dx, word ptr [di+6]
	jg L0D40
	and bh, bh
	je L0D49
	push ds
	push bx
	mov bx, ds
	mov es, bx
	push dx
	push cx
	push ax
	push word ptr [di+0Eh]
	push word ptr [di+0Ch]
	mov ax, DGROUP
	mov ds, ax
	call dword ptr es:[di+8]
	add sp, 0Ah
	and ax, ax
	mov ax, word ptr _g_9120
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	pop bx
	pop ds
	je L0D47
L0D40:
	add di, 12h
	dec bl
	jne L0CF8
L0D47:
	inc bl
L0D49:
	retn
_f_1B73_0CEF	endp

cursor_mode	db	0FFh		; current cursor mode (1 or 2)

	public	_f_1B73_0D4B
_f_1B73_0D4B	label	far
	even
_f_1B73_0D4C	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	and al, 3
	jne L0D58
	jmp short L0D93
L0D58:
	cmp byte ptr cs:cursor_mode, al
	je L0D95
	mov byte ptr cs:cursor_mode, al
	dec al
	jne L0D6C
	call near ptr _f_1B73_0DA4
	jmp short L0D93
L0D6C:
	dec al
	jne L0D93
	push word ptr _g_21A4
	mov word ptr _g_21A4, 1
	push ds
	push word ptr _g_4DA2
	push word ptr _g_4342
	push word ptr _g_4340
	call far ptr _f_1B4E_003B
	add sp, 8
	pop word ptr _g_21A4
L0D93:
	pop bp
	retf
L0D95:
	push ds
	mov ax, offset DGROUP:_g_54B0
	push ax
	call far ptr _f_277D_000B
	add sp, 4
	jmp L0D93
_f_1B73_0D4C	endp

_f_1B73_0DA4	proc	near
	les bx, dword ptr _g_4D8E
	mov word ptr _g_4D96, bx
	mov word ptr _g_4D96+2, es
	mov ax, word ptr es:[bx]
	mov word ptr _g_4DA0, ax
	mov ax, word ptr es:[bx+2]
	mov word ptr _g_4D9E, ax
	les bx, dword ptr _g_4D92
	mov word ptr _g_4D9A, bx
	mov word ptr _g_4D9A+2, es
	les bx, dword ptr _g_3D1C
	mov ax, es
	and ax, ax
	je L0E29
	mov ax, word ptr _g_4DA5
	and ax, ax
	jne L0E29
	les bx, dword ptr es:[bx]
	test word ptr _g_4334, 0FFh
	je L0E29
	mov cx, word ptr _g_9122
	mov dx, word ptr _g_9124
	cmp cx, word ptr _g_4336
	jl L0E29
	cmp cx, word ptr _g_433A
	jg L0E29
	cmp dx, word ptr _g_4338
	jl L0E29
	cmp dx, word ptr _g_433C
	jg L0E29
	mov word ptr _g_4D96, bx
	mov word ptr _g_4D96+2, es
	mov ax, word ptr es:[bx]
	mov word ptr _g_4DA0, ax
	mov ax, word ptr es:[bx+2]
	mov word ptr _g_4D9E, ax
	les bx, dword ptr _g_3D18
	les bx, dword ptr es:[bx]
	mov word ptr _g_4D9A, bx
	mov word ptr _g_4D9A+2, es
L0E29:
	test byte ptr cs:shift_state, 0FFh
	je L0E62
	les bx, dword ptr _g_3D14
	mov ax, es
	and ax, ax
	je L0E62
	les bx, dword ptr es:[bx]
	mov word ptr _g_4D96, bx
	mov word ptr _g_4D96+2, es
	mov ax, word ptr es:[bx]
	mov word ptr _g_4DA0, ax
	mov ax, word ptr es:[bx+2]
	mov word ptr _g_4D9E, ax
	les bx, dword ptr _g_3D10
	les bx, dword ptr es:[bx]
	mov word ptr _g_4D9A, bx
	mov word ptr _g_4D9A+2, es
L0E62:
	push word ptr _g_21A4
	mov word ptr _g_21A4, 1
	push si
	push di
	mov di, word ptr _g_9122
	push di
	and di, -8
	push ds
	push word ptr _g_4DA2
	mov si, word ptr _g_9124
	mov word ptr _g_4340, di
	mov word ptr _g_4342, si
	mov ax, si
	mov bx, di
	add ax, word ptr _g_4D9E
	add bx, word ptr _g_4DA0
	add bx, 7
	mov word ptr _g_4346, bx
	mov word ptr _g_4344, ax
	push ax
	push bx
	push si
	push di
	call dword ptr _g_9148
	add sp, 0Ch
	pop di
	xor ax, ax
	push ax
	push ax
	mov ax, 0FF0Fh
	push ax
	call dword ptr _g_9128
	add sp, 6
	call dword ptr _g_9164
	xor ax, ax
	mov word ptr _g_21A4, ax
	les ax, dword ptr _g_4D96
	push es
	push ax
	push si
	push di
	call far ptr _f_1B4E_005E
	add sp, 8
	call dword ptr _g_9160
	les ax, dword ptr _g_4D9A
	push es
	push ax
	push si
	push di
	call far ptr _f_1B4E_003B
	add sp, 8
	pop di
	pop si
	pop word ptr _g_21A4
	xor ax, ax
	retn
_f_1B73_0DA4	endp

_f_1B73_0EEE	proc	far
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[417h]
	xor ah, ah
	and ax, 10h
	retf
_f_1B73_0EEE	endp

MOUSE_TEXT	ends
	end
