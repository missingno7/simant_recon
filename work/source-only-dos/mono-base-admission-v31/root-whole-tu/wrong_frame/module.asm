; Display driver S01, module 2: mini-map tables.
; Overlay section S01, code frame 328E, linear 328EA-32B5E.

_DATA	segment word public 'DATA'
	extrn	_g_8ED8:byte
_DATA	ends
DGROUP	group	_DATA

S01B_TEXT	segment word public 'CODE'
	assume	cs:S01B_TEXT, ds:DGROUP

	public	_o01_328E_000A
	public	_o01_328E_009D
	public	_o01_328E_012C
	public	_o01_328E_01D5

_o01_328E_000A	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov bx, word ptr [bp+0Eh]
	and bx, 7
	add bx, offset _DATA:_g_8ED8
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	mov cx, 40h
L0023:
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0F0h
	mov byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0F0h
	mov byte ptr es:[di+40h], dl
	mov dl, byte ptr ss:[bx+2]
	and dl, 0F0h
	mov byte ptr es:[di+80h], dl
	mov dl, byte ptr ss:[bx+3]
	and dl, 0F0h
	mov byte ptr es:[di+0C0h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0Fh
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0Fh
	or byte ptr es:[di+40h], dl
	mov dl, byte ptr ss:[bx+2]
	and dl, 0Fh
	or byte ptr es:[di+80h], dl
	mov dl, byte ptr ss:[bx+3]
	and dl, 0Fh
	or byte ptr es:[di+0C0h], dl
	sub bx, ax
	inc di
	loop L0023
	pop ds
	pop di
	pop si
	pop bp
	retf
_o01_328E_000A	endp

_o01_328E_009D	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov bx, word ptr [bp+10h]
	and bx, 7
	add bx, offset _DATA:_g_8ED8
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	mov cx, 20h
L00B6:
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0F0h
	mov byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0F0h
	mov byte ptr es:[di+20h], dl
	mov dl, byte ptr ss:[bx+2]
	and dl, 0F0h
	mov byte ptr es:[di+40h], dl
	mov dl, byte ptr ss:[bx+3]
	and dl, 0F0h
	mov byte ptr es:[di+60h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0Fh
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0Fh
	or byte ptr es:[di+20h], dl
	mov dl, byte ptr ss:[bx+2]
	and dl, 0Fh
	or byte ptr es:[di+40h], dl
	mov dl, byte ptr ss:[bx+3]
	and dl, 0Fh
	or byte ptr es:[di+60h], dl
	sub bx, ax
	inc di
	loop L00B6
	pop ds
	pop di
	pop si
	pop bp
	retf
_o01_328E_009D	endp

_o01_328E_012C	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov bx, word ptr [bp+0Eh]
	and bx, 7
	add bx, offset _DATA:_g_8ED8
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	mov cx, 20h
L0145:
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0C0h
	mov byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0C0h
	mov byte ptr es:[di+20h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 30h
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 30h
	or byte ptr es:[di+20h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0Ch
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0Ch
	or byte ptr es:[di+20h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 3
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 3
	or byte ptr es:[di+20h], dl
	sub bx, ax
	inc di
	dec cx
	je L01D0
	jmp L0145
L01D0:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o01_328E_012C	endp

_o01_328E_01D5	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	mov bx, word ptr [bp+0Eh]
	and bx, 7
	add bx, offset _DATA:_g_8ED8
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	mov cx, 10h
L01EE:
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0C0h
	mov byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0C0h
	mov byte ptr es:[di+10h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 30h
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 30h
	or byte ptr es:[di+10h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 0Ch
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 0Ch
	or byte ptr es:[di+10h], dl
	sub bx, ax
	xor ah, ah
	lodsb
	shl ax, 1
	shl ax, 1
	shl ax, 1
	add bx, ax
	mov dl, byte ptr ss:[bx]
	and dl, 3
	or byte ptr es:[di], dl
	mov dl, byte ptr ss:[bx+1]
	and dl, 3
	or byte ptr es:[di+10h], dl
	sub bx, ax
	inc di
	dec cx
	je L0279
	jmp L01EE
L0279:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o01_328E_01D5	endp

S01B_TEXT	ends
	end
