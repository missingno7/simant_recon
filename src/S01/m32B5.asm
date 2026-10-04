; Display driver S01, module 3: masked sprite blits and rectangle test.
; Overlay section S01, code frame 32B5, linear 32B5E-32DEB.

_DATA	segment word public 'DATA'
	extrn	_g_3D20:byte
	extrn	_mono_tail_masks:byte
_DATA	ends
DGROUP	group	_DATA

S01C_TEXT	segment word public 'CODE'
	assume	cs:S01C_TEXT, ds:DGROUP

	public	_o01_32B5_000E
	public	_o01_32B5_000F
	public	_o01_32B5_00AA
	public	_o01_32B5_0152
	public	_o01_32B5_024F

_o01_32B5_000E	proc	far
	retf
_o01_32B5_000E	endp

_o01_32B5_000F	proc	far
	push bp
	mov bp, sp
	sub sp, 0Ah
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lodsw
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov bx, ax
	shl ax, 1
	mov word ptr [bp-4], ax
	mov ax, word ptr es:[di]
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-2], ax
	mov dx, word ptr es:[di+2]
	mov cx, word ptr [bp+10h]
	and cx, cx
	je L0053
	mov ax, word ptr [bp-2]
	mul cl
	add di, ax
	sub dx, word ptr [bp+10h]
L0053:
	mov ax, word ptr [bp+0Eh]
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add di, ax
	and cl, 7
	lodsw
	cmp ax, dx
	jle L0068
	mov ax, dx
L0068:
	mov cx, word ptr [bp+0Eh]
	and cl, 7
	mov word ptr [bp-6], ax
	add di, 4
L0074:
	mov ch, bl
	push di
	push si
L0078:
	xor ah, ah
	mov al, byte ptr [si]
	ror ax, cl
	add si, bx
	xor dh, dh
	mov dl, byte ptr [si]
	sub si, bx
	inc si
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	inc di
	dec ch
	jne L0078
	pop si
	pop di
	add si, word ptr [bp-4]
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L0074
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o01_32B5_000F	endp

_o01_32B5_00AA	proc	far
	push bp
	mov bp, sp
	sub sp, 0Ch
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lodsw
	mov bx, ax
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-4], ax
	and bx, 7
	assume ss:DGROUP
	mov al, byte ptr ss:_mono_tail_masks[bx]
	assume ss:nothing
	mov byte ptr [bp-0Ch], al
	mov ax, word ptr es:[di]
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-2], ax
	mov bx, word ptr [bp-4]
	mov dx, word ptr es:[di+2]
	mov cx, word ptr [bp+10h]
	and cx, cx
	je L00FA
	mov ax, word ptr [bp-2]
	mul cl
	add di, ax
	sub dx, word ptr [bp+10h]
L00FA:
	mov ax, word ptr [bp+0Eh]
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add di, ax
	lodsw
	cmp ax, dx
	jle L010C
	mov ax, dx
L010C:
	mov word ptr [bp-6], ax
	add di, 4
	mov cx, word ptr [bp+0Eh]
	and cl, 7
L0118:
	mov ch, bl
	push si
	push di
L011C:
	xor ax, ax
	mov al, byte ptr [bp-0Ch]
	cmp ch, 1
	je L0128
	mov al, 0FFh
L0128:
	ror ax, cl
	xor dh, dh
	mov dl, byte ptr [si]
	inc si
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	inc di
	dec ch
	jne L011C
	pop di
	pop si
	add si, word ptr [bp-4]
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L0118
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o01_32B5_00AA	endp

_o01_32B5_0152	proc	far
	push bp
	mov bp, sp
	sub sp, 10h
	push si
	push di
	push ds
	les si, dword ptr [bp+6]
	lds di, dword ptr [bp+0Eh]
	mov ax, word ptr es:[si]
	cmp ax, word ptr [di+4]
	jge L0183
	mov bx, word ptr es:[si+4]
	cmp bx, word ptr [di]
	jle L0183
	mov cx, word ptr es:[si+2]
	cmp cx, word ptr [di+6]
	jge L0183
	mov cx, word ptr es:[si+6]
	cmp cx, word ptr [di+2]
	jg L018C
L0183:
	xor ax, ax
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L018C:
	mov dx, word ptr [di]
	cmp dx, ax
	jg L0194
	mov dx, ax
L0194:
	sub ax, bx
	neg ax
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-0Eh], ax
	mov ax, word ptr [di+4]
	sub ax, word ptr [di]
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-10h], ax
	mov ax, word ptr [di+4]
	cmp bx, ax
	jl L01B8
	mov bx, ax
L01B8:
	mov ax, word ptr [di+6]
	cmp ax, cx
	jl L01C1
	mov ax, cx
L01C1:
	mov word ptr [bp-8], ax
	mov ax, word ptr [di+2]
	mov cx, word ptr es:[si+2]
	cmp ax, cx
	jg L01D1
	mov ax, cx
L01D1:
	mov word ptr [bp-6], ax
	mov ax, bx
	sub ax, dx
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-0Ah], ax
	mov cx, word ptr [bp-8]
	sub cx, word ptr [bp-6]
	mov word ptr [bp-0Ch], cx
	mov ax, word ptr [bp-6]
	sub ax, word ptr es:[si+2]
	mov bx, word ptr [bp-0Eh]
	mov cx, dx
	mov word ptr [bp-2], dx
	mul bx
	sub cx, word ptr es:[si]
	shr cx, 1
	shr cx, 1
	shr cx, 1
	add cx, ax
	mov ax, word ptr [bp-6]
	sub ax, word ptr [di+2]
	mov bx, word ptr [bp-10h]
	mul bx
	mov dx, word ptr [bp-2]
	sub dx, word ptr [di]
	shr dx, 1
	shr dx, 1
	shr dx, 1
	add dx, ax
	les di, dword ptr [bp+12h]
	lds si, dword ptr [bp+0Ah]
	add si, cx
	add si, 4
	add di, dx
	add di, 4
	mov bx, word ptr [bp-0Ah]
	mov ax, word ptr [bp-0Ch]
	mov dx, word ptr [bp-0Eh]
	sub dx, bx
	sub word ptr [bp-10h], bx
L023C:
	mov cx, bx
	rep movsb
	add si, dx
	add di, word ptr [bp-10h]
	dec ax
	jg L023C
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o01_32B5_0152	endp

_o01_32B5_024F	proc	far
	push bp
	mov bp, sp
	push si
	push di
	les di, dword ptr [bp+6]
	lea si, _g_3D20
	mov bx, word ptr [bp+0Ah]
	shr bx, 1
	shr bx, 1
	shr bx, 1
	sub bx, 2
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	movsw
	add di, bx
	pop di
	pop si
	pop bp
	retf
_o01_32B5_024F	endp

S01C_TEXT	ends
	end
