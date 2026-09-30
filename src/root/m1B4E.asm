; Root module 1B4E: video BIOS and bitmap/text entry points (pen colour byte, palette, text draw, mode set).
; Root code frame 1B4E, linear 1B4EC-1B736.
; Genuine assembly: frameless register procs (xchg/stosw loops, rep movsw with DS swapped through ES),
; video BIOS int 10h wrappers, a fold table in the code segment read with cs:, push si; push di and
; push ds; push di saves (MSC saves DI first, rule ASM-2), pop bp without mov sp,bp (ASM-1).

_DATA	segment word public 'DATA'
	extrn	_g_914C:byte
	extrn	_g_9154:byte
	extrn	_g_9128:byte
	public	_g_3D20, _g_3DA0, _g_3DA2, _g_3DA4, _g_3DA8, _g_3DAA, _g_3DAC, _g_3DAE
	public	_g_3DB0, _g_3DB2, _g_3DB4, _g_3DB6, _g_3DC1, _g_3DCA, _g_3DD2, _g_3DD4
	public	_g_3DD6, _g_3DD8, _g_3DDA, _g_3DDC, _g_3DDE, _g_3DE0, _g_3DE1, _g_3DE2
	public	_g_3DE3, _g_3DE4, _g_3DE5, _fd_55B3_3DE6, _fd_55B3_3DE8, _g_3DEA, _g_3DEC
	public	_g_3DED, _g_3DEE, _g_3DEF, _g_3DF1, _g_3DF2, _g_3DF4, _g_3DF8, _g_3DFC
	public	_g_41C0, _g_4220
_g_3D20		db	128 dup (0)	; scratch bitmap row buffer
_g_3DA0		dw	0		; text pen x, y
_g_3DA2		dw	0
_g_3DA4		dd	0		; font objects
_g_3DA8		dw	0
_g_3DAA		dw	0
_g_3DAC		dw	0		; screen bitmap (DGROUP:0 until the driver sets it)
_g_3DAE		dw	DGROUP
_g_3DB0		dw	0A000h		; video segment
_g_3DB2		dw	640		; screen width, height, bytes per row
_g_3DB4		dw	350
_g_3DB6		dw	80
		db	9 dup (0)
_g_3DC1		db	0FFh, 7Fh, 3Fh, 1Fh, 0Fh, 07h, 03h, 01h, 00h	; left edge masks
_g_3DCA		db	80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh, 0FFh	; right edge masks
_g_3DD2		dw	0
_g_3DD4		dw	0
_g_3DD6		dw	0		; current font bitmap (far pointer)
_g_3DD8		dw	0
_g_3DDA		dw	0
_g_3DDC		dw	0		; character cell height, width
_g_3DDE		dw	8
_g_3DE0		db	0Fh		; pen colour
_g_3DE1		db	0
_g_3DE2		db	0
_g_3DE3		db	0
_g_3DE4		db	0		; fill pattern
_g_3DE5		db	0
_fd_55B3_3DE6	dw	0
_fd_55B3_3DE8	dw	0
_g_3DEA		dw	0
_g_3DEC		db	0
_g_3DED		db	0
_g_3DEE		db	0
_g_3DEF		db	0
		db	0
_g_3DF1		db	0
_g_3DF2		dw	0
_g_3DF4		dd	_f_1B4E_000C	; empty driver entry
_g_3DF8		dd	_g_9128		; driver entry table (25 far pointers)
_g_3DFC		db	964 dup (0)
_g_41C0		db	0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15	; colour map
		; 16-byte fill patterns
		db	55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh
		db	0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h
		db	16 dup (0FFh)
		db	16 dup (0)
		db	10h, 10h, 04h, 04h, 10h, 10h, 04h, 04h, 10h, 10h, 04h, 04h, 10h, 10h, 04h, 04h
