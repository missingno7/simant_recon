; Root module 1F58: BIOS tick count, byte swap copy, keyboard polling and Ctrl-Break vector hook.
; Root code frame 1F58, linear 1F586-1F668.
; Genuine assembly: BIOS data area and interrupt-vector access through ES=0, int 16h,
; cli/sti around the vector swap, xchg with memory, frameless procs (rules ASM-1, ASM-2).

_DATA	segment word public 'DATA'
	extrn	_g_53BD:byte
_g_5A2A		dw	0		; pending key (scan code in AH, 80h = pushed back)
_g_5A2C		dw	0		; second pending key
_g_5A2E		dw	0		; saved INT 23h vector (offset, segment)
_g_5A30		dw	0
_DATA	ends
DGROUP	group	_DATA

	extrn	_atexit:far

KBD_TEXT	segment word public 'CODE'
	assume	cs:KBD_TEXT, ds:DGROUP

	public	_f_1F58_0006
	public	_f_1F58_0014
	public	_f_1F58_0017
	public	_f_1F58_0038
	public	_f_1F58_005A
	public	_f_1F58_007F
	public	_f_1F58_0090
	public	_f_1F58_00A1
	public	_f_1F58_00B8

_f_1F58_0006	proc	far
	xor ax, ax
	mov es, ax
	mov ax, word ptr es:[46Ch]
	mov dx, word ptr es:[46Eh]
	retf
_f_1F58_0006	endp

_f_1F58_0014	proc	far
	xor ax, ax
	retf
_f_1F58_0014	endp

_f_1F58_0017	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	push di
	mov cx, word ptr [bp+0Eh]
	and cx, cx
	je L0033
	les di, dword ptr [bp+6]
	lds si, dword ptr [bp+0Ah]
L002A:
	mov al, byte ptr es:[di]
	xchg byte ptr [si], al
	stosb
	inc si
	loop L002A
L0033:
	pop di
	pop si
	pop ds
	pop bp
	retf
_f_1F58_0017	endp

_f_1F58_0038	proc	far
	mov ax, word ptr _g_5A2A
	and ax, ax
	jne L0047
	inc ah
	int 16h
	jne L0047
	xor ax, ax
L0047:
	cmp byte ptr _g_53BD, 0
	je L0059
	xor bx, bx
	mov es, bx
	and word ptr es:[417h], not NumLockState
L0059:
	retf
_f_1F58_0038	endp

_f_1F58_005A	proc	far
	mov ax, word ptr _g_5A2A
	and ax, ax
	jne L0072
	xor ah, ah
	int 16h
	and al, al
	jne L0070
	mov al, ah
	mov word ptr _g_5A2A, ax
	xor al, al
L0070:
	cbw
	retf
L0072:
	xor ah, ah
	xor cx, cx
	xchg word ptr _g_5A2C, cx
	mov word ptr _g_5A2A, cx
	retf
_f_1F58_005A	endp

_f_1F58_007F	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	mov ah, 80h
	xchg word ptr _g_5A2A, ax
	mov word ptr _g_5A2C, ax
	pop bp
	retf
_f_1F58_007F	endp

_f_1F58_0090	proc	far
	call far ptr _f_1F58_005A
	and ax, ax
	jne L00A0
	call far ptr _f_1F58_005A
	mov ah, 8
L00A0:
	retf
_f_1F58_0090	endp

_f_1F58_00A1	proc	far
	cli
	xor ax, ax
	mov es, ax
	mov ax, word ptr _g_5A2E
	mov dx, word ptr _g_5A30
	mov word ptr es:[8Ch], ax
	mov word ptr es:[8Eh], dx
	sti
	retf
_f_1F58_00A1	endp

_f_1F58_00B8	proc	far
	push bp
	mov bp, sp
	cli
	les bx, dword ptr [bp+6]
	mov dx, es
	xor ax, ax
	mov es, ax
	xchg word ptr es:[8Ch], bx
	xchg word ptr es:[8Eh], dx
	mov word ptr _g_5A2E, bx
	mov word ptr _g_5A30, dx
	push cs
	assume	ds:KBD_TEXT
	lea bx, _f_1F58_00A1
	assume	ds:DGROUP
	push bx
	call far ptr _atexit
	add sp, 4
	sti
	pop bp
	retf
_f_1F58_00B8	endp

KBD_TEXT	ends

NumLockState	equ	20h		; BIOS keyboard flag byte 0040:0017, bit 5

	end
