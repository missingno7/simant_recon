; Root module 2650: bit-aligned glyph blit (OR) between far bitmaps, byte-buffer clear.
; Root code frame 2650, linear 26506-26627.
; Genuine assembly: 'add bp,6' argument frames, BP reused as a loop counter, lodsw/xchg/shl/shr
; bit shifting with xchg ch,cl, xlat, rep stosw with 'adc di,-1' odd-byte fix, a mask table in the
; code segment, push es; push ds; push si; push di saves (MSC saves DI first, rule ASM-2).

_DATA	segment word public 'DATA'
	public	_fd_55B3_6770, _fd_55B3_6772, _glyph_edge_masks
_g_676C		dw	0		; source, destination segment
_g_676E		dw	0
_fd_55B3_6770	dw	0		; source, destination row bytes (set by module 25E7)
_fd_55B3_6772	dw	0
		dw	0		; not referenced
_g_6776		dw	0		; row count
_glyph_edge_masks label byte
		db	0FFh, 80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh	; not referenced (edge masks)
_DATA	ends
DGROUP	group	_DATA

BLIT_TEXT	segment word public 'CODE'
	assume	cs:BLIT_TEXT, ds:DGROUP

	public	_f_2650_000F
	public	_f_2650_0107

LeftMasks	db	0, 80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh, 0FFh
_f_2650_000F	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	mov cx, 3
	mov bx, word ptr [bp+0Ch]
	mov al, bl
	and al, 7
	mov si, bx
	shr si, cl
	mov dx, word ptr [bp+0Eh]
	mov ah, dl
	and ah, 7
	mov di, dx
	shr di, cl
	inc cx
	mov bx, ax
	les ax, dword ptr [bp]
	shr ax, cl
	mov word ptr _g_676C, es
	add word ptr _g_676C, ax
	mov ax, word ptr [bp]
	and ax, 0Fh
	add si, ax
	les ax, dword ptr [bp+4]
	shr ax, cl
	mov word ptr _g_676E, es
	add word ptr _g_676E, ax
	mov ax, word ptr [bp+4]
	and ax, 0Fh
	add di, ax
	mov cx, bx
	mov bx, word ptr [bp+8]
	mov bp, word ptr [bp+0Ah]
	mov dx, bx
	shr dx, 1
	shr dx, 1
	shr dx, 1
	mov word ptr _g_6776, dx
L0079:
	push si
	push di
	mov dx, word ptr _g_6776
	mov es, word ptr _g_676E
	mov ds, word ptr _g_676C
	or dx, dx
	je L00A2
L008B:
	lodsw
	xchg ah, al
	shl ax, cl
	xor al, al
	xchg cl, ch
	shr ax, cl
	xchg cl, ch
	xchg ah, al
	or word ptr es:[di], ax
	inc di
	dec si
	dec dx
	jne L008B
L00A2:
	mov ax, bx
	and ax, 7
	je L00CA
	mov dx, bx
	mov bx, offset LeftMasks
	xlat byte ptr cs:[bx]
	mov bx, dx
	xor dx, dx
	mov dh, al
	lodsw
	xchg ah, al
	shl ax, cl
	xor al, al
	xchg cl, ch
	and ax, dx
	shr ax, cl
	xchg cl, ch
	xchg ah, al
	or word ptr es:[di], ax
L00CA:
	pop di
	pop si
	dec bp
	je L0101
	mov ax, DGROUP
	mov ds, ax
	add si, word ptr _fd_55B3_6770
	add di, word ptr _fd_55B3_6772
	mov ax, si
	and si, 0Fh
	shr ax, 1
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add word ptr _g_676C, ax
	mov ax, di
	and di, 0Fh
	shr ax, 1
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add word ptr _g_676E, ax
	jmp L0079
L0101:
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_2650_000F	endp

_f_2650_0107	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	les di, dword ptr [bp]
	mov cx, word ptr [bp+4]
	xor ax, ax
	shr cx, 1
	rep stosw
	adc di, -1
	stosb
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_2650_0107	endp

BLIT_TEXT	ends
	end
