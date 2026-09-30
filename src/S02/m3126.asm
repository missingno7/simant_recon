; Display driver S02 (dispatch table DGROUP:21A6, 25 entries): screen, blit and raster-op procs.
; Overlay section S02, code frame 3126, linear 31260-31BC9.
; Genuine assembly, reproduced byte for byte by MASM 5.10.  Evidence against compiler output:
; framed procs save "push si; push di" (MSC always saves DI first, probe ASM-2 in
; build/workers/ovlA/probe), raster operations are selected by self-modifying code
; (instruction templates such as "xor al,ah" are copied over loop instructions with
; "mov cs:[...],ax"), and short near subroutines return with retn inside far procs.
; The far pointers to the 25 entries live in the DGROUP dispatch table at 21A6 (not reconstructed here).

_DATA	segment word public 'DATA'
	extrn	_fd_55B3_3DE6:byte
	extrn	_fd_55B3_3DE8:byte
	extrn	_g_3DA4:byte
	extrn	_g_3DA8:byte
	extrn	_g_3DAE:byte
	extrn	_g_3DB0:byte
	extrn	_g_3DB2:byte
	extrn	_g_3DB4:byte
	extrn	_g_3DD2:byte
	extrn	_g_3DD4:byte
	extrn	_g_3DD6:byte
	extrn	_g_3DD8:byte
	extrn	_g_3DDA:byte
	extrn	_g_3DDC:byte
	extrn	_g_3DDE:byte
	extrn	_g_3DE0:byte
	extrn	_g_3DE1:byte
	extrn	_g_3DE2:byte
	extrn	_g_3DE3:byte
	extrn	_g_3DEA:byte
	extrn	_g_3DFC:byte
	extrn	_g_4331:byte
	extrn	_g_4333:byte
	extrn	_g_4340:byte
	extrn	_g_4342:byte
	extrn	_g_4344:byte
	extrn	_g_4346:byte
	extrn	_g_4365:byte
	extrn	_g_4366:byte
	extrn	_g_5AAE:byte
; S02 private data (DGROUP:219C-220D): blit scratch words, the dispatch table the game
; calls through, and a far pointer to that table.
_g_219C	dw	0
_g_219E	dw	0
_g_21A0	dw	0
_g_21A2	dw	0
	dw	0
DispatchS02	label	dword
	dd	_o02_3126_0040
	dd	_o02_3126_005C
	dd	_o02_3126_0079
	dd	_o02_3126_027C
	dd	_o02_3126_0185
	dd	_o02_3126_03B1
	dd	_o02_3126_03D4
	dd	_o02_3126_03D4
	dd	_o02_3126_03EF
	dd	_o02_3126_0505
	dd	_o02_3126_0512
	dd	_o02_3126_0636
	dd	_o02_3126_0643
	dd	_o02_3126_04C6
	dd	_o02_3126_0490
	dd	_o02_3126_04B4
	dd	_o02_3126_04A2
	dd	_o02_3126_073A
	dd	_o02_3126_0747
	dd	_o02_3126_0096
	dd	_o02_3126_0051
	dd	_o02_3126_084E
	dd	_o02_3126_0857
	dd	_o02_3126_04D8
	dd	_o02_3126_0860
_g_220A	dd	DGROUP:DispatchS02
_DATA	ends
DGROUP	group	_DATA

	extrn	_f_1B4E_015B:far
	extrn	_f_1B4E_0165:far
	extrn	_f_1B73_00D9:far
	extrn	_f_1B73_0196:far
	extrn	_f_1B73_04BB:far
	extrn	_f_1D8E_0384:far
	extrn	_f_1D8E_0435:far
	extrn	_f_1D8E_0AC7:far
	extrn	_f_1D8E_0BAE:far

S02A_TEXT	segment word public 'CODE'
	assume	cs:S02A_TEXT, ds:DGROUP

	public	_o02_3126_0000
	public	_o02_3126_0040
	public	_o02_3126_0051
	public	_o02_3126_005C
	public	_o02_3126_0079
	public	_o02_3126_0096
	public	_o02_3126_00AE
	public	_o02_3126_0185
	public	_o02_3126_019D
	public	_o02_3126_027C
	public	_o02_3126_03B1
	public	_o02_3126_03D4
	public	_o02_3126_03EF
	public	_o02_3126_0490
	public	_o02_3126_04A2
	public	_o02_3126_04B4
	public	_o02_3126_04C6
	public	_o02_3126_04D8
	public	_o02_3126_0505
	public	_o02_3126_0512
	public	_o02_3126_0636
	public	_o02_3126_0643
	public	_o02_3126_073A
	public	_o02_3126_0747
	public	_o02_3126_084E
	public	_o02_3126_0857
	public	_o02_3126_0860

