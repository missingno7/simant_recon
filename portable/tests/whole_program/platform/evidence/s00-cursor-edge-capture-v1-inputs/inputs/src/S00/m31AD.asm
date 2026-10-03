; Display driver S00 (EGA/VGA planar; dispatch table DGROUP:2098), object 1 of code frame 31AD.
; Overlay section S00, code frame 31AD, linear 31AD4-34583.
; Genuine assembly, reproduced byte for byte by MASM 5.10.  Evidence against compiler output:
; framed procs save "push si; push di" (MSC always saves DI first, probe ASM-2 in
; work/ovlA/probe), the EGA/VGA sequencer and graphics controller are programmed
; with out dx loops, raster operations are selected by self-modifying code (instruction
; templates copied over loop instructions with "mov cs:[...],ax"), and near subroutines
; return with retn inside far procs.  The segment ends at an odd offset (31AD:2AB3); LINK
; fills one 00 byte before the second object of the same segment (31AD:2AB4-3F95).
; The far pointers to the 25 entries live in the DGROUP dispatch table at 2098 (not reconstructed here).

_DATA	segment word public 'DATA'
	extrn	_fd_55B3_3DE6:byte
	extrn	_fd_55B3_3DE8:byte
	extrn	_g_2078:byte
	extrn	_g_20FC:byte
	extrn	_g_2100:byte
	extrn	_g_2108:byte
	extrn	_g_3D20:byte
	extrn	_g_3DA8:byte
	extrn	_g_3DAA:byte
	extrn	_g_3DAE:byte
	extrn	_g_3DB0:byte
	extrn	_g_3DB2:byte
	extrn	_g_3DB4:byte
	extrn	_g_3DB6:byte
	extrn	_g_3DC1:byte
	extrn	_g_3DCA:byte
	extrn	_g_3DD2:byte
	extrn	_g_3DD4:byte
	extrn	_g_3DD6:byte
	extrn	_g_3DD8:byte
	extrn	_g_3DDA:byte
	extrn	_g_3DDC:byte
	extrn	_g_3DDE:byte
	extrn	_g_3DE0:byte
	extrn	_g_3DE2:byte
	extrn	_g_3DEA:byte
	extrn	_g_3DEC:byte
	extrn	_g_3DED:byte
	extrn	_g_3DEE:byte
	extrn	_g_3DEF:byte
	extrn	_g_3DF2:byte
	extrn	_g_3DFC:byte
	extrn	_g_41C0:byte
	extrn	_g_4331:byte
	extrn	_g_4333:byte
	extrn	_g_4340:byte
	extrn	_g_4342:byte
	extrn	_g_4344:byte
	extrn	_g_4346:byte
	extrn	_g_4365:byte
	extrn	_g_4366:byte
	extrn	_g_5AAC:byte
	extrn	_g_5AAE:byte
	extrn	_g_912C:byte
	extrn	_g_9130:byte
_DATA	ends
DGROUP	group	_DATA

	extrn	_f_1B4E_015B:far
	extrn	_f_1B4E_0165:far
	extrn	_f_1B73_00D9:far
	extrn	_f_1B73_0196:far
	extrn	_f_1B73_04BB:far
	extrn	_f_1D8E_0384:far
	extrn	_f_1D8E_0435:far
	extrn	_f_1D8E_070E:far
	extrn	_f_1D8E_07F6:far

S00B_TEXT	segment word public 'CODE'
	assume	cs:S00B_TEXT, ds:DGROUP

	public	_o00_31AD_0004
	public	_o00_31AD_001C
	public	_o00_31AD_0122
	public	_o00_31AD_013A
	public	_o00_31AD_037C
	public	_o00_31AD_0394
	public	_o00_31AD_0522
	public	_o00_31AD_0550
	public	_o00_31AD_062A
	public	_o00_31AD_062E
	public	_o00_31AD_0632
	public	_o00_31AD_0636
	public	_o00_31AD_063C
	public	_o00_31AD_0647
	public	_o00_31AD_0839
	public	_o00_31AD_0CF9
	public	_o00_31AD_0D06
	public	_o00_31AD_0F56
	public	_o00_31AD_1002
	public	_o00_31AD_1065
	public	_o00_31AD_110C
	public	_o00_31AD_11FB
	public	_o00_31AD_1206
	public	_o00_31AD_1213
	public	_o00_31AD_142B
	public	_o00_31AD_145E
	public	_o00_31AD_1468
	public	_o00_31AD_1481
	public	_o00_31AD_148C
	public	_o00_31AD_1499
	public	_o00_31AD_1659
	public	_o00_31AD_166A
	public	_o00_31AD_168C
	public	_o00_31AD_16A9
	public	_o00_31AD_16E4
	public	_o00_31AD_16FC
	public	_o00_31AD_186A
	public	_o00_31AD_18BA
	public	_o00_31AD_1950
	public	_o00_31AD_1A8F
	public	_o00_31AD_1AC4
	public	_o00_31AD_1AE7
	public	_o00_31AD_1B49
	public	_o00_31AD_1B7D

_o00_31AD_0004	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_001C
	mov ax, S00B_TEXT
	push ax
	mov ax, 1Ch
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o00_31AD_0004	endp

_o00_31AD_001C	proc	far
	push bp
	mov bp, sp
	sub sp, 4
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0058
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0058
	cmp dx, word ptr _g_4342
	jl L0058
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0058
	cmp dx, word ptr _g_4340
	jl L0058
	call far ptr _f_1B73_0196
L0058:
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L0066
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L0066:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L0074
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L0074:
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, byte ptr _g_3DE0
	out dx, al
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov es, word ptr _g_3DB0
	mov dx, word ptr [bp+0Eh]
	and dx, 0Fh
	shl dx, 1
	shl dx, 1
	shl dx, 1
	shl dx, 1
	mov cx, word ptr [bp+0Ch]
	mov ax, word ptr [bp+8]
	mov bx, ax
	and bx, 3
	add bx, bx
	add dx, bx
	mov word ptr [bp+0Eh], dx
	sub cx, ax
	mov word ptr [bp+8], cx
	mov bl, byte ptr _g_3DB6
	xor bh, bh
	mul bx
	mov di, ax
	mov cl, 3
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 7
	sar ax, cl
	mov bh, al
	add di, ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	mov dl, al
	and dl, 7
	shr ax, cl
	mov dh, al
	call near ptr L0276
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L0118
	test byte ptr _g_4365, 0FFh
	je L010C
	test byte ptr _g_4331, 0FFh
	je L0118
	call far ptr _f_1B73_04BB
	jmp short L0118
