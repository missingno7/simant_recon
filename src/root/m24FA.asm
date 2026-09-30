; Root module 24FA: byte search, 2-bit to 8-bit pixel expansion, byte inversion, breakpoint stub.
; Root code frame 24FA, linear 24FA4-25056.
; Genuine assembly: std/repne scasb/cld, a 4-byte xlat table in the code segment read with cs:,
; frameless-epilogue procs (pop bp without mov sp,bp) and push si; push di saves (rule ASM-2).

_DATA	segment word public 'DATA'
_DATA	ends
DGROUP	group	_DATA

BITS_TEXT	segment word public 'CODE'
	assume	cs:BITS_TEXT, ds:DGROUP

	public	_f_24FA_0004
	public	_f_24FA_0029
	public	_f_24FA_00A0
	public	_f_24FA_00B5

_f_24FA_0004	proc	far
	push bp
	mov bp, sp
	push di
	std
	les di, dword ptr [bp+6]
	mov al, byte ptr [bp+0Ah]
	mov cx, word ptr [bp+0Ch]
	repne scasb
	cld
	jne L001E
	mov dx, es
	mov ax, di
	inc ax
	jmp short L0022
L001E:
	xor dx, dx
	xor ax, ax
L0022:
	pop di
	pop bp
	retf
_f_24FA_0004	endp

; 2-bit pixel -> 8 pixels of the byte (0, 1, 2, 3 -> FFh, F0h, 0Fh, 0)
ExpandTable	db	0FFh, 0F0h, 0Fh, 0

_f_24FA_0029	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+6]
	lds si, dword ptr [bp+0Ah]
	mov dx, word ptr [bp+0Eh]
	inc dx
	shr dx, 1
L003B:
	mov cx, dx
L003D:
	mov ah, byte ptr [si]
	inc si
	mov bh, ah
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov ah, bh
	xor bh, bh
	mov al, byte ptr cs:[bx+ExpandTable]
	stosb
	dec cx
	je L0096
	mov bh, ah
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov ah, bh
	xor bh, bh
	mov al, byte ptr cs:[bx+ExpandTable]
	stosb
	dec cx
	je L0096
	mov bh, ah
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov ah, bh
	xor bh, bh
	mov al, byte ptr cs:[bx+ExpandTable]
	stosb
	dec cx
	je L0096
	mov bh, ah
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov ah, bh
	xor bh, bh
	mov al, byte ptr cs:[bx+ExpandTable]
	stosb
	dec cx
	je L0096
	jmp L003D
L0096:
	dec word ptr [bp+10h]
	jne L003B
	pop ds
	pop di
	pop si
	pop bp
	retf
_f_24FA_0029	endp

_f_24FA_00A0	proc	far
	push bp
	mov bp, sp
	push di
	mov cx, word ptr [bp+0Ah]
	les di, dword ptr [bp+6]
L00AA:
	mov al, byte ptr es:[di]
	not al
	stosb
	loop L00AA
	pop di
	pop bp
	retf
_f_24FA_00A0	endp

_f_24FA_00B5	proc	far
	int 3
_f_24FA_00B5	endp

BITS_TEXT	ends
	end
