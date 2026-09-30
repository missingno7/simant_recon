; Display driver S00 (EGA/VGA planar), module 3: masked sprite blits and rectangle test.
; Overlay section S00, code frame 35A6, linear 35A66-35F42.
; Genuine assembly (MASM 5.10 reproduces it byte for byte).  Evidence against compiler
; output: every framed proc saves "push si; push di; push ds" and restores in reverse order,
; while MSC 6.00/6.00A/6.00AX always saves DI before SI, also around inline _asm (probe
; ASM-2, work/ovlA/probe); the ror/rol twin loops after the first retf of
; o00_35A6_0007 and o00_35A6_0177 are unreachable code, which MSC never emits.

_DATA	segment word public 'DATA'
	extrn	_g_3D20:byte
_DATA	ends
DGROUP	group	_DATA

S00C_TEXT	segment word public 'CODE'
	assume	cs:S00C_TEXT, ds:DGROUP

	public	_o00_35A6_0006
	public	_o00_35A6_0007
	public	_o00_35A6_0177
	public	_o00_35A6_02FD
	public	_o00_35A6_0406

_o00_35A6_0006	proc	far
	retf
_o00_35A6_0006	endp

; blit a 1-bit image into a plane buffer at a bit shift (called from root 259D)
_o00_35A6_0007	proc	far
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
	mov word ptr [bp-4], ax
	mov ax, word ptr es:[di]
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-2], ax
	mov cx, word ptr [bp+0Eh]
	mov bx, word ptr [bp-4]
	mov ax, bx
	shl ax, 1
	shl ax, 1
	dec ax
	mov word ptr [bp-8], ax
	mov ax, word ptr [bp-2]
	shl ax, 1
	add ax, word ptr [bp-2]
	dec ax
	mov word ptr [bp-0Ah], ax
	mov dx, word ptr es:[di+2]
	mov bx, word ptr [bp+10h]
	and bx, bx
	je L0067
	mov ax, word ptr [bp-2]
	shl ax, 1
	shl ax, 1
	mul bl
	add di, ax
	sub dx, word ptr [bp+10h]
L0067:
	mov bx, word ptr [bp-4]
	mov ax, cx
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add di, ax
	and cl, 7
	lodsw
	cmp ax, dx
	jle L007E
	mov ax, dx
L007E:
	mov word ptr [bp-6], ax
	add di, 4
	cmp cl, 4
L0087:
	mov ch, bl
	push si
	push di
L008B:
	xor ah, ah
	mov al, byte ptr [si]
	ror ax, cl
	add si, bx
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	sub si, word ptr [bp-8]
	sub di, word ptr [bp-0Ah]
	dec ch
	jne L008B
	pop di
	pop si
	add si, word ptr [bp-8]
	inc si
	add si, bx
	add di, word ptr [bp-0Ah]
	inc di
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L0087
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L00FF:
	mov ch, bl
	push si
	push di
L0103:
	xor al, al
	mov ah, byte ptr [si]
	rol ax, cl
	add si, bx
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	sub si, word ptr [bp-8]
	sub di, word ptr [bp-0Ah]
	dec ch
	jne L0103
	pop di
	pop si
	add si, word ptr [bp-8]
	inc si
	add si, bx
	add di, word ptr [bp-0Ah]
	inc di
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L00FF
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_35A6_0007	endp

_o00_35A6_0177	proc	far
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
	mov al, byte ptr ss:[bx+6778h]
	mov byte ptr [bp-0Ch], al
	mov ax, word ptr es:[di]
	add ax, 7
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov word ptr [bp-2], ax
	mov cx, word ptr [bp+0Eh]
	mov bx, word ptr [bp-4]
	mov ax, bx
	shl ax, 1
	add ax, bx
	dec ax
	mov word ptr [bp-8], ax
	mov ax, word ptr [bp-2]
	shl ax, 1
	add ax, word ptr [bp-2]
	dec ax
	mov word ptr [bp-0Ah], ax
	mov dx, word ptr es:[di+2]
	mov bx, word ptr [bp+10h]
	and bx, bx
	je L01E4
	mov ax, word ptr [bp-2]
	shl ax, 1
	shl ax, 1
	mul bl
	add di, ax
	sub dx, word ptr [bp+10h]
L01E4:
	mov bx, word ptr [bp-4]
	mov ax, cx
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add di, ax
	and cl, 7
	lodsw
	cmp ax, dx
	jle L01FB
	mov ax, dx
L01FB:
	mov word ptr [bp-6], ax
	add di, 4
L0201:
	mov ch, bl
	push si
	push di
L0205:
	xor ax, ax
	mov al, byte ptr [bp-0Ch]
	cmp ch, 1
	je L0211
	mov al, 0FFh
L0211:
	ror ax, cl
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dh, dh
	mov dl, byte ptr [si]
	ror dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	sub si, word ptr [bp-8]
	sub di, word ptr [bp-0Ah]
	dec ch
	jne L0205
	pop di
	pop si
	add si, word ptr [bp-8]
	inc si
	add si, bx
	add di, word ptr [bp-0Ah]
	inc di
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L0201
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L027F:
	mov ch, bl
	push si
	push di
L0283:
	xor ax, ax
	mov ah, byte ptr [bp-0Ch]
	cmp ch, 1
	je L028F
	mov ah, 0FFh
L028F:
	rol ax, cl
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	add si, bx
	add di, word ptr [bp-2]
	xor dl, dl
	mov dh, byte ptr [si]
	rol dx, cl
	xor dx, word ptr es:[di]
	and dx, ax
	xor word ptr es:[di], dx
	sub si, word ptr [bp-8]
	sub di, word ptr [bp-0Ah]
	dec ch
	jne L0283
	pop di
	pop si
	add si, word ptr [bp-8]
	inc si
	add si, bx
	add di, word ptr [bp-0Ah]
	inc di
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L027F
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_35A6_0177	endp

_o00_35A6_02FD	proc	far
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
	jge L032E
	mov bx, word ptr es:[si+4]
	cmp bx, word ptr [di]
	jle L032E
	mov cx, word ptr es:[si+2]
	cmp cx, word ptr [di+6]
	jge L032E
	mov cx, word ptr es:[si+6]
	cmp cx, word ptr [di+2]
	jg L0337
L032E:
	xor ax, ax
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0337:
	mov dx, word ptr [di]
	cmp dx, ax
	jg L033F
	mov dx, ax
L033F:
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
	jl L0363
	mov bx, ax
L0363:
	mov ax, word ptr [di+6]
	cmp ax, cx
	jl L036C
	mov ax, cx
L036C:
	mov word ptr [bp-8], ax
	mov ax, word ptr [di+2]
	mov cx, word ptr es:[si+2]
	cmp ax, cx
	jg L037C
	mov ax, cx
L037C:
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
	shl ax, 1
	shl ax, 1
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
	shl ax, 1
	shl ax, 1
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
	shl ax, 1
	shl ax, 1
	mov dx, word ptr [bp-0Eh]
	sub dx, bx
	sub word ptr [bp-10h], bx
L03F3:
	mov cx, bx
	rep movsb
	add si, dx
	add di, word ptr [bp-10h]
	dec ax
	jg L03F3
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_35A6_02FD	endp

_o00_35A6_0406	proc	far
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
_o00_35A6_0406	endp

S00C_TEXT	ends
	end