_o02_3126_0000	proc	far
	push ds
	push es
	push si
	push di
	mov word ptr _g_3DB0, 0A000h
	mov cx, 0C8h
	mov word ptr _g_3DB4, cx
	mov word ptr _g_3DB2, 140h
	xor ax, ax
	mov di, 3DFCh
	mov es, word ptr _g_3DAE
L0020:
	stosw
	add ax, 140h
	loop L0020
	les si, dword ptr _g_220A
	call far ptr _f_1B4E_0165
	mov ax, 13h
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	xor ax, ax
	pop di
	pop si
	pop es
	pop ds
	retf
_o02_3126_0000	endp

_o02_3126_0040	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	mov word ptr _g_3DE0, ax
	mov ax, word ptr [bp+8]
	mov word ptr _g_3DE2, ax
	pop bp
	retf
_o02_3126_0040	endp

_o02_3126_0051	proc	far
	mov ax, 3
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	retf
_o02_3126_0051	endp

_o02_3126_005C	proc	far
	les bx, dword ptr _g_3DA8
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, es
	mov byte ptr _g_3DDC, 6
	mov byte ptr _g_3DDE, 4
	mov word ptr _g_3DDA, 18h
	retf
_o02_3126_005C	endp

_o02_3126_0079	proc	far
	les bx, dword ptr _g_3DA4
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, es
	mov byte ptr _g_3DDC, 8
	mov byte ptr _g_3DDE, 8
	mov word ptr _g_3DDA, 40h
	retf
_o02_3126_0079	endp

_o02_3126_0096	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o02_3126_00AE
	mov ax, S02A_TEXT
	push ax
	mov ax, 0AEh
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o02_3126_0096	endp

_o02_3126_00AE	proc	far
	push bp
	mov bp, sp
	sub sp, 6
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L00EA
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L00EA
	cmp dx, word ptr _g_4342
	jl L00EA
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L00EA
	cmp dx, word ptr _g_4340
	jl L00EA
	call far ptr _f_1B73_0196
L00EA:
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L00F8
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L00F8:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L0106
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L0106:
	mov es, word ptr _g_3DB0
	mov bx, word ptr [bp+8]
	mov si, bx
	mov cx, word ptr [bp+0Ch]
	sub cx, bx
	mov word ptr [bp+8], cx
	mov cx, word ptr [bp+6]
	mov dx, cx
	add dx, bx
	mov dh, 0FFh
	and dl, 1
	je L0129
	dec dl
	xchg dl, dh
L0129:
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov bh, al
	add di, cx
	mov ax, word ptr [bp+0Ah]
	sub ax, cx
	mov bx, word ptr [bp+8]
L013B:
	mov si, di
	mov cx, ax
L013F:
	or byte ptr es:[di], dl
	xchg dl, dh
	inc di
	loop L013F
	mov di, si
	add di, 140h
	xchg dl, dh
	dec bl
	jne L013B
	test byte ptr _g_4333, 0FFh
	jne L017B
	test byte ptr _g_4365, 0FFh
	je L016F
	test byte ptr _g_4331, 0FFh
	je L017B
	call far ptr _f_1B73_04BB
	jmp short L017B
L016F:
	test byte ptr _g_4366, 0FFh
	jne L017B
	call far ptr _f_1B73_00D9
L017B:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o02_3126_00AE	endp

_o02_3126_0185	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o02_3126_019D
	mov ax, S02A_TEXT
	push ax
	mov ax, 19Dh
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o02_3126_0185	endp

_o02_3126_019D	proc	far
	push bp
	mov bp, sp
	sub sp, 6
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L01D9
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L01D9
	cmp dx, word ptr _g_4342
	jl L01D9
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L01D9
	cmp dx, word ptr _g_4340
	jl L01D9
	call far ptr _f_1B73_0196