_g_4220		db	16 dup (0)
		db	44h, 44h, 22h, 22h, 11h, 11h, 88h, 88h, 44h, 44h, 22h, 22h, 11h, 11h, 88h, 88h
		db	55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh
		db	0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h
		db	16 dup (0FFh)
		db	44h, 44h, 00h, 00h, 11h, 11h, 00h, 00h, 44h, 44h, 00h, 00h, 11h, 11h, 00h, 00h
		db	0CCh, 0CCh, 0FFh, 0FFh, 0EEh, 0EEh, 0FFh, 0FFh, 0CCh, 0CCh, 0FFh, 0FFh, 0EEh, 0EEh, 0FFh, 0FFh
		db	77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh
		db	16 dup (0FFh)
		db	16 dup (0)
		db	55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh
		db	16 dup (0)
		db	44h, 44h, 22h, 22h, 11h, 11h, 88h, 88h, 88h, 88h, 44h, 44h, 22h, 22h, 11h, 11h
		db	0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h
		db	0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h
		db	16 dup (0FFh)
		db	9 dup (12h)
_DATA	ends
DGROUP	group	_DATA

	extrn	_f_1FBD_0000:far

VIDEO_TEXT	segment word public 'CODE'
	assume	cs:VIDEO_TEXT, ds:DGROUP

	public	_f_1B4E_000C
	public	_f_1B4E_000D
	public	_f_1B4E_0025
	public	_f_1B4E_003B
	public	_f_1B4E_005E
	public	_f_1B4E_0081
	public	_f_1B4E_00CE
	public	_f_1B4E_0110
	public	_f_1B4E_015B
	public	_f_1B4E_0165
	public	_f_1B4E_0177
	public	_f_1B4E_01A1
	public	_f_1B4E_01AE
	public	_f_1B4E_0228
	public	_f_1B4E_0235
	public	_f_1B4E_0240

_f_1B4E_000C	proc	far
	retf
_f_1B4E_000C	endp

_f_1B4E_000D	proc	far
	push bp
	mov bp, sp
	lea bx, _g_41C0
	mov cx, word ptr [bp+6]
	mov al, cl
	and al, 0Fh
	xlat
	and cl, 0F0h
	or cl, al
	mov ax, cx
	pop bp
	retf
_f_1B4E_000D	endp

_f_1B4E_0025	proc	far
	push di
	les bx, dword ptr _g_3DF4
	mov ax, es
	les di, dword ptr _g_3DF8
	mov cx, 19h
L0033:
	xchg bx, ax
	stosw
	xchg bx, ax
	stosw
	loop L0033
	pop di
	retf
_f_1B4E_0025	endp

_f_1B4E_003B	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+0Ah]
	mov ax, word ptr es:[bx]
	mov cx, word ptr es:[bx+2]
	push cx
	push ax
	push es
	add bx, 4
	push bx
	push word ptr [bp+8]
	push word ptr [bp+6]
	call dword ptr _g_914C
	add sp, 0Ch
	pop bp
	retf
_f_1B4E_003B	endp

_f_1B4E_005E	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+0Ah]
	mov ax, word ptr es:[bx]
	mov cx, word ptr es:[bx+2]
	push cx
	push ax
	push es
	add bx, 4
	push bx
	push word ptr [bp+8]
	push word ptr [bp+6]
	call dword ptr _g_9154
	add sp, 0Ch
	pop bp
	retf
_f_1B4E_005E	endp

_f_1B4E_0081	proc	far
	push bp
	mov bp, sp
	push si
	push di
	mov di, word ptr [bp+6]
	push word ptr _g_3DDC
	les si, dword ptr [bp+0Ah]
	mov bx, word ptr [bp+8]
	sub di, word ptr _g_3DDE
L0097:
	mov al, byte ptr es:[si]
	inc si
	and al, al
	je L00BB
	cbw
	add di, word ptr _g_3DDE
	js L0097
	push es
	push ax
	push word ptr [bp+8]
	push di
	call far ptr _f_1B4E_0110
	add sp, 6
	pop es
	cmp di, word ptr _g_3DB2
	jb L0097
L00BB:
	add di, word ptr _g_3DDE
	mov word ptr _g_3DA0, di
	mov ax, word ptr [bp+8]
	mov word ptr _g_3DA2, ax
	pop ax
	pop di
	pop si
	pop bp
	retf
_f_1B4E_0081	endp

_f_1B4E_00CE	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+6]
	push es
	push bx
	push word ptr _g_3DA2
	push word ptr _g_3DA0
	call far ptr _f_1FBD_0000
	add sp, 8
	pop bp
	retf