L010C:
	test byte ptr _g_4366, 0FFh
	jne L0118
	call far ptr _f_1B73_00D9
L0118:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_31AD_001C	endp

_o00_31AD_0122	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_013A
	mov ax, S00B_TEXT
	push ax
	mov ax, 13Ah
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o00_31AD_0122	endp

_o00_31AD_013A	proc	far
	push bp
	mov bp, sp
	sub sp, 4
	push si
	push di
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L0150
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L0150:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L015E
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L015E:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0192
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0192
	cmp dx, word ptr _g_4342
	jl L0192
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0192
	cmp dx, word ptr _g_4340
	jl L0192
	call far ptr _f_1B73_0196
L0192:
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, byte ptr _g_3DE0
	out dx, al
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov es, word ptr _g_3DB0
	mov dx, word ptr [bp+0Eh]
	and dx, 0Fh
	shl dx, 1
	shl dx, 1
	shl dx, 1
	shl dx, 1
	mov cx, word ptr [bp+0Ch]
	mov ax, word ptr [bp+8]
	mov bx, ax
	add bx, bx
	and bx, 7
	add dx, bx
	mov word ptr [bp+0Eh], dx
	sub cx, ax
	mov word ptr [bp+8], cx
	mov di, ax
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov cl, 3
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 7
	shr ax, cl
	mov bh, al
	add di, ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	mov dl, al
	and dl, 7
	shr ax, cl
	mov dh, al
	push bx
	push cx
	push dx
	push si
	push di
	call near ptr L0276
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, byte ptr _g_3DE2
	out dx, al
	pop di
	pop si
	pop dx
	pop cx
	pop bx
	mov ax, word ptr cs:L037A
	mov word ptr cs:L02AF, ax
	mov word ptr cs:L0311, ax
	mov word ptr cs:L0358, ax
	call near ptr L0276
	mov ax, word ptr cs:L0378
	mov word ptr cs:L02AF, ax
	mov word ptr cs:L0311, ax
	mov word ptr cs:L0358, ax
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L026C
	test byte ptr _g_4365, 0FFh
	je L0260
	test byte ptr _g_4331, 0FFh
	je L026C
	call far ptr _f_1B73_04BB
	jmp short L026C
L0260:
	test byte ptr _g_4366, 0FFh
	jne L026C
	call far ptr _f_1B73_00D9
L026C:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0276:
	sub dh, bh
	mov bh, dh
	jne L0289
	mov ah, byte ptr [bx+_g_3DC1]
	mov bl, dl
	and ah, byte ptr [bx+_g_3DCA]
	jmp near ptr L034D
L0289:
	mov al, bl
	mov bl, dl
	cbw
	and al, al
	je L02D3
	push bx
	mov si, ax
	mov ah, byte ptr [si+_g_3DC1]
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	mov cx, word ptr [bp+8]
	mov si, word ptr [bp+0Eh]
L02AA:
	mov bh, byte ptr ss:[si+41D0h]
L02AF:
	and bh, bh
	and bh, ah
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	inc byte ptr es:[di]
	add di, word ptr ss:_g_3DB6
	add si, 2
	and si, 0F7h
	loop L02AA
	pop di
	inc di
	pop bx
	dec bh
L02D3:
	cmp bl, 7
	jne L02DC
	inc bh
	jmp short L02E3
L02DC:
	and bh, bh
	jne L02E3
	jmp L033D
L02E3:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov dx, word ptr [bp+8]
	mov al, byte ptr ss:_g_3DB6
	sub al, bh
	xor ah, ah
	mov word ptr [bp-2], ax
	mov word ptr [bp-4], dx
	xor ch, ch
	push di
	mov ah, bh
	push ds
	push bx
	mov bx, es
	mov ds, bx
	mov si, word ptr [bp+0Eh]
L030C:
	mov bh, byte ptr ss:[si+41D0h]
L0311:
	and bh, bh
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov cl, ah
	push si
	mov si, di
	rep movsb
	pop si
	add di, word ptr [bp-2]
	add si, 2
	and si, 0F7h
	dec word ptr [bp-4]
	jne L030C
	pop bx
	pop ds
	pop di
	cmp bl, 7
	jne L033D
	retn
L033D:
	mov al, bl
	cbw
	mov si, ax
	mov ah, byte ptr ss:[si+3DCAh]
	mov bl, bh
	xor bh, bh
	add di, bx
L034D:
	mov cx, word ptr [bp+8]
	mov si, word ptr [bp+0Eh]
L0353:
	mov bh, byte ptr ss:[si+41D0h]
L0358:
	and bh, bh
	and bh, ah
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	inc byte ptr es:[di]
	add di, word ptr ss:_g_3DB6
	add si, 2
	and si, 0F7h
	loop L0353
	retn
L0378:
	and bh, bh
L037A:
	not bh
_o00_31AD_013A	endp

_o00_31AD_037C	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_0394
	mov ax, S00B_TEXT
	push ax
	mov ax, 394h
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o00_31AD_037C	endp

_o00_31AD_0394	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L03CD
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L03CD
	cmp dx, word ptr _g_4342
	jl L03CD
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L03CD
	cmp dx, word ptr _g_4340
	jl L03CD
	call far ptr _f_1B73_0196
L03CD:
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L03DB
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L03DB:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L03E9
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L03E9:
	call far ptr _o00_31AD_142B
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 18h
	out dx, al
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov es, word ptr _g_3DB0
	mov cx, word ptr [bp+0Ch]
	mov ax, word ptr [bp+8]
	sub cx, ax
	jne L0413
	jmp near ptr L04DE
L0413:
	mov word ptr [bp+8], cx
	mov bl, byte ptr _g_3DB6
	xor bh, bh
	mul bx
	mov di, ax
	mov cl, 3
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 7
	shr ax, cl
	mov bh, al
	add di, ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	mov dl, al
	and dl, 7
	shr ax, cl
	mov dh, al
	sub dh, bh
	mov bh, dh
	jne L0450
	mov ah, byte ptr [bx+_g_3DC1]
	mov bl, dl
	and ah, byte ptr [bx+_g_3DCA]
	jmp L04C8
