; Translates small map pixels into packed colour nibbles for the Tandy path. The two functions
; use adjacent high and low nibble colour tables.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: overlay section 3 (S03); segment 3253; complete original translation unit.
; Windows: _TEXT, from recorded function pairs in the Windows symbol inventory. This is outside
; the six named application groups.
; Build profile: masm510; /Mx.

_DATA	segment word public 'DATA'
; S03B mini-map xlat tables: byte colours, high nibbles, low nibbles.
_g_2308	db	0FFh, 0EEh, 0CCh, 044h, 0DDh, 055h, 011h, 0BBh, 0AAh, 022h, 066h, 066h
	db	0FFh, 077h, 088h, 0
_g_2318	db	0F0h, 0E0h, 0C0h, 040h, 0D0h, 050h, 010h, 0B0h, 0A0h, 020h, 060h, 060h
	db	0F0h, 070h, 080h, 0
; Windows_MakeTable1x1 adds 10h to BX after translating the first pixel.
; Its second xlat therefore uses the following low-nibble colour table.
_g_2328	db	0Fh, 0Eh, 0Ch, 04h, 0Dh, 05h, 01h, 0Bh
	db	0Ah, 02h, 06h, 06h, 0Fh, 07h, 08h, 0
_DATA	ends
DGROUP	group	_DATA

S03B_TEXT	segment word public 'CODE'
	assume	cs:S03B_TEXT, ds:DGROUP

	public	_gfx_tandy_map_duplicate_rows
	public	_Windows_MakeTable1x1

_gfx_tandy_map_duplicate_rows	proc	far
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
_gfx_tandy_map_duplicate_rows	endp

_Windows_MakeTable1x1	proc	far
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
_Windows_MakeTable1x1	endp

S03B_TEXT	ends
	end
