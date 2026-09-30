; Root module 1699: balloon bitmap helpers (row fill, mask conversion, Tandy mask conversion).
; Root code frame 1699, linear 16990-16B58.
; Genuine assembly: 'add bp,6' argument frames, DS loaded with DGROUP inside the procs,
; push es; push ds; push si; push di saves (MSC saves DI first, rule ASM-2) and pop bp without
; mov sp,bp (ASM-1).

_DATA	segment word public 'DATA'
	extrn	_g_1DE2:byte
	extrn	_g_1DE6:byte
	extrn	_g_1DE7:byte
_DATA	ends
DGROUP	group	_DATA

BALLOON_TEXT	segment word public 'CODE'
	assume	cs:BALLOON_TEXT, ds:DGROUP

	public	_f_1699_0000
	public	_f_1699_0050
	public	_f_1699_00A6
	public	_f_1699_0110
	public	_f_1699_01AA

_f_1699_0000	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	les di, dword ptr [bp+8]
	mov ax, word ptr es:[di]
	add di, 2
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr _g_1DE2, ax
	add di, 2
	mov ax, word ptr [bp+4]
	add di, ax
	mov ax, word ptr [bp+6]
	mov dx, word ptr _g_1DE2
	shl ax, 1
	mul dl
	add di, ax
	mov dx, word ptr _g_1DE2
	sub dx, 1
	lds si, dword ptr [bp]
	mov bx, 10h
	cld
L0044:
	movsb
	add di, dx
	dec bx
	jne L0044
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_1699_0000	endp

_f_1699_0050	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	les di, dword ptr [bp+8]
	mov ax, word ptr es:[di]
	add di, 2
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr _g_1DE2, ax
	add di, 2
	mov ax, word ptr [bp+4]
	add di, ax
	mov ax, word ptr [bp+6]
	mov dx, word ptr _g_1DE2
	shl ax, 1
	mul dl
	add di, ax
	mov dx, word ptr _g_1DE2
	mov cx, word ptr [bp+0Ch]
	sub dx, cx
	lds si, dword ptr [bp]
	mov bx, 10h
	cld
L0096:
	push cx
	lodsb
	rep stosb
	pop cx
	add di, dx
	dec bx
	jne L0096
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_1699_0050	endp

_f_1699_00A6	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	les di, dword ptr [bp+4]
	mov ax, word ptr es:[di]
	add di, 2
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr _g_1DE2, ax
	add di, 2
	mov ax, word ptr [bp+8]
	add di, ax
	mov ax, word ptr [bp+0Ah]
	mov dx, word ptr _g_1DE2
	shl ax, 1
	mul dl
	add di, ax
	mov dx, word ptr _g_1DE2
	lds si, dword ptr [bp]
	mov cx, word ptr [si]
	add cx, 7
	shr cx, 1
	shr cx, 1
	shr cx, 1
	add si, 2
	mov bx, word ptr [si]
	add si, 2
	shl dx, 1
	sub dx, cx
	lds si, dword ptr [si]
	cld
L00FD:
	push cx
L00FE:
	lodsb
	xor al, 0FFh
	stosb
	loop L00FE
	pop cx
	add di, dx
	dec bx
	jne L00FD
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_1699_00A6	endp

_f_1699_0110	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	les di, dword ptr [bp+4]
	mov ax, word ptr es:[di]
	add di, 2
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov byte ptr _g_1DE6, al
	mov ax, word ptr es:[di]
	add di, 2
	mov byte ptr _g_1DE7, al
	push di
	mov bl, byte ptr _g_1DE6
	shl bl, 1
	shl bl, 1
	mul bl
	mov cx, ax
	mov ax, 0
	rep stosb
	pop di
	mov bl, byte ptr _g_1DE6
	xor bh, bh
	dec di
	mov cl, 7
	mov dh, byte ptr _g_1DE7
	mov ch, byte ptr _g_1DE6
	mov ah, byte ptr _g_1DE6
	lds si, dword ptr [bp]
	add si, 4
L0166:
	mov al, byte ptr [si]
	shr al, cl
	and al, 1
	mov dl, byte ptr [bx+si]
	shr dl, cl
	and dl, 1
	je L017E
	sub al, 1
	xor al, 0Fh
	and al, 0Fh
	jmp L0180
L017E:
	mov al, 0Dh
L0180:
	test cl, 1
	je L018E
	shl al, 1
	shl al, 1
	shl al, 1
	shl al, 1
	inc di
L018E:
	or byte ptr es:[di], al
	dec cl
	jge L0166
	mov cl, 7
	inc si
	dec ch
	jne L0166
	add si, bx
	mov ch, ah
	dec dh
	jne L0166
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_1699_0110	endp

_f_1699_01AA	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov cx, word ptr [bp+0Eh]
	les di, dword ptr [bp+6]
	lds si, dword ptr [bp+0Ah]
L01B9:
	lodsb
	mov ah, byte ptr es:[di]
	stosb
	mov byte ptr [si-1], ah
	loop L01B9
	pop ds
	pop di
	pop si
	pop bp
	retf
_f_1699_01AA	endp

BALLOON_TEXT	ends
	end
