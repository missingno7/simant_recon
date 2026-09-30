; Display driver S03, module 3: colour-translated sprite and tile blits.
; Overlay section S03, code frame 3258, linear 3258C-33D33.

_DATA	segment word public 'DATA'
	extrn	_g_3D20:byte
_DATA	ends
DGROUP	group	_DATA

	extrn	_o03_3126_091F:far

S03C_TEXT	segment word public 'CODE'
	assume	cs:S03C_TEXT, ds:DGROUP

	public	_o03_3258_040C
	public	_o03_3258_040D
	public	_o03_3258_04CE
	public	_o03_3258_05A7
	public	_o03_3258_0690
	public	_o03_3258_0F04
	public	_o03_3258_175F

xlat_tabs	label	byte
; Four 256-byte colour translation tables indexed by a byte of two 4-bit pixels.
; Table 0 is the transparency mask: colour 0Dh gives a 0 nibble, every other colour 0Fh.
; Tables 1-3 copy both pixels, mapping colour 0Eh to 4, 8 and 0Eh respectively.
hi	=	0
	rept	16
lo	=	0
	rept	16
m	=	0
	if	hi NE 0Dh
m	=	0F0h
	endif
	if	lo NE 0Dh
m	=	m OR 0Fh
	endif
	db	m
lo	=	lo + 1
	endm
hi	=	hi + 1
	endm

nibmap	macro	ecol
hi	=	0
	rept	16
lo	=	0
	rept	16
h	=	hi
	if	hi EQ 0Eh
h	=	ecol
	endif
l	=	lo
	if	lo EQ 0Eh
l	=	ecol
	endif
	db	h * 16 + l
lo	=	lo + 1
	endm
hi	=	hi + 1
	endm
	endm

	nibmap	4
	nibmap	8
	nibmap	0Eh
_o03_3258_040C	proc	far
	retf
_o03_3258_040C	endp

_o03_3258_040D	proc	far
	push bp
	mov bp, sp
	sub sp, 0Ah
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lodsw
	inc ax
	shr ax, 1
	mov dx, ax
	mov word ptr [bp-4], ax
	mov ax, word ptr es:[di]
	inc ax
	shr ax, 1
	mov word ptr [bp-2], ax
	mov cx, word ptr es:[di+2]
	mov bx, word ptr [bp+10h]
	and bx, bx
	je L0443
	mov ax, word ptr [bp-2]
	mul bl
	add di, ax
	sub cx, word ptr [bp+10h]
L0443:
	mov ax, word ptr [bp+0Eh]
	shr ax, 1
	add di, ax
	lodsw
	cmp ax, cx
	jle L0451
	mov ax, cx
L0451:
	mov word ptr [bp-6], ax
	add di, 4
	test word ptr [bp+0Eh], 1
	jne L048D
	xor bh, bh
L0460:
	mov ch, dl
	push di
	push si
L0464:
	mov bl, byte ptr [si]
	mov al, byte ptr cs:[bx+xlat_tabs]
	inc si
	xor bl, byte ptr es:[di]
	and bl, al
	xor byte ptr es:[di], bl
	inc di
	dec ch
	jne L0464
	pop si
	pop di
	add si, word ptr [bp-4]
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L0460
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L048D:
	mov ch, dl
	push di
	push si
L0491:
	xor bh, bh
	mov bl, byte ptr [si]
	mov al, byte ptr cs:[bx+xlat_tabs]
	xor ah, ah
	ror ax, 1
	ror ax, 1
	ror ax, 1
	ror ax, 1
	ror bx, 1
	ror bx, 1
	ror bx, 1
	ror bx, 1
	inc si
	xor bx, word ptr es:[di]
	and bx, ax
	xor word ptr es:[di], bx
	inc di
	dec ch
	jne L0491
	pop si
	pop di
	add si, word ptr [bp-4]
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L048D
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o03_3258_040D	endp

_o03_3258_04CE	proc	far
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
	mov dx, ax
	add ax, 1
	shr ax, 1
	mov word ptr [bp-4], ax
	and bx, 1
	mov al, byte ptr ss:[bx+68B4h]
	mov byte ptr [bp-0Ch], al
	mov ax, word ptr es:[di]
	add ax, 1
	shr ax, 1
	mov word ptr [bp-2], ax
	mov dx, word ptr es:[di+2]
	mov cx, word ptr [bp+10h]
	and cx, cx
	je L0511
	mul cl
	add di, ax
	sub dx, cx
L0511:
	mov ax, word ptr [bp+0Eh]
	shr ax, 1
	add di, ax
	lodsw
	cmp ax, dx
	jle L051F
	mov ax, dx
L051F:
	mov word ptr [bp-6], ax
	add di, 4
	mov cx, word ptr [bp+0Eh]
	and cx, 1
	jne L0561
	xor bh, bh
L052F:
	mov ch, dl
	push di
	push si
L0533:
	mov al, 0FFh
	cmp ch, 1
	je L053F
	movsb
	dec ch
	jmp L0533
