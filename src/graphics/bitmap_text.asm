; Draws a string with the bitmap font. It folds accented characters and supports underlining.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: resident code; segment 1FBD; complete original translation unit.
; Windows: GR, from recorded function pairs in the Windows symbol inventory.
; Build profile: masm510; /Mx.
;
; Root code frame 1FBD, linear 1FBD0-1FD27.
; Genuine assembly: push si; push di saves (MSC saves DI first, rule ASM-2) and a BP frame
; without stack check ending pop bp without mov sp,bp (ASM-1).

_DATA	segment word public 'DATA'
	extrn	_gfx_text_pen_x:byte
	extrn	_gfx_text_pen_y:byte
	extrn	_gfx_active_font_offset:byte
	extrn	_gfx_font_glyph_stride:byte
	extrn	_gfx_font_height_pixels:byte
	extrn	_fontWidth:byte
	extrn	_gfx_display_mode:byte
	public	_text_bitmap_width, _text_bitmap_height, _text_bitmap_pixels
_text_bitmap_width		dw	0		; text bitmap: width, height, pixel rows
_text_bitmap_height		dw	0
_text_bitmap_pixels		db	1040 dup (0)
_text_bitmap_string_copy		db	79 dup (0)	; copy of the string (at most 79 characters)
_g_5F1D		db	0
		db	160 dup (0)	; not referenced
_text_small_font_fold_table		db	'cueaaaaceeeiiiAAEaAooouuyoucLYPfaiounNao'	; folding of characters 80h-A7h
_DATA	ends
DGROUP	group	_DATA

	extrn	_GPutImg:far
	extrn	_gfx_put_fixed_font_chars:far

TEXTOUT_TEXT	segment word public 'CODE'
	assume	cs:TEXTOUT_TEXT, ds:DGROUP

	public	_GPutStr

_GPutStr	proc	far
	push bp
	mov bp, sp
	push si
	push di
	cmp byte ptr _gfx_display_mode, 6
	je L000E
	jne L0025
L000E:
	les ax, dword ptr [bp+0Ah]
	push es
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _gfx_put_fixed_font_chars
	add sp, 8
	pop di
	pop si
	pop bp
	retf
L0025:
	mov bl, byte ptr _gfx_font_height_pixels
	xor bh, bh
	mov word ptr _text_bitmap_height, bx
	mov ax, ds
	mov es, ax
	mov di, offset DGROUP:_text_bitmap_string_copy
	lds si, dword ptr [bp+0Ah]
	xor dl, dl
L003B:
	lodsb
	stosb
	or al, al
	je L004A
	inc dl
	cmp dl, 50h
	jne L003B
	dec dl
L004A:
	mov ax, DGROUP
	mov ds, ax
	or dl, dl
	jne L0057
	pop di
	pop si
	pop bp
	retf
L0057:
	cmp byte ptr _fontWidth, 8
	jne L00A5
	mov byte ptr _g_5F1D, 0
	mov al, byte ptr _fontWidth
	mul dl
	mov word ptr _text_bitmap_width, ax
	dec ax
	or ax, 7
	inc ax
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov dx, ax
	dec dx
	mov di, offset DGROUP:_text_bitmap_pixels
	mov si, offset DGROUP:_text_bitmap_string_copy
L007F:
	lodsb
	or al, al
	je L00A2
	mov cx, word ptr _gfx_font_glyph_stride
	mul cl
	push si
	lds si, dword ptr _gfx_active_font_offset
	add si, ax
	mov ax, di
L0093:
	movsb
	add di, dx
	loop L0093
	mov di, ax
	inc di
	pop si
	mov ax, es
	mov ds, ax
	jmp L007F
L00A2:
	jmp near ptr L0130
L00A5:
	mov byte ptr _g_5F1D, 0
	mov al, byte ptr _fontWidth
	mul dl
	mov word ptr _text_bitmap_width, ax
	dec ax
	or ax, 7
	inc ax
	shr ax, 1
	shr ax, 1
	shr ax, 1
	mov dx, ax
	mov di, offset DGROUP:_text_bitmap_pixels
	mov si, offset DGROUP:_text_bitmap_string_copy
L00C5:
	lodsb
	or al, al
	je L0130
	test al, 80h
	je L00D8
	push bx
	mov bl, al
	xor bh, bh
	mov al, byte ptr [bx+_text_small_font_fold_table]
	pop bx
L00D8:
	mov cx, word ptr _gfx_font_glyph_stride
	mul cl
	push si
	lds si, dword ptr _gfx_active_font_offset
	add si, ax
	push di
L00E6:
	lodsb
	and al, 0F0h
	mov byte ptr es:[di], al
	add di, dx
	loop L00E6
	pop di
	pop si
	mov ax, es
	mov ds, ax
	lodsb
	or al, al
	je L0130
	test al, 80h
	je L0109
	push bx
	mov bl, al
	xor bh, bh
	mov al, byte ptr [bx+_text_small_font_fold_table]
	pop bx
L0109:
	mov cx, word ptr _gfx_font_glyph_stride
	mul cl
	push si
	lds si, dword ptr _gfx_active_font_offset
	add si, ax
	push di
L0117:
	lodsb
	shr al, 1
	shr al, 1
	shr al, 1
	shr al, 1
	or byte ptr es:[di], al
	add di, dx
	loop L0117
	pop di
	inc di
	pop si
	mov ax, es
	mov ds, ax
	jmp L00C5
L0130:
	push ds
	mov ax, offset DGROUP:_text_bitmap_width
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _GPutImg
	add sp, 8
	mov ax, word ptr [bp+6]
	add ax, word ptr _text_bitmap_width
	mov word ptr _gfx_text_pen_x, ax
	mov ax, word ptr [bp+8]
	mov word ptr _gfx_text_pen_y, ax
	pop di
	pop si
	pop bp
	retf
_GPutStr	endp

TEXTOUT_TEXT	ends
	end