L0450:
	mov si, di
	mov al, bl
	mov bl, dl
	cbw
	and al, al
	je L047E
	mov si, ax
	mov ah, byte ptr [si+_g_3DC1]
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov si, di
	mov cx, word ptr [bp+8]
L0470:
	inc byte ptr es:[di]
	add di, word ptr _g_3DB6
	loop L0470
	inc si
	mov di, si
	dec bh
L047E:
	cmp bl, 7
	jne L0487
	inc bh
	jmp short L048B
L0487:
	and bh, bh
	je L04B7
L048B:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov dx, word ptr [bp+8]
	mov al, byte ptr _g_3DB6
	sub al, bh
	xor ah, ah
	xor ch, ch
	push si
	push ds
	push es
	pop ds
L04A5:
	mov cl, bh
	mov si, di
	rep movsb
	add di, ax
	dec dx
	jne L04A5
	pop ds
	pop si
	cmp bl, 7
	je L04DE
L04B7:
	mov di, si
	mov al, bl
	cbw
	mov si, ax
	mov ah, byte ptr [si+_g_3DCA]
	mov bl, bh
	xor bh, bh
	add di, bx
L04C8:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov cx, word ptr [bp+8]
L04D5:
	inc byte ptr es:[di]
	add di, word ptr _g_3DB6
	loop L04D5
L04DE:
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L051A
	test byte ptr _g_4365, 0FFh
	je L050E
	test byte ptr _g_4331, 0FFh
	je L051A
	call far ptr _f_1B73_04BB
	jmp short L051A
L050E:
	test byte ptr _g_4366, 0FFh
	jne L051A
	call far ptr _f_1B73_00D9
L051A:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o00_31AD_0394	endp

_o00_31AD_0522	proc	far
	push bp
	mov bp, sp
	call near ptr L0537
	xor dx, dx
	shl ax, 1
	rol dx, 1
	shl ax, 1
	rol dx, 1
	add ax, 4
	pop bp
	retf
L0537:
	mov cl, 3
	mov ax, word ptr [bp+0Ah]
	dec ax
	sar ax, cl
	mov bx, word ptr [bp+6]
	sar bx, cl
	sub ax, bx
	inc ax
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	mul bx
	retn
_o00_31AD_0522	endp

_o00_31AD_0550	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L058A
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L058A
	cmp dx, word ptr _g_4342
	jl L058A
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L058A
	cmp dx, word ptr _g_4340
	jl L058A
	call far ptr _f_1B73_0196
L058A:
	les di, dword ptr [bp+0Eh]
	mov bx, word ptr _g_3DB6
	mov ax, word ptr [bp+8]
	mul bx
	mov si, ax
	mov dx, bx
	mov cl, 3
	mov ax, word ptr [bp+6]
	sar ax, cl
	add si, ax
	mov bx, ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	sar ax, cl
	sub ax, bx
	inc ax
	push ax
	shl ax, cl
	stosw
	pop ax
	mov dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	mov word ptr es:[di], dx
	add di, 2
	mov ds, word ptr _g_3DB0
	xor ch, ch
	mov bl, al
L05C7:
	mov ah, 0
	push dx
L05CA:
	push si
	mov cl, bl
	mov al, 4
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	test si, 1
	je L05DF
	movsb
	dec cx
L05DF:
	shr cx, 1
	rep movsw
	adc cx, 0
	rep movsb
	pop si
	inc ah
	cmp ah, 4
	jne L05CA
	add si, word ptr ss:_g_3DB6
	pop dx
	dec dx
	jne L05C7
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0622
	test byte ptr _g_4365, 0FFh
	je L0616
	test byte ptr _g_4331, 0FFh
	je L0622
	call far ptr _f_1B73_04BB
	jmp short L0622
L0616:
	test byte ptr _g_4366, 0FFh
	jne L0622
	call far ptr _f_1B73_00D9
L0622:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o00_31AD_0550	endp

_o00_31AD_062A	proc	far
	mov al, 10h
	jmp short L0638
_o00_31AD_062A	endp

_o00_31AD_062E	proc	far
	mov al, 18h
	jmp short L0638
_o00_31AD_062E	endp

_o00_31AD_0632	proc	far
	mov al, 8
	jmp short L0638
_o00_31AD_0632	endp

_o00_31AD_0636	proc	far
	xor al, al
L0638:
	mov byte ptr _g_3DD2, al
	retf
_o00_31AD_0636	endp

_o00_31AD_063C	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	mov byte ptr _g_3DD2, al
	pop bp
	retf
_o00_31AD_063C	endp

_o00_31AD_0647	proc	far
	push bp
	mov bp, sp
	sub sp, 82h
	push si
	push di
	mov ax, word ptr [bp+6]
	test ax, 7
	jne L0662
	mov ax, word ptr _g_5AAE
	and ax, ax
	jne L066F
	jmp near ptr L0708
L0662:
	push ds
	jmp L06B1
L0666:
	add si, 8
	jmp short L0684
L066B:
	pop ds
	jmp near ptr L0833
L066F:
	push ds
	lds si, dword ptr _g_5AAC
	mov ax, word ptr [bp+8]
	mov bx, word ptr [bp+6]
	mov cx, ax
	add cx, 0Fh
	mov dx, bx
	add dx, 0Fh
L0684:
	cmp word ptr [si+2], 8000h
	je L066B
	cmp word ptr [si+6], ax
	jl L0666
	cmp word ptr [si+4], bx
	jl L0666
	cmp word ptr [si], dx
	jg L0666
	cmp word ptr [si+2], cx
	jg L0666
	cmp word ptr [si+6], cx
	jl L06B1
	cmp word ptr [si+2], ax
	jg L06B1
	cmp word ptr [si], bx
	jg L06B1
	cmp word ptr [si+4], dx
	jg L0707
L06B1:
	inc byte ptr ss:_g_3DD4
	mov si, word ptr [bp+0Ah]
	lea di, [bp-80h]
	mov ax, ss
	mov es, ax
	mov ds, word ptr ss:_g_3DB0
	mov dx, 10h
L06C8:
	mov ah, 0
	push dx
