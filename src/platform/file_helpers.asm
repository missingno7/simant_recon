; Root module 1F66: wildcard file-name match, current directory, checksum, drive count, register self-test (Daniel Goldman library).
; Root code frame 1F66, linear 1F668-1F80B.
; Genuine assembly: code-segment copyright string, two entry stubs (mov dl,1/0; jmp) into one
; body, lodsb/loop/rol checksum, int 21h calls with carry results (cmc/adc) and register-only
; procs; the framed procs save push ds; push si; push di (MSC saves DI first, rule ASM-2).

_DATA	segment word public 'DATA'
_DATA	ends
DGROUP	group	_DATA

GOLDMAN_TEXT	segment word public 'CODE'
	assume	cs:GOLDMAN_TEXT, ds:DGROUP

	public	_f_1F66_0029
	public	_f_1F66_002D
	public	_f_1F66_00AF
	public	_f_1F66_00DA
	public	_f_1F66_00F6
	public	_f_1F66_0107

Copyright	db	'Copyright (C)1990, Daniel Goldman'

_f_1F66_0029	proc	far
	mov dl, 1
	jmp short L0031
_f_1F66_0029	endp

_f_1F66_002D	proc	far
	mov dl, 0
	jmp short L0031
L0031:
	push bp
	mov bp, sp
	push ds
	push si
	push di
	les si, dword ptr [bp+6]
	lds di, dword ptr [bp+0Ah]
	xor cx, cx
L003F:
	xor bx, bx
	dec bx
L0042:
	inc bx
	mov al, byte ptr es:[bx+si]
	and al, al
	je L0093
	cmp al, '*'
	je L007E
	cmp al, 'a'
	jb L0058
	cmp al, 'z'
	ja L0058
	xor al, 20h
L0058:
	mov ah, byte ptr [bx+di]
	and ah, ah
	je L00A7
	cmp al, '?'
	je L0042
	cmp ah, 'a'
	jb L006F
	cmp ah, 'z'
	ja L006F
	xor ah, 20h
L006F:
	cmp ah, al
	je L0042
	and dl, dl
	je L00A7
	inc di
	and bx, bx
	je L0058
	jmp L003F
L007E:
	and dl, dl
	je L0088
	and cx, cx
	jne L0088
	mov cx, di
L0088:
	mov dl, 1
	add si, bx
	add si, 1
	add di, bx
	jmp L003F
L0093:
	mov ah, byte ptr [bx+di]
	and ah, ah
	je L009D
	and dl, dl
	je L00A7
L009D:
	and cx, cx
	jne L00A3
	mov cx, di
L00A3:
	mov ax, cx
	jmp short L00AA
L00A7:
	mov ax, 0
L00AA:
	pop di
	pop si
	pop ds
	pop bp
	retf
_f_1F66_002D	endp

_f_1F66_00AF	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	mov dl, byte ptr [bp+6]
	lds si, dword ptr [bp+8]
	mov al, byte ptr [bp+6]
	add al, 40h
	mov byte ptr [si], al
	inc si
	mov al, 3Ah
	mov byte ptr [si], al
	inc si
	mov al, 5Ch
	mov byte ptr [si], al
	inc si
	mov ah, 47h
	int 21h
	mov ax, 0
	cmc
	adc al, 0
	pop si
	pop ds
	pop bp
	retf
_f_1F66_00AF	endp

_f_1F66_00DA	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	lds si, dword ptr [bp+6]
	mov cx, word ptr [bp+0Ah]
	xor bx, bx
	xor ax, ax
L00E9:
	lodsb
	add bx, ax
	rol bx, 1
	loop L00E9
	mov ax, bx
	pop si
	pop ds
	pop bp
	retf
_f_1F66_00DA	endp

_f_1F66_00F6	proc	far
	mov ah, 52h
	int 21h
	mov al, byte ptr es:[bx+20h]
	xor ah, ah
	and al, al
	jne L0106
	mov al, 8
L0106:
	retf
_f_1F66_00F6	endp

_f_1F66_0107	proc	far
	push bp
	mov bp, sp
	sub sp, 14h
	push es
	push ds
	push ax
	push bx
	push cx
	push dx
	push di
	push si
	mov ax, 0A3A5h
	mov word ptr [bp-4], ax
	ror ax, 1
	mov word ptr [bp-6], ax
	mov si, ax
	ror ax, 1
	mov word ptr [bp-8], ax
	mov di, ax
	ror ax, 1
	mov word ptr [bp-0Ah], ax
	mov bx, ax
	ror ax, 1
	mov word ptr [bp-0Ch], ax
	mov cx, ax
	ror ax, 1
	mov word ptr [bp-0Eh], ax
	mov dx, ax
	ror ax, 1
	mov word ptr [bp-10h], ax
	mov ds, ax
	ror ax, 1
	mov word ptr [bp-12h], ax
	mov es, ax
	mov word ptr [bp-14h], 40h
L0151:
	mov word ptr [bp-2], 0
L0156:
	cmp word ptr [bp-4], ax
	je L019A
	cmp word ptr [bp-4], si
	je L019A
	cmp word ptr [bp-4], di
	je L019A
	cmp word ptr [bp-4], bx
	je L019A
	cmp word ptr [bp-4], cx
	je L019A
	cmp word ptr [bp-4], dx
	je L019A
	push ax
	mov ax, ds
	cmp word ptr [bp-4], ax
	je L019A
	mov ax, es
	cmp word ptr [bp-4], ax
	je L019A
	pop ax
	dec word ptr [bp-2]
	jne L0156
	dec word ptr [bp-14h]
	jne L0151
	pop si
	pop di
	pop dx
	pop cx
	pop bx
	pop ax
	pop ds
	pop es
	mov sp, bp
	pop bp
	retf
L019A:
	mov ax, 0B000h
	mov es, ax
	mov byte ptr es:[40h], 21h
	int 23h
	mov sp, bp
	pop bp
	retf
_f_1F66_0107	endp

GOLDMAN_TEXT	ends
	end
