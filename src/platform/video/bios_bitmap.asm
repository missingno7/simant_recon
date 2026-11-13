; Provides video BIOS operations and low level bitmap and text entry points. It includes palette
; and pen colour handling and accented character folding for the small font.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: resident code; segment 1B4E; complete original translation unit.
; Windows: GR, from recorded function pairs in the Windows symbol inventory.
; Build profile: masm510; /Mx.
;
; Root code frame 1B4E, linear 1B4EC-1B736.
; Genuine assembly: frameless register procs (xchg/stosw loops, rep movsw with DS swapped through ES),
; video BIOS int 10h wrappers, a fold table in the code segment read with cs:, push si; push di and
; push ds; push di saves (MSC saves DI first, rule ASM-2), pop bp without mov sp,bp (ASM-1).

_DATA	segment word public 'DATA'
	extrn	_gfx_put_picture_hook:byte
	extrn	_gfx_put_image_hook:byte
	extrn	_gfx_set_attributes_hook:byte
	public	_gfx_row_scratch, _gfx_text_pen_x, _gfx_text_pen_y, _gfx_secondary_font, _gfx_primary_font_offset, _gfx_primary_font_segment, _gfx_screen_bitmap_offset, _gfx_screen_bitmap_segment
	public	_gfx_video_segment, _gfx_screen_width_pixels, _gfx_screen_height_pixels, _gfx_screen_row_bytes, _gfx_left_edge_masks, _gfx_right_edge_masks, _g_3DD2, _gfx_cursor_draw_lock
	public	_gfx_active_font_offset, _gfx_active_font_segment, _gfx_font_glyph_stride, _gfx_font_height_pixels, _fontWidth, __foreColor, _g_3DE1, _g_3DE2
	public	_g_3DE3, _g_3DE4, _g_3DE5, _gfx_clip_left_pixels, _gfx_clip_right_pixels, _g_3DEA, _g_3DEC
	public	_g_3DED, _g_3DEE, _g_3DEF, _g_3DF1, _g_3DF2, _gfx_empty_callback_pointer, _gfx_callback_table_pointer, _g_3DFC
	public	_gfx_colour_translation, _g_41D0, _g_4220
_gfx_row_scratch		db	128 dup (0)	; scratch bitmap row buffer
_gfx_text_pen_x		dw	0		; text pen x, y
_gfx_text_pen_y		dw	0
_gfx_secondary_font		dd	0		; font objects
_gfx_primary_font_offset		dw	0
_gfx_primary_font_segment		dw	0
_gfx_screen_bitmap_offset		dw	0		; screen bitmap (DGROUP:0 until the driver sets it)
_gfx_screen_bitmap_segment		dw	DGROUP
_gfx_video_segment		dw	0A000h		; video segment
_gfx_screen_width_pixels		dw	640		; screen width, height, bytes per row
_gfx_screen_height_pixels		dw	350
_gfx_screen_row_bytes		dw	80
		db	9 dup (0)
_gfx_left_edge_masks		db	0FFh, 7Fh, 3Fh, 1Fh, 0Fh, 07h, 03h, 01h, 00h	; left edge masks
_gfx_right_edge_masks		db	80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh, 0FFh	; right edge masks
_g_3DD2		dw	0
_gfx_cursor_draw_lock		dw	0
_gfx_active_font_offset		dw	0		; current font bitmap (far pointer)
_gfx_active_font_segment		dw	0
_gfx_font_glyph_stride		dw	0
_gfx_font_height_pixels		dw	0		; character cell height, width
_fontWidth		dw	8
__foreColor		db	0Fh		; pen colour
_g_3DE1		db	0
_g_3DE2		db	0
_g_3DE3		db	0
_g_3DE4		db	0		; fill pattern
_g_3DE5		db	0
_gfx_clip_left_pixels	dw	0
_gfx_clip_right_pixels	dw	0
_g_3DEA		dw	0
_g_3DEC		db	0
_g_3DED		db	0
_g_3DEE		db	0
_g_3DEF		db	0
		db	0
_g_3DF1		db	0
_g_3DF2		dw	0
_gfx_empty_callback_pointer		dd	_gfx_empty_driver_callback	; empty driver entry
_gfx_callback_table_pointer		dd	_gfx_set_attributes_hook		; driver entry table (25 far pointers)
_g_3DFC		db	964 dup (0)
_gfx_colour_translation		db	0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15	; colour map
		; 16-byte fill patterns
_g_41D0	label	byte
		db	55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh
		db	0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h
		db	16 dup (0FFh)
		db	16 dup (0)
		db	10h, 10h, 04h, 04h, 10h, 10h, 04h, 04h, 10h, 10h, 04h, 04h, 10h, 10h, 04h, 04h
