; Display driver S00, module 1: mini-map table builders.
; Overlay section S00, code frame 3126, linear 31260-31AD3.

_DATA	segment word public 'DATA'
	extrn	_g_3DB2:byte
; S00A private data, first part (DGROUP:1F9E-2065): the two 100-byte dither tables the
; mini-map builders index (o00_3126_0000/0137/026A/03A9/04D8/06A3).  Not placed yet: DGROUP
; 2066-2117 (EGA palette, dword table, the dispatch table at 2098 whose 25 entries reach S00B procs
; as externals, its far pointer at 20FC, bit masks, palette map); its split between this object
; and S00B is open (build/workers/data/s27_map.md).
_g_1F9E	db	0, 0, 0, 0, 0FFh, 0, 0, 0, 0, 0FFh, 0, 0
	db	0FFh, 0FFh, 0, 0, 0, 0, 0FFh, 0, 0FFh, 0, 0FFh, 0
	db	0, 0FFh, 0FFh, 0, 0FFh, 0FFh, 0FFh, 0, 0, 0, 0, 0FFh
	db	0FFh, 0, 0, 0FFh, 0, 0FFh, 0, 0FFh, 0FFh, 0FFh, 0, 0FFh
	db	0, 0, 0FFh, 0FFh, 0FFh, 0, 0FFh, 0FFh, 0, 0FFh, 0FFh, 0FFh
	db	0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 055h, 0, 055h, 0FFh, 055h, 0, 055h
	db	0FFh, 0, 0, 0, 055h, 0AAh, 0, 0, 0, 0FFh, 0, 0
	db	0AAh, 0FFh, 0, 0, 0FFh, 0FFh, 0, 0, 055h, 055h, 0AAh, 0
	db	0, 0, 0FFh, 0
_g_2002	db	0FFh, 0FFh, 0FFh, 0FFh, 0, 0FFh, 0FFh, 0FFh, 0, 0, 0FFh, 0FFh
	db	0, 0, 0FFh, 0, 0FFh, 0, 0FFh, 0FFh, 0FFh, 0, 0FFh, 0
	db	0FFh, 0, 0, 0, 0FFh, 0FFh, 0, 0FFh, 0, 0FFh, 0, 0FFh
	db	0, 0FFh, 0, 0, 0, 0FFh, 0FFh, 0, 0, 0FFh, 0FFh, 0
	db	0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0, 0, 0, 0, 0FFh
	db	0, 0, 0, 0, 0, 0FFh, 0FFh, 0AAh, 0, 0FFh, 0FFh, 0AAh
	db	0, 0FFh, 0FFh, 0FFh, 0, 055h, 0FFh, 0FFh, 0, 0, 0FFh, 0FFh
	db	0, 0, 0FFh, 055h, 0, 0, 0FFh, 0, 0AAh, 0, 0FFh, 0AAh
	db	0FFh, 0, 0FFh, 0FFh
_DATA	ends
DGROUP	group	_DATA

	extrn	_o15_384C_0000:far

S00A_TEXT	segment word public 'CODE'
	assume	cs:S00A_TEXT, ds:DGROUP

	public	_o00_3126_0000
	public	_o00_3126_0137
	public	_o00_3126_026A
	public	_o00_3126_03A9
	public	_o00_3126_04D8
	public	_o00_3126_06A3
	public	_o00_3126_086E

_o00_3126_0000	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lea bx, _g_1F9E
	mov cx, 40h
L0013:
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di], al
	mov byte ptr es:[di+200h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+100h], dl
	mov byte ptr es:[di+300h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di+40h], al
	mov byte ptr es:[di+240h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+140h], dl
	mov byte ptr es:[di+340h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di+80h], al
	mov byte ptr es:[di+280h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+180h], dl
	mov byte ptr es:[di+380h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di+0C0h], al
	mov byte ptr es:[di+2C0h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+1C0h], dl
	mov byte ptr es:[di+3C0h], dl
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di], al
	or byte ptr es:[di+200h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+100h], dl
	or byte ptr es:[di+300h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di+40h], al
	or byte ptr es:[di+240h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+140h], dl
	or byte ptr es:[di+340h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di+80h], al
	or byte ptr es:[di+280h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+180h], dl
	or byte ptr es:[di+380h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di+0C0h], al
	or byte ptr es:[di+2C0h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+1C0h], dl
	or byte ptr es:[di+3C0h], dl
	sub bx, 3
	inc di
	dec cx
	je L0132
	jmp L0013
L0132:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o00_3126_0000	endp