L06CB:
	mov bx, si
	mov al, 4
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	movsw
	mov si, bx
	inc ah
	cmp ah, 4
	jne L06CB
	inc si
	inc si
	pop dx
	dec dx
	jne L06C8
	pop ds
	dec byte ptr _g_3DD4
	mov ax, 10h
	push ax
	push ax
	push ss
	lea ax, [bp-80h]
	push ax
	push word ptr [bp+8]
	push word ptr [bp+6]
	push cs
	call near ptr _o00_31AD_0CF9
	add sp, 0Ch
	push ds
	jmp L066B
L0707:
	pop ds
L0708:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0740
	mov ax, word ptr [bp+8]
	mov dx, ax
	add dx, 0Fh
	cmp ax, word ptr _g_4344
	jg L0740
	cmp dx, word ptr _g_4342
	jl L0740
	mov ax, word ptr [bp+6]
	mov dx, ax
	add dx, 0Fh
	cmp ax, word ptr _g_4346
	jg L0740
	cmp dx, word ptr _g_4340
	jl L0740
	call far ptr _f_1B73_0196
L0740:
	push ds
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 5
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 1
	out dx, al
	mov di, word ptr [bp+8]
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add di, ax
	mov ax, word ptr _g_3DB0
	mov es, ax
	mov ds, ax
	mov si, word ptr [bp+0Ah]
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	add di, word ptr ss:_g_3DB6
	dec di
	dec di
	movsb
	movsb
	pop ds
	mov al, 5
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L082F
	test byte ptr _g_4365, 0FFh
	je L0823
	test byte ptr _g_4331, 0FFh
	je L082F
	call far ptr _f_1B73_04BB
	jmp short L082F
L0823:
	test byte ptr _g_4366, 0FFh
	jne L082F
	call far ptr _f_1B73_00D9
L082F:
	dec byte ptr _g_3DD4
L0833:
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_31AD_0647	endp

_o00_31AD_0839	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+0Eh]
	lds si, dword ptr [bp+0Ah]
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
	pop di
	pop si
	pop bp
	retf
_o00_31AD_0839	endp

_o00_31AD_0CF9	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_0D06
	call far ptr _f_1D8E_07F6
	retf
_o00_31AD_0CF9	endp

_o00_31AD_0D06	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0D4F
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L0D4F
	cmp dx, word ptr _g_4342
	jl L0D4F
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L0D4F
	cmp dx, word ptr _g_4340
	jl L0D4F
	call far ptr _f_1B73_0196
L0D4F:
	mov di, word ptr [bp+8]
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov dx, word ptr _g_3DB6
	mov cl, 3
	mov ax, word ptr [bp+6]
	test ax, 7
	je L0D69
	jmp near ptr L0F25
L0D69:
	cmp word ptr [bp+0Eh], 10h
	jne L0D8A
	cmp word ptr [bp+10h], 10h
	jne L0D8A
	cmp byte ptr _g_3DD2, 0
	jne L0D8A
	cmp word ptr _fd_55B3_3DE6, 0
	jne L0D8A
	cmp word ptr _fd_55B3_3DE8, 0
	je L0D8D
L0D8A:
	jmp near ptr L0EA7
L0D8D:
	sar ax, 1
	sar ax, 1
	sar ax, 1
	add di, ax
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov es, word ptr _g_3DB0
	lds si, dword ptr [bp+0Ah]
	mov ah, 1
L0DA8:
	push di
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	movsw
	add si, 6
	add di, word ptr ss:_g_3DB6
	sub di, 2
	sub si, 7Eh
	pop di
	shl ah, 1
	cmp al, 10h
	je L0E80
	jmp L0DA8
L0E80:
	jmp L0EDE
L0E83:
	mov ah, 1
L0E85:
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	call near ptr _o00_31AD_1002
	pop di
	shl ah, 1
	cmp ah, 10h
	jne L0E85
	add di, word ptr ss:_g_3DB6
	dec word ptr [bp-2]
	jne L0E83
	jmp short L0EDE
L0EA7:
	sar ax, cl
	add di, ax
	call near ptr _o00_31AD_0F56
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
	cmp byte ptr ss:_g_3DD2, 0
	jne L0E83
L0EBC:
	mov ah, 1
L0EBE:
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	call near ptr _o00_31AD_1065
	pop di
	shl ah, 1
	cmp ah, 10h
	jne L0EBE
	add di, word ptr ss:_g_3DB6
	dec word ptr [bp-2]
	jne L0EBC
L0EDE:
	pop ds
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L0F1B
	test byte ptr _g_4365, 0FFh
	je L0F0F
	test byte ptr _g_4331, 0FFh
	je L0F1B
	call far ptr _f_1B73_04BB
	jmp short L0F1B
L0F0F:
	test byte ptr _g_4366, 0FFh
	jne L0F1B
	call far ptr _f_1B73_00D9
L0F1B:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0F25:
	sar ax, cl
	add di, ax
	call near ptr _o00_31AD_0F56
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L0F32:
	mov ah, 1
L0F34:
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	call near ptr _o00_31AD_110C
	pop di
	shl ah, 1
	cmp ah, 10h
	jne L0F34
	add di, word ptr ss:_g_3DB6
	dec word ptr [bp-2]
	jne L0F32
	jmp L0EDE
_o00_31AD_0D06	endp

_o00_31AD_0F56	proc	far
	mov ch, byte ptr ss:_g_3DD2
	and ch, ch
	je L0F69
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ch
	out dx, al
L0F69:
	mov cl, 3
	mov ax, word ptr _fd_55B3_3DE6
	mov bx, word ptr [bp+6]
	mov bh, al
	and bl, 7
	and bh, 7
	add bh, bl
	sar bh, cl
	mov byte ptr _g_3DEF, bh
	sar ax, cl
	push ax
	mov byte ptr _g_3DEA, al
	mov bx, word ptr [bp+6]
	and bx, 7
	mov dx, bx
	mov byte ptr _g_3DEE, bl
	add bx, word ptr _fd_55B3_3DE6
	and bx, 7
	mov ch, byte ptr [bx+_g_3DC1]
	mov byte ptr _g_3DEC, ch
	mov ax, word ptr [bp+0Eh]
	mov bx, ax
	add bx, 7
	sar bx, cl
	mov byte ptr _g_3DF2, bl
	add ax, dx
	mov bx, ax
	add ax, 7
	shr ax, cl
	mov dl, al
	sub bx, word ptr _fd_55B3_3DE8
	mov ax, bx
	dec bx
	and bx, 7
	mov ch, byte ptr [bx+_g_3DCA]
	mov byte ptr _g_3DED, ch
	add ax, 7
	shr ax, cl
	sub al, byte ptr _g_3DEA
	mov bl, al
	sub dl, al
	mov byte ptr _g_3DEA, dl
	sub bl, byte ptr ss:_g_3DEF
	cmp bl, 1
	jne L0FF0
	mov bh, byte ptr _g_3DEC
	and bh, byte ptr _g_3DED