L01D9:
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L01E7
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L01E7:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L01F5
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L01F5:
	mov es, word ptr _g_3DB0
	mov bx, word ptr [bp+8]
	mov si, bx
	mov cx, word ptr [bp+0Ch]
	sub cx, bx
	mov word ptr [bp+8], cx
	mov cx, word ptr [bp+6]
	mov ax, cx
	add ax, bx
	mov dh, byte ptr _g_3DE1
	mov dl, byte ptr _g_3DE3
	and al, 1
	je L021B
	xchg dl, dh
L021B:
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov bh, al
	add di, cx
	mov ax, word ptr [bp+0Ah]
	sub ax, cx
	mov bx, word ptr [bp+8]
L022D:
	mov si, di
	mov cx, ax
L0231:
	mov byte ptr es:[di], dl
	xchg dl, dh
	inc di
	loop L0231
	mov di, si
	add di, 140h
	test ax, 1
	jne L0246
	xchg dl, dh
L0246:
	dec bl
	jne L022D
	test byte ptr _g_4333, 0FFh
	jne L0272
	test byte ptr _g_4365, 0FFh
	je L0266
	test byte ptr _g_4331, 0FFh
	je L0272
	call far ptr _f_1B73_04BB
	jmp short L0272
L0266:
	test byte ptr _g_4366, 0FFh
	jne L0272
	call far ptr _f_1B73_00D9
L0272:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o02_3126_019D	endp

_o02_3126_027C	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je L0294
	mov ax, S02A_TEXT
	push ax
	mov ax, 294h
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
L0294:
	push bp
	mov bp, sp
	push si
	push di
	mov bx, word ptr [bp+8]
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L02B0
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L02B0:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L02BE
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L02BE:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L02F2
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L02F2
	cmp dx, word ptr _g_4342
	jl L02F2
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L02F2
	cmp dx, word ptr _g_4340
	jl L02F2
	call far ptr _f_1B73_0196
L02F2:
	mov dx, word ptr [bp+0Eh]
	mov es, word ptr _g_3DB0
	mov bx, word ptr [bp+8]
	mov cx, word ptr [bp+0Ch]
	sub cx, bx
	je L0381
	mov dl, cl
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov ax, word ptr [bp+6]
	add di, ax
	mov bx, word ptr [bp+0Ah]
	sub bx, ax
	je L0381
	test byte ptr _g_3DD2, 0FFh
	jne L0369
	mov al, dh
	mov ah, al
	test di, 1
	jne L0341
L0328:
	mov si, di
	mov cx, bx
	shr cx, 1
	je L0334
	rep stosw
	jae L0335
L0334:
	stosb
L0335:
	mov di, si
	add di, 140h
	dec dl
	jne L0328
	jmp short L0381
L0341:
	dec cx
	jne L0351
L0344:
	mov byte ptr es:[di], al
	add di, 140h
	dec dl
	jne L0344
	jmp short L0381
L0351:
	mov si, di
	mov cx, bx
	stosb
	shr cx, 1
	rep stosw
	jae L035D
	stosb
L035D:
	mov di, si
	add di, 140h
	dec dl
	jne L0351
	jmp short L0381
L0369:
	mov si, di
	mov cx, bx
L036D:
	mov al, dh
	mov ah, byte ptr es:[di]
L0372:
	and al, al
	stosb
	loop L036D
	mov di, si
	add di, 140h
	dec dl
	jne L0369
L0381:
	test byte ptr _g_4333, 0FFh
	jne L03A9
	test byte ptr _g_4365, 0FFh
	je L039D
	test byte ptr _g_4331, 0FFh
	je L03A9
	call far ptr _f_1B73_04BB
	jmp short L03A9
L039D:
	test byte ptr _g_4366, 0FFh
	jne L03A9
	call far ptr _f_1B73_00D9
L03A9:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o02_3126_027C	endp

_o02_3126_03B1	proc	far
	push bp
	mov bp, sp
	call near ptr L071B
	mov ax, 0FFFFh
	push ax
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o02_3126_027C
	add sp, 0Ah
	call near ptr L072D
	pop bp
	retf
_o02_3126_03B1	endp

