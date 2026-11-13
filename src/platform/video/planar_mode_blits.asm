; Sets up planar display modes and performs masked planar tile blits through a scratch buffer.
; It is the second object in frame 31AD and remains a separate file from the main raster
; routines.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: overlay section 0 (S00); segment 31AD, object starts at 2AB4; complete original
; translation unit.
; Windows: none (DOS only), based on the platform-specific code or DOS release data.
; Build profile: masm510; /Mx.
;
; The object begins at 31AD:2AB4 after the one-byte LINK fill at 31AD:2AB3.
; Genuine assembly: SI is saved before DI, unlike MSC (ASM-2); planar I/O,
; self-modifying raster templates and near returns inside far procs also
; exclude C compiler output. MASM 5.10 reproduces the complete object.

_DATA	segment word public 'DATA'
	extrn	_gfx_row_scratch:byte
	extrn	_gfx_screen_bitmap_segment:byte
	extrn	_g_3DFC:byte
	extrn	_gfx_video_segment:byte
	extrn	_gfx_screen_height_pixels:byte
	extrn	_gfx_cursor_draw_lock:byte
_DATA	ends
DGROUP	group	_DATA

	extrn	_gfx_video_bios_ax:far
	extrn	_gfx_planar_gputpics:far
	extrn	_gfx_planar_install_dispatch:far

S00B_TEXT	segment word public 'CODE'
	assume	cs:S00B_TEXT, ds:DGROUP

	public	_gfx_planar_init_640x350
	public	_gfx_planar_init_640x480
	public	_gfx_planar_compose_life_ems
	public	_gfx_planar_draw_life_ems
	public	_gfx_planar_draw_life_hires
	public	_gfx_planar_compose_life_hires

_gfx_planar_init_640x350	proc	far
	push bp
	mov bp, sp
	sub sp, 8
	push si
	push di
	mov cx, 15Eh
	xor ax, ax
	mov di, OFFSET DGROUP:_g_3DFC
	mov es, word ptr _gfx_screen_bitmap_segment
L2AC8:
	stosw
	add ax, 50h
	loop L2AC8
	call far ptr _gfx_planar_install_dispatch
	mov ax, 10h
	push ax
	call far ptr _gfx_video_bios_ax
	pop ax
	xor ax, ax
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_gfx_planar_init_640x350	endp

_gfx_planar_init_640x480	proc	far
	push bp
	mov bp, sp
	sub sp, 8
	push si
	push di
	mov cx, 1E0h
	mov word ptr _gfx_screen_height_pixels, cx
	xor ax, ax
	mov di, OFFSET DGROUP:_g_3DFC
	mov es, word ptr _gfx_screen_bitmap_segment
L2AFD:
	stosw
	add ax, 50h
	loop L2AFD
	call far ptr _gfx_planar_install_dispatch
	mov ax, 12h
	push ax
	call far ptr _gfx_video_bios_ax
	pop ax
	xor ax, ax
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_gfx_planar_init_640x480	endp

_gfx_planar_compose_life_ems	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _gfx_cursor_draw_lock
	mov ah, byte ptr [bp+8]
	mov al, 4
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push ds
	les di, dword ptr [bp+0Ah]
	mov si, word ptr [bp+6]
	mov ds, word ptr _gfx_video_segment
	push bp
	lea bp, _gfx_row_scratch
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	pop bp
	pop ds
	dec byte ptr _gfx_cursor_draw_lock
	pop di
	pop si
	pop bp
	retf
_gfx_planar_compose_life_ems	endp

_gfx_planar_draw_life_ems	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+0Eh]
	push es
	push bx
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	call far ptr _gfx_planar_compose_life_ems
	add sp, 8
	mov ax, 10h
	push ax
	push ax
	push ds
	lea ax, _gfx_row_scratch
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _gfx_planar_gputpics
	add sp, 0Ch
	pop bp
	retf
_gfx_planar_draw_life_ems	endp

_gfx_planar_draw_life_hires	proc	far
	push bp
	mov bp, sp
	push word ptr [bp+12h]
	les bx, dword ptr [bp+0Eh]
	push es
	push bx
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	call far ptr _gfx_planar_compose_life_hires
	add sp, 0Ah
	mov ax, 10h
	push ax
	push ax
	push ds
	lea ax, _gfx_row_scratch
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _gfx_planar_gputpics
	add sp, 0Ch
	pop bp
	retf
_gfx_planar_draw_life_hires	endp

_gfx_planar_compose_life_hires	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _gfx_cursor_draw_lock
	mov ah, byte ptr [bp+8]
	mov al, 4
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push ds
	les di, dword ptr [bp+0Ah]
	mov si, word ptr [bp+6]
	mov ds, word ptr _gfx_video_segment
	cmp byte ptr [bp+0Eh], 0
	jne L3069
	jmp near ptr L3521
L3069:
	cmp byte ptr [bp+0Eh], 3
	jne L3072
	jmp near ptr L3A8B
L3072:
	push bp
	lea bp, _gfx_row_scratch
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	add di, 4
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	pop bp
	pop ds
L3519:
	dec byte ptr _gfx_cursor_draw_lock
	pop di
	pop si
	pop bp
	retf
L3521:
	push bp
	lea bp, _gfx_row_scratch
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	pop bp
	pop ds
	jmp L3519
L3A8B:
	push bp
	lea bp, _gfx_row_scratch
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	mov dx, word ptr es:[di]
	inc di
	inc di
	mov cx, word ptr es:[di]
	inc di
	inc di
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	lodsw
	mov bx, word ptr es:[di]
	inc di
	inc di
	xor bx, ax
	and bx, dx
	xor bx, ax
	mov word ptr [bp], bx
	inc bp
	inc bp
	pop bp
	pop ds
	jmp L3519
_gfx_planar_compose_life_hires	endp

S00B_TEXT	ends
	end