_f_1B4E_00CE	endp

; characters 80h-A7h folded to plain letters for the 6-pixel font
FoldTable	db	'cueaaaaceeeiiiAAEaAooouuyoucLYPfaiounNao'

_f_1B4E_0110	proc	far
	push bp
	mov bp, sp
	push si
	push di
	mov bx, word ptr _g_3DDA
	cmp bx, 6
	jne L0135
	test byte ptr [bp+0Ah], 80h
	je L0135
	mov cx, bx
	mov bx, word ptr [bp+0Ah]
	xor bh, bh
	mov al, byte ptr cs:[bx+FoldTable]
	mov byte ptr [bp+0Ah], al
	mov bx, cx
L0135:
	mov ax, bx
	mul byte ptr [bp+0Ah]
	les si, dword ptr _g_3DD6
	add si, ax
	push word ptr _g_3DDC
	push word ptr _g_3DDE
	push es
	push si
	push word ptr [bp+8]
	push word ptr [bp+6]
	call dword ptr _g_9154
	add sp, 0Ch
	pop di
	pop si
	pop bp
	retf
_f_1B4E_0110	endp

_f_1B4E_015B	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	int 10h
	pop bp
	retf
_f_1B4E_015B	endp

_f_1B4E_0165	proc	far
	push ds
	push di
	mov ax, es
	les di, dword ptr _g_3DF8
	mov ds, ax
	mov cx, 32h
	rep movsw
	pop di
	pop ds
	retf
_f_1B4E_0165	endp

_f_1B4E_0177	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+6]
	mov cx, 300h
L0186:
	lodsb
	shr al, 1
	shr al, 1
	stosb
	loop L0186
	les dx, dword ptr [bp+6]
	mov bx, 0
	mov cx, 100h
	mov ax, 1012h
	int 10h
	pop ds
	pop di
	pop si
	pop bp
	retf
_f_1B4E_0177	endp

_f_1B4E_01A1	proc	far
	push bp
	mov bp, sp
	les dx, dword ptr [bp+6]
	mov ax, 1002h
	int 10h
	pop bp
	retf
_f_1B4E_01A1	endp

_f_1B4E_01AE	proc	far
	push bp
	mov bp, sp
	sub sp, 33h
	push si
	push di
	push ds
	mov ax, ss
	mov es, ax
	cmp word ptr [bp+0Ah], 0
	jne L01C6
	mov word ptr [bp+0Ah], 100h
L01C6:
	cmp word ptr [bp+0Ah], 10h
	jne L01E4
	mov cx, 10h
	xor al, al
	lea di, [bp-31h]
L01D4:
	stosb
	inc al
	loop L01D4
	xor al, al
	stosb
	lea dx, [bp-31h]
	mov ax, 1002h
	int 10h
L01E4:
	lds si, dword ptr [bp+6]
	mov word ptr [bp-33h], 0
L01EC:
	lea di, [bp-31h]
	mov cx, word ptr [bp+0Ah]
	and cx, cx
	je L0221
	cmp cx, 10h
	jle L01FE
	mov cx, 10h
L01FE:
	sub word ptr [bp+0Ah], cx
	mov bx, cx
	add cx, cx
	add cx, bx
L0207:
	lodsb
	shr al, 1
	shr al, 1
	stosb
	loop L0207
	lea dx, [bp-31h]
	mov cx, bx
	mov bx, word ptr [bp-33h]
	add word ptr [bp-33h], cx
	mov ax, 1012h
	int 10h
	jmp L01EC
L0221:
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_f_1B4E_01AE	endp

_f_1B4E_0228	proc	far
	push bp
	mov bp, sp
	mov ax, 1001h
	mov bh, byte ptr [bp+6]
	int 10h
	pop bp
	retf
_f_1B4E_0228	endp

_f_1B4E_0235	proc	far
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	xor ah, ah
	retf
_f_1B4E_0235	endp

_f_1B4E_0240	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	xor ah, ah
	int 10h
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	xor ah, ah
	pop bp
	retf
_f_1B4E_0240	endp

VIDEO_TEXT	ends
	end