L053F:
	mov al, byte ptr [bp-0Ch]
	mov bl, byte ptr [si]
	inc si
	xor bl, byte ptr es:[di]
	and bl, al
	xor byte ptr es:[di], bl
	pop si
	pop di
	add si, word ptr [bp-4]
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L052F
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0561:
	mov ch, dl
	push di
	push si
L0565:
	xor bh, bh
	mov bl, byte ptr [si]
	xor ah, ah
	mov al, byte ptr [bp-0Ch]
	cmp ch, 1
	je L0575
	mov al, 0FFh
L0575:
	ror ax, 1
	ror ax, 1
	ror ax, 1
	ror ax, 1
	ror bx, 1
	ror bx, 1
	ror bx, 1
	ror bx, 1
	inc si
	xor bx, word ptr es:[di]
	and bx, ax
	xor word ptr es:[di], bx
	inc di
	dec ch
	jne L0565
	pop si
	pop di
	add si, word ptr [bp-4]
	add di, word ptr [bp-2]
	dec word ptr [bp-6]
	jne L0561
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o03_3258_04CE	endp

_o03_3258_05A7	proc	far
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
	jge L05D8
	mov bx, word ptr es:[si+4]
	cmp bx, word ptr [di]
	jle L05D8
	mov cx, word ptr es:[si+2]
	cmp cx, word ptr [di+6]
	jge L05D8
	mov cx, word ptr es:[si+6]
	cmp cx, word ptr [di+2]
	jg L05E1
L05D8:
	xor ax, ax
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L05E1:
	mov dx, word ptr [di]
	cmp dx, ax
	jg L05E9
	mov dx, ax
L05E9:
	sub ax, bx
	neg ax
	shr ax, 1
	mov word ptr [bp-0Eh], ax
	mov ax, word ptr [di+4]
	sub ax, word ptr [di]
	shr ax, 1
	mov word ptr [bp-10h], ax
	mov ax, word ptr [di+4]
	cmp bx, ax
	jl L0605
	mov bx, ax
L0605:
	mov ax, word ptr [di+6]
	cmp ax, cx
	jl L060E
	mov ax, cx
L060E:
	mov word ptr [bp-8], ax
	mov ax, word ptr [di+2]
	mov cx, word ptr es:[si+2]
	cmp ax, cx
	jg L061E
	mov ax, cx
L061E:
	mov word ptr [bp-6], ax
	mov ax, bx
	sub ax, dx
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
	add cx, ax
	mov ax, word ptr [bp-6]
	sub ax, word ptr [di+2]
	mov bx, word ptr [bp-10h]
	mul bx
	mov dx, word ptr [bp-2]
	sub dx, word ptr [di]
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
L067D:
	mov cx, bx
	rep movsb
	add si, dx
	add di, word ptr [bp-10h]
	dec ax
	jg L067D
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o03_3258_05A7	endp

_o03_3258_0690	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+0Eh]
	lds si, dword ptr [bp+0Ah]
	lea dx, ds:[0Ch]
	lea bx, ds:[20Ch]
	cmp byte ptr [bp+12h], 0
	je L06B8
	lea bx, ds:[10Ch]
	cmp byte ptr [bp+12h], 3
	je L06B8
	lea bx, ds:[30Ch]
L06B8:
	push bp
	lea bp, _g_3D20
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	pop bp
	pop ds
	mov ax, 0Ch
	push ax
	push ax
	push ds
	lea ax, _g_3D20
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o03_3126_091F
	add sp, 0Ch
	pop di
	pop si
	pop bp
	retf
_o03_3258_0690	endp

_o03_3258_0F04	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+0Ah]
	lds si, dword ptr [bp+6]
	lea dx, ds:[0Ch]
	lea bx, ds:[20Ch]
	cmp byte ptr [bp+0Eh], 0
	je L0F2C
	lea bx, ds:[10Ch]
	cmp byte ptr [bp+0Eh], 3
	je L0F2C
	lea bx, ds:[30Ch]
L0F2C:
	push bp
	lea bp, _g_3D20
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	mov al, byte ptr es:[di]
	inc di
	mov ah, al
	xlat byte ptr cs:[bx]
	xchg bx, dx
	xchg al, ah
	xlat byte ptr cs:[bx]
	xchg bx, dx
	mov cl, byte ptr [si]
	inc si
	xor ah, cl
	and ah, al
	xor ah, cl
	mov byte ptr [bp], ah
	inc bp
	pop bp
	pop ds
	pop di
	pop si
	pop bp
	retf
_o03_3258_0F04	endp

_o03_3258_175F	proc	far
	push bp
	mov bp, sp
	push si
	push di
	les di, dword ptr [bp+6]
	lea si, _g_3D20
	mov bx, word ptr [bp+0Ah]
	shr bx, 1
	sub bx, 6
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	movsw
	movsw
	movsw
	add di, bx
	pop di
	pop si
	pop bp
	retf
_o03_3258_175F	endp

S03C_TEXT	ends
	end