_g_4220		db	16 dup (0)
		db	44h, 44h, 22h, 22h, 11h, 11h, 88h, 88h, 44h, 44h, 22h, 22h, 11h, 11h, 88h, 88h
		db	55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh
		db	0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h
		db	16 dup (0FFh)
		db	44h, 44h, 00h, 00h, 11h, 11h, 00h, 00h, 44h, 44h, 00h, 00h, 11h, 11h, 00h, 00h
		db	0CCh, 0CCh, 0FFh, 0FFh, 0EEh, 0EEh, 0FFh, 0FFh, 0CCh, 0CCh, 0FFh, 0FFh, 0EEh, 0EEh, 0FFh, 0FFh
		db	77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh
		db	16 dup (0FFh)
		db	16 dup (0)
		db	55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh
		db	16 dup (0)
		db	44h, 44h, 22h, 22h, 11h, 11h, 88h, 88h, 88h, 88h, 44h, 44h, 22h, 22h, 11h, 11h
		db	0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h, 0AAh, 0AAh, 55h, 55h
		db	0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h, 0BBh, 0BBh, 0DDh, 0DDh, 0EEh, 0EEh, 77h, 77h
		db	16 dup (0FFh)
		db	9 dup (12h)
_DATA	ends
DGROUP	group	_DATA

	extrn	_GPutStr:far

VIDEO_TEXT	segment word public 'CODE'
	assume	cs:VIDEO_TEXT, ds:DGROUP

	public	_gfx_empty_driver_callback
	public	_ConvColor
	public	_gfx_reset_driver_callbacks
	public	_GPutPic
	public	_GPutImg
	public	_gfx_put_fixed_font_chars
	public	_gfx_put_string_at_pen
	public	_gfx_put_fixed_font_char
	public	_gfx_video_bios_ax
	public	_gfx_install_driver_callbacks
	public	_gfx_set_dac_palette_inplace
	public	_gfx_set_ega_palette
	public	_gfx_set_dac_palette
	public	_gfx_set_border_colour
	public	_gfx_get_bios_video_mode
	public	_gfx_set_bios_video_mode

_gfx_empty_driver_callback	proc	far
	retf
_gfx_empty_driver_callback	endp

_ConvColor	proc	far
	push bp
	mov bp, sp
	lea bx, _gfx_colour_translation
	mov cx, word ptr [bp+6]
	mov al, cl
	and al, 0Fh
	xlat
	and cl, 0F0h
	or cl, al
	mov ax, cx
	pop bp
	retf
_ConvColor	endp

_gfx_reset_driver_callbacks	proc	far
	push di
	les bx, dword ptr _gfx_empty_callback_pointer
	mov ax, es
	les di, dword ptr _gfx_callback_table_pointer
	mov cx, 19h
L0033:
	xchg bx, ax
	stosw
	xchg bx, ax
	stosw
	loop L0033
	pop di
	retf
_gfx_reset_driver_callbacks	endp

_GPutPic	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+0Ah]
	mov ax, word ptr es:[bx]
	mov cx, word ptr es:[bx+2]
	push cx
	push ax
	push es
	add bx, 4
	push bx
	push word ptr [bp+8]
	push word ptr [bp+6]
	call dword ptr _gfx_put_picture_hook
	add sp, 0Ch
	pop bp
	retf
_GPutPic	endp

_GPutImg	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+0Ah]
	mov ax, word ptr es:[bx]
	mov cx, word ptr es:[bx+2]
	push cx
	push ax
	push es
	add bx, 4
	push bx
	push word ptr [bp+8]
	push word ptr [bp+6]
	call dword ptr _gfx_put_image_hook
	add sp, 0Ch
	pop bp
	retf
_GPutImg	endp

_gfx_put_fixed_font_chars	proc	far
	push bp
	mov bp, sp
	push si
	push di
	mov di, word ptr [bp+6]
	push word ptr _gfx_font_height_pixels
	les si, dword ptr [bp+0Ah]
	mov bx, word ptr [bp+8]
	sub di, word ptr _fontWidth
L0097:
	mov al, byte ptr es:[si]
	inc si
	and al, al
	je L00BB
	cbw
	add di, word ptr _fontWidth
	js L0097
	push es
	push ax
	push word ptr [bp+8]
	push di
	call far ptr _gfx_put_fixed_font_char
	add sp, 6
	pop es
	cmp di, word ptr _gfx_screen_width_pixels
	jb L0097
L00BB:
	add di, word ptr _fontWidth
	mov word ptr _gfx_text_pen_x, di
	mov ax, word ptr [bp+8]
	mov word ptr _gfx_text_pen_y, ax
	pop ax
	pop di
	pop si
	pop bp
	retf