L0FF0:
	mov es, word ptr _g_3DB0
	lds si, dword ptr [bp+0Ah]
	pop ax
	add di, ax
	add di, word ptr ss:_g_3DEF
	add si, ax
	retn
_o00_31AD_0F56	endp

_o00_31AD_1002	proc	far
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L104E
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L102A
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	lodsb
L1025:
	and al, al
	stosb
	dec cl
L102A:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	xor ch, ch
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L1047
L1040:
	mov al, byte ptr es:[di]
	lodsb
L1044:
	and al, al
	stosb
L1047:
	loop L1040
	test bh, 1
	jne L105F
L104E:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	lodsb
L105C:
	and al, al
	stosb
L105F:
	add si, word ptr ss:_g_3DEA
	retn
_o00_31AD_1002	endp

_o00_31AD_1065	proc	far
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L104E
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L108A
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	movsb
	dec cl
L108A:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	xor ch, ch
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L10B3
	test di, 1
	je L10AA
	movsb
	dec cx
	je L10B5
L10AA:
	shr cx, 1
	rep movsw
	jae L10B5
	movsb
	jmp short L10B5
L10B3:
	loop L10AA
L10B5:
	test bh, 1
	jne L10C8
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	movsb
L10C8:
	add si, word ptr ss:_g_3DEA
	retn
L10CE:
	mov ax, word ptr cs:L1108
	mov word ptr cs:L1025, ax
	mov word ptr cs:L1044, ax
	mov word ptr cs:L105C, ax
	mov word ptr cs:L1165, ax
	mov word ptr cs:L1185, ax
	mov word ptr cs:L11A0, ax
	retn
L10EB:
	mov ax, word ptr cs:L110A
	mov word ptr cs:L1025, ax
	mov word ptr cs:L1044, ax
	mov word ptr cs:L105C, ax
	mov word ptr cs:L1165, ax
	mov word ptr cs:L1185, ax
	mov word ptr cs:L11A0, ax
	retn
L1108:
	and al, al
L110A:
	not al
_o00_31AD_1065	endp

_o00_31AD_110C	proc	far
	push bp
	mov bp, sp
	sub sp, 52h
	push bx
	push ax
	mov cl, byte ptr ss:_g_3DEE
	mov ch, byte ptr ss:_g_3DF2
	xor dh, dh
	lea bx, [bp-52h]
L1123:
	lodsb
	mov ah, al
	xor al, al
	shr ax, cl
	or ah, dh
	mov byte ptr ss:[bx], ah
	inc bx
	mov dh, al
	dec ch
	jne L1123
	mov byte ptr ss:[bx], dh
	pop ax
	pop bx
	push si
	lea si, [bp-52h]
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L118F
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L116A
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	mov al, byte ptr ss:[si]
	inc si
L1165:
	and al, al
	stosb
	dec cl
L116A:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L1188
L117E:
	mov al, byte ptr es:[di]
	mov al, byte ptr ss:[si]
	inc si
L1185:
	and al, al
	stosb
L1188:
	loop L117E
	test bh, 1
	jne L11A3
L118F:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	mov al, byte ptr ss:[si]
	inc si
L11A0:
	and al, al
	stosb
L11A3:
	pop si
	mov sp, bp
	pop bp
	retn
L11A8:
	cmp bl, 1
	je L11E7
	mov cl, bl
	mov ah, byte ptr ss:_g_3DEC
	and ah, ah
	js L11C8
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov al, byte ptr es:[di]
	stosb
	dec cl
L11C8:
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	jne L11D4
	dec cl
L11D4:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	xor ch, ch
	rep stosb
	test bh, 1
	jne L11F5
L11E7:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, bh
	out dx, al
	mov al, byte ptr es:[di]
	stosb
L11F5:
	add si, word ptr ss:_g_3DEA
	retn
_o00_31AD_110C	endp

_o00_31AD_11FB	proc	far
	push bp
	mov bp, sp
	call near ptr L0537
	add ax, 4
	pop bp
	retf
_o00_31AD_11FB	endp

_o00_31AD_1206	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_1213
	call far ptr _f_1D8E_070E
	retf
_o00_31AD_1206	endp

_o00_31AD_1213	proc	far
	push bp
	mov bp, sp
	sub sp, 0Ah
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L125C
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L125C
	cmp dx, word ptr _g_4342
	jl L125C
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L125C
	cmp dx, word ptr _g_4340
	jl L125C
	call far ptr _f_1B73_0196
L125C:
	mov al, byte ptr _g_3DE0
	mov byte ptr [bp-2], al
	mov ah, byte ptr _g_3DE2
	mov byte ptr [bp-4], ah
	mov dx, word ptr _g_3DB6
	mov di, word ptr [bp+8]
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov cl, 3
	mov ax, word ptr [bp+6]
	sar ax, cl
	add di, ax
	mov ax, word ptr _g_3DB6
	mov word ptr [bp-8], ax
	call near ptr _o00_31AD_0F56
	sub byte ptr [bp-8], bl
	test word ptr [bp+6], 7
	je L1295
	jmp near ptr L1394
L1295:
	xor ch, ch
	mov ah, byte ptr [bp-4]
	not ah
	and ah, byte ptr [bp-2]
	and ah, 0Fh
	je L12C3
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	push si
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-6], dx
L12B6:
	call near ptr _o00_31AD_1002
	add di, word ptr [bp-8]
	dec word ptr [bp-6]
	jne L12B6
	pop si
	pop di
L12C3:
	mov ah, byte ptr [bp-2]
	not ah
	and ah, byte ptr [bp-4]
	and ah, 0Fh
	je L12F3
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-6], dx
	call near ptr L10EB
