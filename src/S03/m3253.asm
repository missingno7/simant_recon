; Display driver S03, module 2: mini-map tables.
; Overlay section S03, code frame 3253, linear 32538-3258C.

_DATA	segment word public 'DATA'
; S03B private data (DGROUP:2308-2327): the two 16-byte xlat tables of o03_3253_0008/002F.
_g_2308	db	0FFh, 0EEh, 0CCh, 044h, 0DDh, 055h, 011h, 0BBh, 0AAh, 022h, 066h, 066h
	db	0FFh, 077h, 088h, 0
_g_2318	db	0F0h, 0E0h, 0C0h, 040h, 0D0h, 050h, 010h, 0B0h, 0A0h, 020h, 060h, 060h
	db	0F0h, 070h, 080h, 0
_DATA	ends
DGROUP	group	_DATA

S03B_TEXT	segment word public 'CODE'
	assume	cs:S03B_TEXT, ds:DGROUP

	public	_o03_3253_0008
	public	_o03_3253_002F

_o03_3253_0008	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lea bx, _g_2308
	mov cx, word ptr [bp+0Eh]
	mov dx, cx
L001D:
	lodsb
	xlat byte ptr ss:[bx]
	add di, dx
	mov byte ptr es:[di], al
	sub di, dx
	stosb
	loop L001D
	pop ds
	pop di
	pop si
	pop bp
	retf
_o03_3253_0008	endp

_o03_3253_002F	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lea bx, _g_2318
	mov cx, word ptr [bp+0Eh]
	shr cx, 1
L0044:
	lodsb
	xlat byte ptr ss:[bx]
	mov ah, al
	lodsb
	add bx, 10h
	xlat byte ptr ss:[bx]
	sub bx, 10h
	or al, ah
	stosb
	loop L0044
	pop ds
	pop di
	pop si
	pop bp
	retf
_o03_3253_002F	endp

S03B_TEXT	ends
	end