_gfx_put_fixed_font_chars	endp

_gfx_put_string_at_pen	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+6]
	push es
	push bx
	push word ptr _gfx_text_pen_y
	push word ptr _gfx_text_pen_x
	call far ptr _GPutStr
	add sp, 8
	pop bp
	retf
_gfx_put_string_at_pen	endp

; characters 80h-A7h folded to plain letters for the 6-pixel font
FoldTable	db	'cueaaaaceeeiiiAAEaAooouuyoucLYPfaiounNao'

_gfx_put_fixed_font_char	proc	far
	push bp
	mov bp, sp
	push si
	push di
	mov bx, word ptr _gfx_font_glyph_stride
	cmp bx, 6
	jne L0135
	test byte ptr [bp+0Ah], 80h
	je L0135
	mov cx, bx
	mov bx, word ptr [bp+0Ah]
	xor bh, bh
	mov al, byte ptr cs:[bx+FoldTable]
	mov byte ptr [bp+0Ah], al
	mov bx, cx
L0135:
	mov ax, bx
	mul byte ptr [bp+0Ah]
	les si, dword ptr _gfx_active_font_offset
	add si, ax
	push word ptr _gfx_font_height_pixels
	push word ptr _fontWidth
	push es
	push si
	push word ptr [bp+8]
	push word ptr [bp+6]
	call dword ptr _gfx_put_image_hook
	add sp, 0Ch
	pop di
	pop si
	pop bp
	retf
_gfx_put_fixed_font_char	endp

_gfx_video_bios_ax	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	int 10h
	pop bp
	retf
_gfx_video_bios_ax	endp

_gfx_install_driver_callbacks	proc	far
	push ds
	push di
	mov ax, es
	les di, dword ptr _gfx_callback_table_pointer
	mov ds, ax
	mov cx, 32h
	rep movsw
	pop di
	pop ds
	retf
_gfx_install_driver_callbacks	endp

_gfx_set_dac_palette_inplace	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	lds si, dword ptr [bp+6]
	les di, dword ptr [bp+6]
	mov cx, 300h
L0186:
	lodsb
	shr al, 1
	shr al, 1
	stosb
	loop L0186
	les dx, dword ptr [bp+6]
	mov bx, 0
	mov cx, 100h
	mov ax, 1012h
	int 10h
	pop ds
	pop di
	pop si
	pop bp
	retf
_gfx_set_dac_palette_inplace	endp

_gfx_set_ega_palette	proc	far
	push bp
	mov bp, sp
	les dx, dword ptr [bp+6]
	mov ax, 1002h
	int 10h
	pop bp
	retf
_gfx_set_ega_palette	endp

_gfx_set_dac_palette	proc	far
	push bp
	mov bp, sp
	sub sp, 33h
	push si
	push di
	push ds
	mov ax, ss
	mov es, ax
	cmp word ptr [bp+0Ah], 0
	jne L01C6
	mov word ptr [bp+0Ah], 100h
L01C6:
	cmp word ptr [bp+0Ah], 10h
	jne L01E4
	mov cx, 10h
	xor al, al
	lea di, [bp-31h]
L01D4:
	stosb
	inc al
	loop L01D4
	xor al, al
	stosb
	lea dx, [bp-31h]
	mov ax, 1002h
	int 10h
L01E4:
	lds si, dword ptr [bp+6]
	mov word ptr [bp-33h], 0
L01EC:
	lea di, [bp-31h]
	mov cx, word ptr [bp+0Ah]
	and cx, cx
	je L0221
	cmp cx, 10h
	jle L01FE
	mov cx, 10h
L01FE:
	sub word ptr [bp+0Ah], cx
	mov bx, cx
	add cx, cx
	add cx, bx
L0207:
	lodsb
	shr al, 1
	shr al, 1
	stosb
	loop L0207
	lea dx, [bp-31h]
	mov cx, bx
	mov bx, word ptr [bp-33h]
	add word ptr [bp-33h], cx
	mov ax, 1012h
	int 10h
	jmp L01EC
L0221:
	pop ds
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_gfx_set_dac_palette	endp

_gfx_set_border_colour	proc	far
	push bp
	mov bp, sp
	mov ax, 1001h
	mov bh, byte ptr [bp+6]
	int 10h
	pop bp
	retf
_gfx_set_border_colour	endp

_gfx_get_bios_video_mode	proc	far
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	xor ah, ah
	retf
_gfx_get_bios_video_mode	endp

_gfx_set_bios_video_mode	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	xor ah, ah
	int 10h
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	xor ah, ah
	pop bp
	retf
_gfx_set_bios_video_mode	endp

VIDEO_TEXT	ends
	end