L12E4:
	call near ptr _o00_31AD_1002
	add di, word ptr [bp-8]
	dec word ptr [bp-6]
	jne L12E4
	call near ptr L10CE
	pop di
L12F3:
	mov cl, byte ptr [bp-4]
	or cl, byte ptr [bp-2]
	not cl
	and cl, 0Fh
	mov ah, byte ptr [bp-4]
	and ah, byte ptr [bp-2]
	and ah, 0Fh
	or cl, ah
	je L133A
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, cl
	out dx, al
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, cl
	out dx, al
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-6], dx
L132F:
	call near ptr L11A8
	add di, word ptr [bp-8]
	dec word ptr [bp-6]
	jne L132F
L133A:
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov ch, byte ptr ss:_g_3DD2
	and ch, ch
	je L1357
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
L1357:
	pop ds
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L138A
	test byte ptr _g_4365, 0FFh
	je L137E
	test byte ptr _g_4331, 0FFh
	je L138A
	call far ptr _f_1B73_04BB
	jmp short L138A
L137E:
	test byte ptr _g_4366, 0FFh
	jne L138A
	call far ptr _f_1B73_00D9
L138A:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L1394:
	xor ch, ch
	mov ah, byte ptr [bp-4]
	not ah
	and ah, byte ptr [bp-2]
	and ah, 0Fh
	je L13CD
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	push si
	mov word ptr [bp-0Ah], di
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-6], dx
L13B8:
	mov di, word ptr [bp-0Ah]
	call near ptr _o00_31AD_110C
	mov cx, word ptr ss:_g_3DB6
	add word ptr [bp-0Ah], cx
	dec word ptr [bp-6]
	jne L13B8
	pop si
	pop di
L13CD:
	mov ah, byte ptr [bp-2]
	not ah
	and ah, byte ptr [bp-4]
	and ah, 0Fh
	je L1408
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	mov word ptr [bp-0Ah], di
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-6], dx
	call near ptr L10EB
L13F1:
	mov di, word ptr [bp-0Ah]
	call near ptr _o00_31AD_110C
	mov cx, word ptr ss:_g_3DB6
	add word ptr [bp-0Ah], cx
	dec word ptr [bp-6]
	jne L13F1
	call near ptr L10CE
	pop di
L1408:
	jmp L12F3
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ch
	out dx, al
	push di
	push si
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-6], dx
L141D:
	call near ptr _o00_31AD_1002
	add di, word ptr [bp-8]
	dec word ptr [bp-6]
	jne L141D
	pop si
	pop di
	retn
_o00_31AD_1213	endp

_o00_31AD_142B	proc	far
	mov al, 5
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	retf
_o00_31AD_142B	endp

_o00_31AD_145E	proc	far
	les si, dword ptr _g_20FC
	call far ptr _f_1B4E_0165
	retf
_o00_31AD_145E	endp

_o00_31AD_1468	proc	far
	xor ax, ax
	mov es, ax
	mov bl, byte ptr es:[487h]
	and bl, 60h
	mov cl, 4
	shr bl, cl
	xor bh, bh
	les ax, dword ptr [bx+_g_2078]
	mov dx, es
	retf
_o00_31AD_1468	endp

_o00_31AD_1481	proc	far
	mov ax, 3
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	retf
_o00_31AD_1481	endp

_o00_31AD_148C	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_1499
	call far ptr _f_1D8E_0435
	retf
_o00_31AD_148C	endp

_o00_31AD_1499	proc	far
	push bp
	mov bp, sp
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L14DA
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, dx
	jle L14B2
	xchg dx, ax
L14B2:
	cmp ax, word ptr _g_4344
	jg L14DA
	cmp dx, word ptr _g_4342
	jl L14DA
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, dx
	jle L14C9
	xchg dx, ax
L14C9:
	cmp ax, word ptr _g_4346
	jg L14DA
	cmp dx, word ptr _g_4340
	jl L14DA
	call far ptr _f_1B73_0196
L14DA:
	mov cx, word ptr [bp+8]
	cmp cx, word ptr [bp+0Ch]
	jne L14E3
	nop
L14E3:
	sub sp, 6
	push di
	push si
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov ah, byte ptr [bp+0Eh]
	and ah, 0Fh
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov ah, byte ptr _g_3DD2
	and ah, ah
	je L151E
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
L151E:
	mov dx, word ptr [bp+0Ch]
	mov ax, word ptr [bp+0Ah]
	mov di, ax
	mov bx, word ptr [bp+6]
	mov ax, di
	sub ax, bx
	jge L1539
	mov bx, di
	mov di, dx
	mov dx, cx
	mov cx, di
	neg ax
L1539:
	mov word ptr [bp+8], ax
	mov word ptr [bp+6], bx
	mov word ptr [bp+0Ah], cx
	sub dx, cx
	mov ax, word ptr _g_3DB6
	mov word ptr [bp-2], ax
	jge L1551
	neg word ptr [bp-2]
	neg dx
L1551:
	mov word ptr [bp+0Ch], dx
	mov dx, 3CEh
	mov al, 8
	out dx, al
	mov ax, word ptr _g_3DB0
	mov es, ax
	mov ax, word ptr [bp+6]
	mov dx, ax
	and dx, 7
	mov cl, 3
	sar ax, cl
	mov si, ax
	lea bx, _g_2100
	add bx, dx
	mov al, byte ptr [bx]
	mov bx, word ptr [bp+0Ah]
	add bx, bx
	mov bx, word ptr [bx+_g_3DFC]
	mov cx, 0
	mov dx, word ptr [bp+8]
	cmp dx, word ptr [bp+0Ch]
	jl L158F
	call near ptr L15D8
	jmp L1592
L158F:
	call near ptr L160A
L1592:
	pop si
	pop di
	mov sp, bp
	pop bp
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov al, 3
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L15D3
	test byte ptr _g_4365, 0FFh
	je L15C7
	test byte ptr _g_4331, 0FFh
	je L15D3
	call far ptr _f_1B73_04BB
	jmp short L15D3
L15C7:
	test byte ptr _g_4366, 0FFh
	jne L15D3
	call far ptr _f_1B73_00D9
L15D3:
	dec byte ptr _g_3DD4
	retf
L15D8:
	mov di, word ptr [bp+0Ch]
	mov dx, word ptr [bp+8]
	mov word ptr [bp-4], dx
	shr dx, 1
	mov word ptr [bp-6], dx
	mov dx, 3CFh