_o02_3126_03D4	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+0Ah]
	mov bx, word ptr [bp+6]
	sub ax, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	mul bx
	add ax, 4
	adc dx, 0
	pop bp
	retf
_o02_3126_03D4	endp

_o02_3126_03EF	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0429
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0429
	cmp dx, word ptr _g_4342
	jl L0429
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0429
	cmp dx, word ptr _g_4340
	jl L0429
	call far ptr _f_1B73_0196
L0429:
	les di, dword ptr [bp+0Eh]
	mov si, word ptr [bp+8]
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov bx, word ptr [bp+6]
	add si, bx
	mov ax, word ptr [bp+0Ah]
	sub ax, bx
	stosw
	mov dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	mov word ptr es:[di], dx
	add di, 2
	mov ds, word ptr _g_3DB0
L0450:
	mov bx, si
	mov cx, ax
	rep movsb
	mov si, bx
	add si, 140h
	dec dx
	jne L0450
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0488
	test byte ptr _g_4365, 0FFh
	je L047C
	test byte ptr _g_4331, 0FFh
	je L0488
	call far ptr _f_1B73_04BB
	jmp short L0488
L047C:
	test byte ptr _g_4366, 0FFh
	jne L0488
	call far ptr _f_1B73_00D9
L0488:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o02_3126_03EF	endp

_o02_3126_0490	proc	far
	mov ax, word ptr cs:L0501
	mov word ptr cs:L06D4, ax
	mov word ptr cs:L05F2, ax
	mov byte ptr _g_3DD2, 18h
	retf
_o02_3126_0490	endp

_o02_3126_04A2	proc	far
	mov ax, word ptr cs:L0736
	mov word ptr cs:L06D4, ax
	mov word ptr cs:L05F2, ax
	mov byte ptr _g_3DD2, 0
	retf
_o02_3126_04A2	endp

_o02_3126_04B4	proc	far
	mov ax, word ptr cs:L04FF
	mov word ptr cs:L06D4, ax
	mov word ptr cs:L05F2, ax
	mov byte ptr _g_3DD2, 8
	retf
_o02_3126_04B4	endp

_o02_3126_04C6	proc	far
	mov ax, word ptr cs:L0503
	mov word ptr cs:L06D4, ax
	mov word ptr cs:L05F2, ax
	mov byte ptr _g_3DD2, 10h
	retf
_o02_3126_04C6	endp

_o02_3126_04D8	proc	far
	push bp
	mov bp, sp
	push cs
	mov ax, word ptr [bp+6]
	cmp al, 10h
	jne L04E8
	call near ptr _o02_3126_04C6
	jmp short L04FD
L04E8:
	cmp al, 18h
	jne L04F1
	call near ptr _o02_3126_0490
	jmp short L04FD
L04F1:
	cmp al, 8
	jne L04FA
	call near ptr _o02_3126_04B4
	jmp short L04FD
L04FA:
	call near ptr _o02_3126_04A2
L04FD:
	pop bp
	retf
L04FF:
	and al, ah
L0501:
	xor al, ah
L0503:
	or al, ah
_o02_3126_04D8	endp

_o02_3126_0505	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o02_3126_0512
	call far ptr _f_1D8E_0AC7
	retf
_o02_3126_0505	endp

_o02_3126_0512	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L055B
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L055B
	cmp dx, word ptr _g_4342
	jl L055B
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L055B
	cmp dx, word ptr _g_4340
	jl L055B
	call far ptr _f_1B73_0196
L055B:
	mov ax, word ptr [bp+8]
	mov es, word ptr _g_3DB0
	mov di, ax
	add di, di
	mov di, word ptr [di+_g_3DFC]
	add di, word ptr [bp+6]
	mov ax, word ptr _fd_55B3_3DE6
	mov dx, word ptr _fd_55B3_3DE8
	mov bx, word ptr [bp+0Eh]
	and ax, ax
	jne L05D2
	and dx, dx
	jne L05D2
	cmp bx, 8
	jne L05D2
	cmp byte ptr _g_3DD2, 0
	jne L05D2
	mov bx, 4
	mov ax, word ptr [bp+10h]
	lds si, dword ptr [bp+0Ah]
