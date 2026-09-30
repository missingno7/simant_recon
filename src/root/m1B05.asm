; Root module 1B05: LZSS decompression (4096-byte ring buffer) from memory or from a file.
; Root code frame 1B05, linear 1B058-1B285.
; Genuine assembly: a decoder state machine that resumes mid-token (State), DGROUP variables
; addressed with ss: while DS points at the input, DS switched between input and ring buffer inside
; the loop, xchg bx,cx ring copying, "and ax,ax" tests and "mov ax,0" (MSC emits or r,r / sub r,r),
; BP frames without stack check and 'pop bp' without 'mov sp,bp' (rule ASM-1).

	extrn	_fd_4F6F_0000:byte		; 4096-byte ring buffer (far segment 4F6F)

_DATA	segment word public 'DATA'
RingBuf		dd	_fd_4F6F_0000	; ring buffer
Threshold	dw	2		; match length bias
SrcPtr		dd	0		; compressed input
SrcCount	dw	0		; input bytes left
RingPos		dw	0		; r
Flags		dw	0		; flag byte (AH = remaining bits marker)
SaveDX		dw	0
SaveCX		dw	0		; match position
MatchLen	dw	0		; match bytes left
State		dw	1		; where decoding stopped (0 = continue)
ReadBuf		db	256 dup (0)	; file read buffer
ReadSize	dw	100h
ReadPtr		dd	DGROUP:ReadBuf
Handle		dw	0
_DATA	ends
DGROUP	group	_DATA

	extrn	_close:far
	extrn	_open:far
	extrn	_read:far

LZSS_TEXT	segment word public 'CODE'
	assume	cs:LZSS_TEXT, ds:DGROUP

	public	_f_1B05_0008
	public	_f_1B05_0046
	public	_f_1B05_0178
	public	_f_1B05_018E
	public	_f_1B05_01C7
	public	_f_1B05_022A

_f_1B05_0008	proc	far
	push bp
	mov bp, sp
	push di
	mov cx, 0FEEh
	les di, dword ptr RingBuf
	mov al, 20h
	rep stosb
	mov word ptr RingPos, 0FEEh
	mov word ptr Flags, 0
	mov word ptr State, 0
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+8]
	mov word ptr SrcPtr, ax
	mov word ptr SrcPtr+2, dx
	mov ax, word ptr [bp+0Ah]
	and ax, ax
	jns L0040
	mov ax, 7FFFh
L0040:
	mov word ptr SrcCount, ax
	pop di
	pop bp
	retf
_f_1B05_0008	endp

_f_1B05_0046	proc	far
	push bp
	mov bp, sp
	sub sp, 4
	push di
	push si
	mov word ptr [bp-2], 0
	mov bx, word ptr RingPos
	mov dx, word ptr SaveDX
	mov cx, word ptr SaveCX
	push ds
	mov ax, word ptr RingBuf+2
	mov word ptr [bp-4], ax
	mov ax, word ptr Flags
	les di, dword ptr [bp+6]
	lds si, dword ptr SrcPtr
	assume	ds:nothing		; DS = input or ring buffer until pop ds
	cmp word ptr ss:State, 0
	je L00A6
	dec word ptr ss:State
	je L00AD
	dec word ptr ss:State
	je L00BB
	dec word ptr ss:State
	je L00E4
	dec word ptr ss:State
	je L00EE
	mov ds, word ptr [bp-4]
	jmp near ptr L0136
L009A:
	mov di, 1
	jmp near ptr L0157
L00A0:
	mov di, 2
	jmp near ptr L0157
L00A6:
	shr ax, 1
	test ah, 1
	jne L00B7
L00AD:
	dec word ptr ss:SrcCount
	js L009A
	lodsb
	mov ah, 0FFh
L00B7:
	test al, 1
	je L00E4
L00BB:
	dec word ptr ss:SrcCount
	js L00A0
	mov dl, byte ptr [si]
	inc si
	mov byte ptr es:[di], dl
	inc di
	mov ds, word ptr [bp-4]
	mov byte ptr ds:_fd_4F6F_0000[bx], dl
	mov ds, word ptr ss:SrcPtr+2
	inc bx
	and bx, 0FFFh
	inc word ptr [bp-2]
	dec word ptr [bp+0Ah]
	je L0154
	jmp L00A6