L15E9:
	cmp si, 0
	jl L15F2
	out dx, al
	inc byte ptr es:[bx+si]
L15F2:
	ror al, 1
	jae L15F7
	inc si
L15F7:
	add cx, di
	cmp cx, word ptr [bp-6]
	jle L1604
	sub cx, word ptr [bp+8]
	add bx, word ptr [bp-2]
L1604:
	dec word ptr [bp-4]
	jge L15E9
	retn
L160A:
	mov di, word ptr [bp+8]
	or di, di
	je L1641
	mov dx, word ptr [bp+0Ch]
	mov word ptr [bp-4], dx
	shr dx, 1
	mov word ptr [bp-6], dx
	mov dx, 3CFh
	out dx, al
L1620:
	cmp si, 0
	jl L1628
	inc byte ptr es:[bx+si]
L1628:
	add bx, word ptr [bp-2]
	add cx, di
	cmp cx, word ptr [bp-6]
	jle L163B
	sub cx, word ptr [bp+0Ch]
	ror al, 1
	out dx, al
	jae L163B
	inc si
L163B:
	dec word ptr [bp-4]
	jge L1620
L1640:
	retn
L1641:
	add bx, si
	cmp si, 0
	jl L1640
	mov cx, word ptr [bp+0Ch]
	mov dx, 3CFh
	out dx, al
L164F:
	inc byte ptr es:[bx]
	add bx, word ptr [bp-2]
	dec cx
	jge L164F
	retn
_o00_31AD_1499	endp

_o00_31AD_1659	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	mov byte ptr _g_3DE0, al
	mov ax, word ptr [bp+8]
	mov byte ptr _g_3DE2, al
	pop bp
	retf
_o00_31AD_1659	endp

_o00_31AD_166A	proc	far
	push bp
	mov ax, 1130h
	mov bh, 3
	int 10h
	mov word ptr _g_3DD6, bp
	mov word ptr _g_3DD8, es
	mov byte ptr _g_3DDC, 8
	mov byte ptr _g_3DDE, 8
	mov word ptr _g_3DDA, 8
	pop bp
	retf
_o00_31AD_166A	endp

_o00_31AD_168C	proc	far
	push bp
	mov ax, 1130h
	mov bh, 2
	int 10h
	mov word ptr _g_3DD6, bp
	mov word ptr _g_3DD8, es
	mov byte ptr _g_3DDC, 0Eh
	mov word ptr _g_3DDA, 0Eh
	pop bp
	retf
_o00_31AD_168C	endp

_o00_31AD_16A9	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je L16C1
	mov ax, S00B_TEXT
	push ax
	mov ax, 16C1h
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
L16C1:
	push bp
	mov bp, sp
	push si
	push di
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L16D4
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L16D4:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L16E2
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L16E2:
	jmp short L1702
_o00_31AD_16A9	endp

_o00_31AD_16E4	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o00_31AD_16FC
	mov ax, S00B_TEXT
	push ax
	mov ax, 16FCh
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o00_31AD_16E4	endp

_o00_31AD_16FC	proc	far
	push bp
	mov bp, sp
	push si
	push di
	nop
L1702:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L1736
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L1736
	cmp dx, word ptr _g_4342
	jl L1736
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L1736
	cmp dx, word ptr _g_4340
	jl L1736
	call far ptr _f_1B73_0196
L1736:
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov ah, byte ptr [bp+0Eh]
	and ah, 0Fh
	mov al, 0
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov es, word ptr _g_3DB0
	mov cx, word ptr [bp+0Ch]
	mov ax, word ptr [bp+8]
	sub cx, ax
	jle L1798
	mov word ptr [bp+8], cx
	mov bl, byte ptr _g_3DB6
	xor bh, bh
	mul bx
	mov di, ax
	mov cl, 3
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 7
	shr ax, cl
	mov bh, al
	add di, ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	mov dl, al
	and dl, 7
	shr ax, cl
	mov dh, al
	sub dh, bh
	mov bh, dh
	jge L179B
L1798:
	jmp near ptr L1830
L179B:
	jne L17AA
	mov ah, byte ptr [bx+_g_3DC1]
	mov bl, dl
	and ah, byte ptr [bx+_g_3DCA]
	jmp L181A
L17AA:
	mov si, di
	mov al, bl
	mov bl, dl
	cbw
	and al, al
	je L17D8
	mov si, ax
	mov ah, byte ptr [si+_g_3DC1]
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov si, di
	mov cx, word ptr [bp+8]
L17CA:
	inc byte ptr es:[di]
	add di, word ptr _g_3DB6
	loop L17CA
	inc si
	mov di, si
	dec bh
L17D8:
	cmp bl, 7
	jne L17E1
	inc bh
	jmp short L17E5
L17E1:
	and bh, bh
	je L1809
L17E5:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov dx, word ptr [bp+8]
	mov al, byte ptr _g_3DB6
	sub al, bh
	xor ah, ah
	xor ch, ch
L17FB:
	mov cl, bh
	rep stosb
	add di, ax
	dec dx
	jne L17FB
	cmp bl, 7
	je L1830
L1809:
	mov di, si
	mov al, bl
	cbw
	mov si, ax
	mov ah, byte ptr [si+_g_3DCA]
	mov bl, bh
	xor bh, bh
	add di, bx
L181A:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov cx, word ptr [bp+8]
L1827:
	inc byte ptr es:[di]
	add di, word ptr _g_3DB6
	loop L1827
L1830:
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L1862
	test byte ptr _g_4365, 0FFh
	je L1856
	test byte ptr _g_4331, 0FFh
	je L1862
	call far ptr _f_1B73_04BB
	jmp short L1862
L1856:
	test byte ptr _g_4366, 0FFh
	jne L1862
	call far ptr _f_1B73_00D9
L1862:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o00_31AD_16FC	endp

_o00_31AD_186A	proc	far
	push bp
	mov bp, sp
	push di
	push si
	push ds
	inc byte ptr _g_3DD4
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov cx, word ptr [bp+0Ch]
	mov ah, 1
	shl ah, cl
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov di, word ptr [bp+0Ah]
	mov es, word ptr _g_3DB0
	lds si, dword ptr [bp+6]
	mov cx, word ptr [bp+0Eh]
	jcxz L18B1
	test di, 1
	je L18A8
	movsb
	dec cx
	jcxz L18B1
