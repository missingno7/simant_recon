; Display driver S00, module 1: mini-map table builders.
; Overlay section S00, code frame 3126, linear 31260-31AD3.

_DATA	segment word public 'DATA'
	extrn	_g_3DB2:byte
; S00 driver data (DGROUP:1F9E-20FF): dither tables of the mini-map builders, EGA palette and
; plane data used by S00B, the dispatch table the game calls through (entries in S00B, referenced
; as externals: RTLink keeps their relocations in per-symbol groups) and a far pointer to it.
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
D2066	db	0, 1, 010h, 030h, 4, 5, 014h, 7, 038h, 9, 2, 00Bh, 024h, 02Dh, 036h, 03Fh	; EGA attribute-controller palette registers 0-15
	db	0, 0
	public _g_2078, _g_20FC
_g_2078	dd	004000h, 008000h, 00C000h, 010000h, 020000h, 020000h, 020000h, 020000h
DispatchS00	label	dword
	dd	_gfx_planar_gsetattrib
	dd	_gfx_planar_select_small_font
	dd	_gfx_planar_select_big_font
	dd	_gfx_planar_gboxfill
	dd	_gfx_planar_gpatbox
	dd	_gfx_planar_ginvbox
	dd	_gfx_planar_gpicsize
	dd	_gfx_planar_gimgsize
	dd	_gfx_planar_capture_box
	dd	_gfx_planar_gputpics
	dd	_gfx_planar_put_picture_raw
	dd	_gfx_planar_gputimgs
	dd	_gfx_planar_put_image_raw
	dd	_gfx_planar_set_or
	dd	_gfx_planar_set_xor
	dd	_gfx_planar_set_and
	dd	_gfx_planar_set_copy
	dd	_gfx_planar_gline
	dd	_gfx_planar_draw_line_raw
	dd	_gfx_planar_dither_box
	dd	_gfx_planar_restore_text_mode
	dd	_gfx_planar_put_cached_tile
	dd	_gfx_planar_upload_tiles
	dd	_gfx_planar_set_raster_op
	dd	_gfx_planar_move_box
_g_20FC	dd	DGROUP:DispatchS00
_DATA	ends
DGROUP	group	_DATA

	extrn	_gfx_planar_dither_box:far
	extrn	_gfx_planar_gpatbox:far
	extrn	_gfx_planar_ginvbox:far
	extrn	_gfx_planar_gpicsize:far
	extrn	_gfx_planar_capture_box:far
	extrn	_gfx_planar_set_or:far
	extrn	_gfx_planar_set_xor:far
	extrn	_gfx_planar_set_and:far
	extrn	_gfx_planar_set_copy:far
	extrn	_gfx_planar_set_raster_op:far
	extrn	_gfx_planar_put_cached_tile:far
	extrn	_gfx_planar_gputpics:far
	extrn	_gfx_planar_put_picture_raw:far
	extrn	_gfx_planar_gimgsize:far
	extrn	_gfx_planar_gputimgs:far
	extrn	_gfx_planar_put_image_raw:far
	extrn	_gfx_planar_restore_text_mode:far
	extrn	_gfx_planar_gline:far
	extrn	_gfx_planar_draw_line_raw:far
	extrn	_gfx_planar_gsetattrib:far
	extrn	_gfx_planar_select_small_font:far
	extrn	_gfx_planar_select_big_font:far
	extrn	_gfx_planar_gboxfill:far
	extrn	_gfx_planar_upload_tiles:far
	extrn	_gfx_planar_move_box:far
	extrn	_o15_384C_0000:far

S00A_TEXT	segment word public 'CODE'
	assume	cs:S00A_TEXT, ds:DGROUP

	public	_gfx_planar_map128_pack2
	public	_gfx_planar_map64_pack2
	public	_gfx_planar_map128_pack4
	public	_gfx_planar_map64_pack4
	public	_gfx_planar_map128_pack8
	public	_gfx_planar_map64_pack8
	public	_gfx_planar_fatal_display_jump

_gfx_planar_map128_pack2	proc	far
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
_gfx_planar_map128_pack2	endp

_gfx_planar_map64_pack2	proc	far
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
_gfx_planar_map64_pack2	endp

_gfx_planar_map128_pack4	proc	far
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
_gfx_planar_map128_pack4	endp

_gfx_planar_map64_pack4	proc	far
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
_gfx_planar_map64_pack4	endp

_gfx_planar_map128_pack8	proc	far
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
_gfx_planar_map128_pack8	endp

_gfx_planar_map64_pack8	proc	far
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
_gfx_planar_map64_pack8	endp

_gfx_planar_fatal_display_jump	proc	far
	jmp far ptr _o15_384C_0000
_gfx_planar_fatal_display_jump	endp

S00A_TEXT	ends
	end