L00E4:
	dec word ptr ss:SrcCount
	js L014A
	mov cl, byte ptr [si]
	inc si
L00EE:
	dec word ptr ss:SrcCount
	js L0145
	mov dl, byte ptr [si]
	inc si
	mov ch, dl
	shr ch, 1
	shr ch, 1
	shr ch, 1
	shr ch, 1
	and dl, 0Fh
	add dl, byte ptr ss:Threshold
	xor dh, dh
	mov word ptr ss:MatchLen, dx
	mov ds, word ptr [bp-4]
L0114:
	xchg bx, cx
	mov dl, byte ptr ds:_fd_4F6F_0000[bx]
	inc bx
	and bx, 0FFFh
	mov byte ptr es:[di], dl
	inc di
	xchg bx, cx
	mov byte ptr ds:_fd_4F6F_0000[bx], dl
	inc bx
	and bx, 0FFFh
	inc word ptr [bp-2]
	dec word ptr [bp+0Ah]
	je L014F
L0136:
	dec word ptr ss:MatchLen
	jns L0114
	mov ds, word ptr ss:SrcPtr+2
	jmp L00A6
L0145:
	mov di, 4
	jmp short L0157
L014A:
	mov di, 3
	jmp short L0157
L014F:
	mov di, 5
	jmp short L0157
L0154:
	mov di, 0
L0157:
	pop ds
	assume	ds:DGROUP
	mov word ptr State, di
	mov word ptr Flags, ax
	mov word ptr RingPos, bx
	mov word ptr SrcPtr, si
	mov word ptr SaveDX, dx
	mov word ptr SaveCX, cx
	mov ax, word ptr [bp-2]
	pop si
	pop di
	mov sp, bp
	pop bp
	retf
_f_1B05_0046	endp

_f_1B05_0178	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+6]
	mov word ptr ReadPtr, bx
	mov word ptr ReadPtr+2, es
	mov ax, word ptr [bp+0Ah]
	mov word ptr ReadSize, ax
	pop bp
	retf
_f_1B05_0178	endp

_f_1B05_018E	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+6]
	mov ax, 8000h
	push ax
	push es
	push bx
	call far ptr _open
	add sp, 6
	mov word ptr Handle, ax
	and ax, ax
	jg L01AE
	mov ax, 0
	jmp short L01C5
L01AE:
	mov ax, word ptr ReadPtr
	mov dx, word ptr ReadPtr+2
	xor bx, bx
	push bx
	push dx
	push ax
	call far ptr _f_1B05_0008
	add sp, 6
	mov ax, 1
L01C5:
	pop bp
	retf
_f_1B05_018E	endp

_f_1B05_01C7	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	xor ax, ax
	mov word ptr [bp-2], ax
	cmp word ptr SrcCount, ax
	jg L01FD
L01D8:
	push word ptr ReadSize
	les bx, dword ptr ReadPtr
	mov word ptr SrcPtr, bx
	mov word ptr SrcPtr+2, es
	push es
	push bx
	push word ptr Handle
	call far ptr _read
	add sp, 8
	and ax, ax
	jle L0223
	mov word ptr SrcCount, ax
L01FD:
	mov ax, word ptr [bp+0Ah]
	sub ax, word ptr [bp-2]
	push ax
	push word ptr [bp+8]
	mov ax, word ptr [bp+6]
	add ax, word ptr [bp-2]
	push ax
	call far ptr _f_1B05_0046
	add sp, 6
	add word ptr [bp-2], ax
	mov ax, word ptr [bp+0Ah]
	cmp word ptr [bp-2], ax
	jne L01D8
	jmp short L0226
L0223:
	mov ax, word ptr [bp-2]
L0226:
	mov sp, bp
	pop bp
	retf
_f_1B05_01C7	endp

_f_1B05_022A	proc	far
	push word ptr Handle
	call far ptr _close
	pop ax
	retf
_f_1B05_022A	endp

LZSS_TEXT	ends
	end