L18A8:
	shr cx, 1
	jcxz L18B1
	rep movsw
	jae L18B1
	movsb
L18B1:
	pop ds
	dec byte ptr _g_3DD4
	pop si
	pop di
	pop bp
	retf
_o00_31AD_186A	endp

_o00_31AD_18BA	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	call far ptr _o00_31AD_142B
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov es, word ptr _g_3DB0
	mov di, word ptr [bp+0Ah]
	lds si, dword ptr [bp+6]
	mov cx, word ptr [bp+0Ch]
L18E0:
	mov ah, 1
L18E2:
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	push di
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	add si, 6
	movsw
	pop di
	sub si, 78h
	shl ah, 1
	cmp ah, 10h
	jne L18E2
	add si, 78h
	add di, 20h
	loop L18E0
	mov al, 5
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	pop ds
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o00_31AD_18BA	endp

_o00_31AD_1950	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L198D
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L198D
	cmp dx, word ptr _g_4342
	jl L198D
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L198D
	cmp dx, word ptr _g_4340
	jl L198D
	call far ptr _f_1B73_0196
	jmp L19C0
L198D:
	mov ax, word ptr [bp+0Eh]
	mov dx, ax
	add dx, word ptr [bp+0Ah]
	sub dx, word ptr [bp+6]
	cmp ax, word ptr _g_4346
	jg L19C0
	cmp dx, word ptr _g_4340
	jl L19C0
	mov ax, word ptr [bp+10h]
	mov dx, ax
	add dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	cmp ax, word ptr _g_4344
	jg L19C0
	cmp dx, word ptr _g_4342
	jl L19C0
	call far ptr _f_1B73_0196
L19C0:
	mov al, 8
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0FFh
	out dx, al
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	mov al, 5
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 1
	out dx, al
	mov cx, word ptr [bp+10h]
	mov dx, word ptr _g_3DB6
	mov ax, word ptr [bp+8]
	cmp ax, cx
	jge L19F6
	mov ax, word ptr [bp+0Ch]
	add cx, ax
	sub cx, word ptr [bp+8]
	neg dx
L19F6:
	mov si, ax
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov di, cx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	shr ax, 1
	shr ax, 1
	shr ax, 1
	add si, ax
	mov bx, word ptr [bp+0Eh]
	shr bx, 1
	shr bx, 1
	shr bx, 1
	add di, bx
	mov bh, al
	mov ax, word ptr [bp+0Ah]
	shr ax, 1
	shr ax, 1
	shr ax, 1
	sub al, bh
	cmp bh, bl
	jge L1A38
	std
	add dx, ax
	add di, ax
	dec di
	add si, ax
	dec si
	jmp short L1A3A
L1A38:
	sub dx, ax
L1A3A:
	mov bx, word ptr _g_3DB0
	mov ds, bx
	mov es, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
L1A48:
	mov cx, ax
	rep movsb
	add di, dx
	add si, dx
	dec bx
	jne L1A48
	cld
	pop ds
	mov al, 5
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	test byte ptr _g_4333, 0FFh
	jne L1A87
	test byte ptr _g_4365, 0FFh
	je L1A7B
	test byte ptr _g_4331, 0FFh
	je L1A87
	call far ptr _f_1B73_04BB
	jmp short L1A87
L1A7B:
	test byte ptr _g_4366, 0FFh
	jne L1A87
	call far ptr _f_1B73_00D9
L1A87:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o00_31AD_1950	endp

_o00_31AD_1A8F	proc	far
	push bp
	mov bp, sp
	push di
	push si
	push ds
	inc byte ptr _g_3DD4
	mov ah, byte ptr [bp+6]
	mov al, 4
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, ah
	out dx, al
	mov si, word ptr [bp+8]
	mov ds, word ptr _g_3DB0
	mov cx, 40h
	mov ax, ss
	mov es, ax
	lea di, _g_3D20
	rep movsw
	dec byte ptr ss:_g_3DD4
	pop ds
	pop si
	pop di
	pop bp
	retf
_o00_31AD_1A8F	endp

_o00_31AD_1AC4	proc	far
	mov ax, word ptr _g_3DAA
	and ax, ax
	je L1AE6
	mov bx, word ptr _g_3DA8
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, ax
	mov byte ptr _g_3DDC, 6
	mov byte ptr _g_3DDE, 4
	mov word ptr _g_3DDA, 6
L1AE6:
	retf
_o00_31AD_1AC4	endp

_o00_31AD_1AE7	proc	far
	push bp
	mov bp, sp
	sub sp, 8
	push si
	push di
	call far ptr _o00_31AD_145E
	lea bx, _g_9130
	mov ax, 166Ah
	mov word ptr [bx], ax
	lea bx, _g_912C
	mov ax, 1AC4h
	mov word ptr [bx], ax
	mov word ptr _g_3DB6, 28h
	mov word ptr _g_3DB2, 140h
	mov cx, 0C8h
	mov word ptr _g_3DB4, cx
	xor ax, ax
	mov di, 3DFCh
	mov es, word ptr _g_3DAE
L1B22:
	stosw
	add ax, 28h
	loop L1B22
	mov ax, 0Dh
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	mov ax, ds
	mov es, ax
	lea di, _g_41C0
	lea si, _g_2108
	mov cx, 8
	rep movsw
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o00_31AD_1AE7	endp

_o00_31AD_1B49	proc	far
	push bp
	mov bp, sp
	push word ptr [bp+12h]
	les bx, dword ptr [bp+0Eh]
	push es
	push bx
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	call far ptr _o00_31AD_1B7D
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
_o00_31AD_1B49	endp

_o00_31AD_1B7D	proc	far
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
	jne L1BA7
	jmp near ptr L205F
L1BA7:
	cmp byte ptr [bp+0Eh], 3
	jne L1BB0
	jmp near ptr L2589
L1BB0:
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
L2057:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
L205F:
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
	pop bp
	pop ds
	jmp L2057
L2589:
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	mov word ptr [bp], bx
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
	xor bx, cx
	mov word ptr [bp], bx
	inc bp
	inc bp
	pop bp
	pop ds
	jmp L2057
_o00_31AD_1B7D	endp

S00B_TEXT	ends
	end