L0594:
	mov cx, bx
	rep movsw
	add di, 138h
	dec ax
	jne L0594
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L05C8
	test byte ptr _g_4365, 0FFh
	je L05BC
	test byte ptr _g_4331, 0FFh
	je L05C8
	call far ptr _f_1B73_04BB
	jmp short L05C8
L05BC:
	test byte ptr _g_4366, 0FFh
	jne L05C8
	call far ptr _f_1B73_00D9
L05C8:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L05D2:
	add di, ax
	add dx, ax
	sub bx, dx
	lds si, dword ptr [bp+0Ah]
	add si, ax
	test bx, 1
	jne L05EB
	cmp byte ptr ss:_g_3DD2, 0
	jne L05EB
L05EB:
	push di
	mov cx, bx
L05EE:
	mov ah, byte ptr es:[di]
	lodsb
L05F2:
	and al, al
	stosb
	loop L05EE
	add si, dx
	pop di
	add di, 140h
	dec word ptr [bp+10h]
	jne L05EB
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L062C
	test byte ptr _g_4365, 0FFh
	je L0620
	test byte ptr _g_4331, 0FFh
	je L062C
	call far ptr _f_1B73_04BB
	jmp short L062C
L0620:
	test byte ptr _g_4366, 0FFh
	jne L062C
	call far ptr _f_1B73_00D9
L062C:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o02_3126_0512	endp

_o02_3126_0636	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o02_3126_0643
	call far ptr _f_1D8E_0BAE
	retf
_o02_3126_0636	endp

_o02_3126_0643	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L068C
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L068C
	cmp dx, word ptr _g_4342
	jl L068C
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L068C
	cmp dx, word ptr _g_4340
	jl L068C
	call far ptr _f_1B73_0196
L068C:
	mov di, word ptr [bp+8]
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov es, word ptr _g_3DB0
	add di, word ptr [bp+6]
	mov ax, word ptr _fd_55B3_3DE6
	mov dx, word ptr _fd_55B3_3DE8
	add di, ax
	add dx, ax
	mov word ptr _g_3DEA, dx
	mov bx, word ptr [bp+0Eh]
	sub bx, dx
	mov dh, byte ptr _g_3DE3
	mov dl, byte ptr _g_3DE1
	lds si, dword ptr [bp+0Ah]
	add si, ax
	mov ax, word ptr [bp+10h]
	mov word ptr [bp-2], ax
L06C3:
	push di
	mov cx, bx
L06C6:
	lodsb
	mov ah, al
	not ah
	and al, dl
	and ah, dh
	or al, ah
	mov ah, byte ptr es:[di]
L06D4:
	and al, al
	stosb
	loop L06C6
	add si, word ptr ss:_g_3DEA
	pop di
	add di, 140h
	dec word ptr [bp-2]
	jne L06C3
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0711
	test byte ptr _g_4365, 0FFh
	je L0705
	test byte ptr _g_4331, 0FFh
	je L0711
	call far ptr _f_1B73_04BB
	jmp short L0711
L0705:
	test byte ptr _g_4366, 0FFh
	jne L0711
	call far ptr _f_1B73_00D9
L0711:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L071B:
	mov ax, word ptr cs:L0501
	mov word ptr cs:L0372, ax
	retn
	mov ax, word ptr cs:L0503
	mov word ptr cs:L0372, ax
	retn
L072D:
	mov ax, word ptr cs:L0736
	mov word ptr cs:L0372, ax
	retn
L0736:
	and al, al
	not al
_o02_3126_0643	endp

_o02_3126_073A	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o02_3126_0747
	call far ptr _f_1D8E_0435
	retf
_o02_3126_073A	endp

_o02_3126_0747	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L078A
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, dx
	jle L0762
	xchg dx, ax
L0762:
	cmp ax, word ptr _g_4344
	jg L078A
	cmp dx, word ptr _g_4342
	jl L078A
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, dx
	jle L0779
	xchg dx, ax
L0779:
	cmp ax, word ptr _g_4346
	jg L078A
	cmp dx, word ptr _g_4340
	jl L078A
	call far ptr _f_1B73_0196
L078A:
	mov bx, word ptr [bp+0Eh]
	mov bl, bh
	push bx
	mov ax, word ptr [bp+6]
	mov bx, word ptr [bp+8]
	mov es, word ptr [bp+0Ch]
	mov bp, word ptr [bp+0Ah]
	mov si, 1
	mov di, 1
	mov dx, es
	sub dx, bx
	jge L07AC
	neg di
	neg dx
