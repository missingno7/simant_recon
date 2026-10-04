; Display driver S00, object 2 of code frame 31AD (after the LINK fill byte at 31AD:2AB3).
; Overlay section S00, code frame 31AD, linear 34584-35A65.
; Genuine assembly, reproduced byte for byte by MASM 5.10.  Evidence against compiler output:
; framed procs save "push si; push di" (MSC always saves DI first, probe ASM-2 in
; work/ovlA/probe), the EGA/VGA sequencer and graphics controller are programmed
; with out dx loops, raster operations are selected by self-modifying code (instruction
; templates copied over loop instructions with "mov cs:[...],ax"), and near subroutines
; return with retn inside far procs.  The segment ends at an odd offset (31AD:2AB3); LINK

_DATA	segment word public 'DATA'
	extrn	_g_3D20:byte
	extrn	_g_3DAE:byte
	extrn	_g_3DFC:byte
	extrn	_g_3DB0:byte
	extrn	_g_3DB4:byte
	extrn	_g_3DD4:byte
_DATA	ends
DGROUP	group	_DATA

	extrn	_f_1B4E_015B:far
	extrn	_o00_31AD_0CF9:far
	extrn	_o00_31AD_145E:far

S00B_TEXT	segment word public 'CODE'
	assume	cs:S00B_TEXT, ds:DGROUP

	public	_o00_31AD_2AB4
	public	_o00_31AD_2AE5
	public	_o00_31AD_2B1A
	public	_o00_31AD_2FDA
	public	_o00_31AD_300B
	public	_o00_31AD_303F

_o00_31AD_2AB4	proc	far
	push bp
	mov bp, sp
	sub sp, 8
	push si
	push di
	mov cx, 15Eh
	xor ax, ax
	mov di, OFFSET DGROUP:_g_3DFC
	mov es, word ptr _g_3DAE
L2AC8:
	stosw
	add ax, 50h
	loop L2AC8
	call far ptr _o00_31AD_145E
	mov ax, 10h
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	xor ax, ax
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_31AD_2AB4	endp

_o00_31AD_2AE5	proc	far
	push bp
	mov bp, sp
	sub sp, 8
	push si
	push di
	mov cx, 1E0h
	mov word ptr _g_3DB4, cx
	xor ax, ax
	mov di, OFFSET DGROUP:_g_3DFC
	mov es, word ptr _g_3DAE
L2AFD:
	stosw
	add ax, 50h
	loop L2AFD
	call far ptr _o00_31AD_145E
	mov ax, 12h
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	xor ax, ax
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_31AD_2AE5	endp

_o00_31AD_2B1A	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _g_3DD4
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
	mov ds, word ptr _g_3DB0
	push bp
	lea bp, _g_3D20
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
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o00_31AD_2B1A	endp

_o00_31AD_2FDA	proc	far
	push bp
	mov bp, sp
	les bx, dword ptr [bp+0Eh]
	push es
	push bx
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	call far ptr _o00_31AD_2B1A
	add sp, 8
	mov ax, 10h
	push ax
	push ax
	push ds
	lea ax, _g_3D20
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o00_31AD_0CF9
	add sp, 0Ch
	pop bp
	retf
_o00_31AD_2FDA	endp

_o00_31AD_300B	proc	far
	push bp
	mov bp, sp
	push word ptr [bp+12h]
	les bx, dword ptr [bp+0Eh]
	push es
	push bx
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	call far ptr _o00_31AD_303F
	add sp, 0Ah
	mov ax, 10h
	push ax
	push ax
	push ds
	lea ax, _g_3D20
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o00_31AD_0CF9
	add sp, 0Ch
	pop bp
	retf
_o00_31AD_300B	endp

_o00_31AD_303F	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _g_3DD4
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
	mov ds, word ptr _g_3DB0
	cmp byte ptr [bp+0Eh], 0
	jne L3069
	jmp near ptr L3521
L3069:
	cmp byte ptr [bp+0Eh], 3
	jne L3072
	jmp near ptr L3A8B
L3072:
	push bp
	lea bp, _g_3D20
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
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
L3521:
	push bp
	lea bp, _g_3D20
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
	lea bp, _g_3D20
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
_o00_31AD_303F	endp

S00B_TEXT	ends
	end