_o00_3126_0137	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lea bx, _g_1F9E
	mov cx, 20h
L014A:
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di], al
	mov byte ptr es:[di+100h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+80h], dl
	mov byte ptr es:[di+180h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di+20h], al
	mov byte ptr es:[di+120h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+0A0h], dl
	mov byte ptr es:[di+1A0h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di+40h], al
	mov byte ptr es:[di+140h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+0C0h], dl
	mov byte ptr es:[di+1C0h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0F0h
	mov byte ptr es:[di+60h], al
	mov byte ptr es:[di+160h], al
	rol dl, 1
	and dl, 0F0h
	mov byte ptr es:[di+0E0h], dl
	mov byte ptr es:[di+1E0h], dl
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di], al
	or byte ptr es:[di+100h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+80h], dl
	or byte ptr es:[di+180h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di+20h], al
	or byte ptr es:[di+120h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+0A0h], dl
	or byte ptr es:[di+1A0h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di+40h], al
	or byte ptr es:[di+140h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+0C0h], dl
	or byte ptr es:[di+1C0h], dl
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	mov dl, al
	and al, 0Fh
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+160h], al
	rol dl, 1
	and dl, 0Fh
	or byte ptr es:[di+0E0h], dl
	or byte ptr es:[di+1E0h], dl
	sub bx, 3
	inc di
	dec cx
	je L0265
	jmp L014A
L0265:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o00_3126_0137	endp

_o00_3126_026A	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lea bx, _g_2002
	mov cx, 20h
L027D:
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di], al
	mov byte ptr es:[di+80h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+20h], al
	mov byte ptr es:[di+0A0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+40h], al
	mov byte ptr es:[di+0C0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+60h], al
	mov byte ptr es:[di+0E0h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di], al
	or byte ptr es:[di+80h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+20h], al
	or byte ptr es:[di+0A0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+40h], al
	or byte ptr es:[di+0C0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+0E0h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di], al
	or byte ptr es:[di+80h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+20h], al
	or byte ptr es:[di+0A0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+40h], al
	or byte ptr es:[di+0C0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+0E0h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di], al
	or byte ptr es:[di+80h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+20h], al
	or byte ptr es:[di+0A0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+40h], al
	or byte ptr es:[di+0C0h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+0E0h], al
	sub bx, 3
	inc di
	dec cx
	je L03A4
	jmp L027D
L03A4:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o00_3126_026A	endp

_o00_3126_03A9	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	lea bx, _g_2002
	mov cx, 10h
L03BC:
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+40h], al
	mov byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+50h], al
	mov byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+60h], al
	mov byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0C0h
	mov byte ptr es:[di+70h], al
	mov byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+40h], al
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+50h], al
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 30h
	or byte ptr es:[di+70h], al
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+40h], al
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+50h], al
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 0Ch
	or byte ptr es:[di+70h], al
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+40h], al
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+50h], al
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+60h], al
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 3
	or byte ptr es:[di+70h], al
	or byte ptr es:[di+30h], al
	sub bx, 3
	inc di
	dec cx
	je L04D3
	jmp L03BC
L04D3:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o00_3126_03A9	endp

_o00_3126_04D8	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lea bx, _g_1F9E
	cmp word ptr _g_3DB2, 140h
	jne L04EE
	lea bx, _g_2002
L04EE:
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	mov cx, 10h
L04F7:
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di+30h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di+20h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di+30h], al
	sub bx, 3
	inc di
	dec cx
	je L069E
	jmp L04F7
L069E:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o00_3126_04D8	endp

_o00_3126_06A3	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lea bx, _g_1F9E
	cmp word ptr _g_3DB2, 140h
	jne L06B9
	lea bx, _g_2002
L06B9:
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+0Ah]
	mov cx, 8
L06C2:
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 80h
	mov byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 40h
	or byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 20h
	or byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 10h
	or byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 8
	or byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 4
	or byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 2
	or byte ptr es:[di+18h], al
	sub bx, 3
	lodsb
	shl al, 1
	shl al, 1
	mov ah, al
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di+8], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di+10h], al
	inc bx
	mov al, ah
	xlat byte ptr ss:[bx]
	and al, 1
	or byte ptr es:[di+18h], al
	sub bx, 3
	inc di
	dec cx
	je L0869
	jmp L06C2
L0869:
	pop ds
	pop di
	pop si
	pop bp
	retf
_o00_3126_06A3	endp

_o00_3126_086E	proc	far
	jmp far ptr _o15_384C_0000
_o00_3126_086E	endp

S00A_TEXT	ends
	end