L07AC:
	mov word ptr _g_219E, di
	mov cx, bp
	sub cx, ax
	jge L07BA
	neg si
	neg cx
L07BA:
	mov word ptr _g_219C, si
	cmp cx, dx
	jge L07C9
	xor si, si
	xchg cx, dx
	jmp L07CB
L07C9:
	xor di, di
L07CB:
	mov word ptr _g_21A2, si
	mov word ptr _g_21A0, di
	mov si, ax
	mov di, bx
	mov ax, dx
	shl ax, 1
	mov dx, ax
	sub ax, cx
	mov bx, ax
	sub ax, cx
	inc cx
	mov bp, word ptr _g_3DB0
	mov es, bp
	pop bp
L07EB:
	push ax
	push di
	shl di, 1
	mov di, word ptr [di+_g_3DFC]
	mov ax, si
	add di, ax
	mov ax, bp
	mov byte ptr es:[di], al
	pop di
	pop ax
	cmp bx, 0
	jge L0812
	add si, word ptr _g_21A2
	add di, word ptr _g_21A0
	add bx, dx
	loop L07EB
	jmp L081E
L0812:
	add si, word ptr _g_219C
	add di, word ptr _g_219E
	add bx, ax
	loop L07EB
L081E:
	test byte ptr _g_4333, 0FFh
	jne L0846
	test byte ptr _g_4365, 0FFh
	je L083A
	test byte ptr _g_4331, 0FFh
	je L0846
	call far ptr _f_1B73_04BB
	jmp short L0846
L083A:
	test byte ptr _g_4366, 0FFh
	jne L0846
	call far ptr _f_1B73_00D9
L0846:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o02_3126_0747	endp

_o02_3126_084E	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pop di
	pop si
	pop bp
	retf
_o02_3126_084E	endp

_o02_3126_0857	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pop di
	pop si
	pop bp
	retf
_o02_3126_0857	endp

_o02_3126_0860	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L089D
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L089D
	cmp dx, word ptr _g_4342
	jl L089D
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L089D
	cmp dx, word ptr _g_4340
	jl L089D
	call far ptr _f_1B73_0196
	jmp L08D0
L089D:
	mov ax, word ptr [bp+0Eh]
	mov dx, ax
	add dx, word ptr [bp+0Ah]
	sub dx, word ptr [bp+6]
	cmp ax, word ptr _g_4346
	jg L08D0
	cmp dx, word ptr _g_4340
	jl L08D0
	mov ax, word ptr [bp+10h]
	mov dx, ax
	add dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	cmp ax, word ptr _g_4344
	jg L08D0
	cmp dx, word ptr _g_4342
	jl L08D0
	call far ptr _f_1B73_0196
L08D0:
	mov cx, word ptr [bp+10h]
	mov dx, 140h
	mov ax, word ptr [bp+8]
	cmp ax, cx
	jge L08E7
	mov ax, word ptr [bp+0Ch]
	add cx, ax
	sub cx, word ptr [bp+8]
	neg dx
L08E7:
	mov si, ax
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov di, cx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	mov cx, ax
	add si, ax
	mov bx, word ptr [bp+0Eh]
	add di, bx
	mov bx, ax
	mov ax, word ptr [bp+0Ah]
	sub ax, bx
	inc ax
	cmp cx, word ptr [bp+0Eh]
	jge L091B
	std
	add dx, ax
	add di, ax
	dec di
	add si, ax
	dec si
	jmp short L091D
L091B:
	sub dx, ax
L091D:
	mov bx, word ptr _g_3DB0
	mov ds, bx
	mov es, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	inc bx
L092C:
	mov cx, ax
	rep movsb
	add di, dx
	add si, dx
	dec bx
	jne L092C
	cld
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0961
	test byte ptr _g_4365, 0FFh
	je L0955
	test byte ptr _g_4331, 0FFh
	je L0961
	call far ptr _f_1B73_04BB
	jmp short L0961
L0955:
	test byte ptr _g_4366, 0FFh
	jne L0961
	call far ptr _f_1B73_00D9
L0961:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o02_3126_0860	endp

S02A_TEXT	ends
	end
