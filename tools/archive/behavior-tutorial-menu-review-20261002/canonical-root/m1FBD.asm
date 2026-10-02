; Root module 1FBD: draw a text string with the bitmap font (accented-character folding, underline).
; Root code frame 1FBD, linear 1FBD0-1FD27.
; Genuine assembly: push si; push di saves (MSC saves DI first, rule ASM-2) and a BP frame
; without stack check ending pop bp without mov sp,bp (ASM-1).

_DATA	segment word public 'DATA'
	extrn	_g_3DA0:byte
	extrn	_g_3DA2:byte
	extrn	_g_3DD6:byte
	extrn	_g_3DDA:byte
	extrn	_g_3DDC:byte
	extrn	_g_3DDE:byte
	extrn	_g_5A97:byte
	public	_g_5ABA, _g_5ABC, _g_5ABE
_g_5ABA		dw	0		; text bitmap: width, height, pixel rows
_g_5ABC		dw	0
_g_5ABE		db	1040 dup (0)
_g_5ECE		db	79 dup (0)	; copy of the string (at most 79 characters)
_g_5F1D		db	0
		db	160 dup (0)	; not referenced
_g_5FBE		db	'cueaaaaceeeiiiAAEaAooouuyoucLYPfaiounNao'	; folding of characters 80h-A7h
_DATA	ends
DGROUP	group	_DATA

	extrn	_f_1B4E_005E:far
	extrn	_f_1B4E_0081:far

TEXTOUT_TEXT	segment word public 'CODE'
	assume	cs:TEXTOUT_TEXT, ds:DGROUP

	public	_f_1FBD_0000

_f_1FBD_0000	proc	far
	push bp
	mov bp, sp
	push si
	push di
	cmp byte ptr _g_5A97, 6
	je L000E
	jne L0025
L000E:
	les ax, dword ptr [bp+0Ah]
	push es
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _f_1B4E_0081
	add sp, 8
	pop di
	pop si
	pop bp
	retf
L0025:
	mov bl, byte ptr _g_3DDC
	xor bh, bh
	mov word ptr _g_5ABC, bx
	mov ax, ds
	mov es, ax
	mov di, offset DGROUP:_g_5ECE
	lds si, dword ptr [bp+0Ah]
	xor dl, dl
L003B:
	lodsb
	stosb
	or al, al
	je L004A
	inc dl
	cmp dl, 50h
	jne L003B
	dec dl
L004A:
	mov ax, DGROUP
	mov ds, ax
	or dl, dl
	jne L0057
	pop di
	pop si
	pop bp
	retf
L0057:
	cmp byte ptr _g_3DDE, 8
	jne L00A5
	mov byte ptr _g_5F1D, 0
	mov al, byte ptr _g_3DDE
	mul dl
	mov word ptr _g_5ABA, ax
	dec ax
	or ax, 7
	inc ax
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov dx, ax
	dec dx
	mov di, offset DGROUP:_g_5ABE
	mov si, offset DGROUP:_g_5ECE
L007F:
	lodsb
	or al, al
	je L00A2
	mov cx, word ptr _g_3DDA
	mul cl
	push si
	lds si, dword ptr _g_3DD6
	add si, ax
	mov ax, di
L0093:
	movsb
	add di, dx
	loop L0093
	mov di, ax
	inc di
	pop si
	mov ax, es
	mov ds, ax
	jmp L007F
L00A2:
	jmp near ptr L0130
L00A5:
	mov byte ptr _g_5F1D, 0
	mov al, byte ptr _g_3DDE
	mul dl
	mov word ptr _g_5ABA, ax
	dec ax
	or ax, 7
	inc ax
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov dx, ax
	mov di, offset DGROUP:_g_5ABE
	mov si, offset DGROUP:_g_5ECE
L00C5:
	lodsb
	or al, al
	je L0130
	test al, 80h
	je L00D8
	push bx
	mov bl, al
	xor bh, bh
	mov al, byte ptr [bx+_g_5FBE]
	pop bx
L00D8:
	mov cx, word ptr _g_3DDA
	mul cl
	push si
	lds si, dword ptr _g_3DD6
	add si, ax
	push di
L00E6:
	lodsb
	and al, 0F0h
	mov byte ptr es:[di], al
	add di, dx
	loop L00E6
	pop di
	pop si
	mov ax, es
	mov ds, ax
	lodsb
	or al, al
	je L0130
	test al, 80h
	je L0109
	push bx
	mov bl, al
	xor bh, bh
	mov al, byte ptr [bx+_g_5FBE]
	pop bx
L0109:
	mov cx, word ptr _g_3DDA
	mul cl
	push si
	lds si, dword ptr _g_3DD6
	add si, ax
	push di
L0117:
	lodsb
	shr al, 1
	shr al, 1
	shr al, 1
	shr al, 1
	or byte ptr es:[di], al
	add di, dx
	loop L0117
	pop di
	inc di
	pop si
	mov ax, es
	mov ds, ax
	jmp L00C5
L0130:
	push ds
	mov ax, offset DGROUP:_g_5ABA
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _f_1B4E_005E
	add sp, 8
	mov ax, word ptr [bp+6]
	add ax, word ptr _g_5ABA
	mov word ptr _g_3DA0, ax
	mov ax, word ptr [bp+8]
	mov word ptr _g_3DA2, ax
	pop di
	pop si
	pop bp
	retf
_f_1FBD_0000	endp

TEXTOUT_TEXT	ends
	end
