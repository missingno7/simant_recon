; Display driver S03 (dispatch table DGROUP:2276, 25 entries): screen, blit and raster-op procs.
; Overlay section S03, code frame 3126, linear 31260-32538.
; Genuine assembly, reproduced byte for byte by MASM 5.10.  Evidence against compiler output:
; framed procs save "push si; push di" (MSC always saves DI first, probe ASM-2 in
; build/workers/ovlA/probe), raster operations are selected by self-modifying code
; (instruction templates copied over loop instructions with "mov cs:[...],ax"), a 320-byte
; line buffer lives at offset 0 of the code segment (addressed as cs:[di]), and near
; subroutines return with retn inside far procs.
; The far pointers to the 25 entries live in the DGROUP dispatch table at 2276 (not reconstructed here).

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
	extrn	_g_5AAE:byte
; S03 private data (DGROUP:220E-2307): driver state, palette map (_g_2216), bank offsets,
; pixel masks, the dispatch table the game calls through and a far pointer to it, colour tables.
_g_220E	db	0, 0
_g_2210	db	0, 0
_g_2212	db	0, 0
_g_2214	db	0, 0
_g_2216	db	00Fh, 00Eh, 00Ch, 4, 00Dh, 5, 1, 00Bh, 2, 00Ah, 6, 6
	db	7, 7, 8, 0
_g_2226	db	0
_g_2227	db	0
_g_2228	db	0
_g_2229	db	0
_g_222A	db	0, 0
_g_222C	db	0, 0, 0, 0, 0, 020h, 0, 040h, 0, 060h
_g_2236	db	00Fh, 00Fh, 0F0h, 0F0h, 00Fh, 00Fh, 0F0h, 0F0h, 00Fh, 00Fh, 0F0h, 0F0h
	db	00Fh, 00Fh, 0F0h, 0F0h, 0FFh, 0F0h, 00Fh, 0FFh, 0F0h, 0FFh, 0FFh, 00Fh
	db	0FFh, 0F0h, 00Fh, 0FFh, 0F0h, 0FFh, 0FFh, 00Fh, 0FFh, 0FFh, 0FFh, 0FFh
	db	0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh, 0FFh
	db	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	db	0, 0, 0, 0
DispatchS03	label	dword
	dd	_o03_3126_019E
	dd	_o03_3126_01BE
	dd	_o03_3126_01DB
	dd	_o03_3126_059C
	dd	_o03_3126_03C2
	dd	_o03_3126_070A
	dd	_o03_3126_072D
	dd	_o03_3126_072D
	dd	_o03_3126_074E
	dd	_o03_3126_091F
	dd	_o03_3126_092C
	dd	_o03_3126_0C11
	dd	_o03_3126_0C1E
	dd	_o03_3126_08B8
	dd	_o03_3126_080A
	dd	_o03_3126_087E
	dd	_o03_3126_0844
	dd	_o03_3126_104D
	dd	_o03_3126_105A
	dd	_o03_3126_01F8
	dd	_o03_3126_01B3
	dd	_o03_3126_1180
	dd	_o03_3126_1189
	dd	_o03_3126_08F2
	dd	_o03_3126_1192
_g_22DA	dd	DGROUP:DispatchS03
	db	0
_g_22DF	db	0FFh, 00Fh, 0
_g_22E2	db	0F0h, 0FFh
_g_22E4	db	0, 0, 0, 0
_g_22E8	db	0, 0, 011h, 011h, 022h, 022h, 033h, 033h, 044h, 044h, 055h, 055h
	db	066h, 066h, 077h, 077h, 088h, 088h, 099h, 099h, 0AAh, 0AAh, 0BBh, 0BBh
	db	0CCh, 0CCh, 0DDh, 0DDh, 0EEh, 0EEh, 0FFh, 0FFh
_DATA	ends
DGROUP	group	_DATA

	extrn	_f_1B4E_015B:far
	extrn	_f_1B4E_0165:far
	extrn	_f_1B73_00D9:far
	extrn	_f_1B73_0196:far
	extrn	_f_1B73_04BB:far
	extrn	_f_1D8E_0384:far
	extrn	_f_1D8E_0435:far
	extrn	_f_1D8E_08EA:far
	extrn	_f_1D8E_09DE:far

S03A_TEXT	segment word public 'CODE'
	assume	cs:S03A_TEXT, ds:DGROUP

	public	_o03_3126_0140
	public	_o03_3126_019E
	public	_o03_3126_01B3
	public	_o03_3126_01BE
	public	_o03_3126_01DB
	public	_o03_3126_01F8
	public	_o03_3126_0210
	public	_o03_3126_03C2
	public	_o03_3126_03DA
	public	_o03_3126_059C
	public	_o03_3126_070A
	public	_o03_3126_072D
	public	_o03_3126_074E
	public	_o03_3126_080A
	public	_o03_3126_0844
	public	_o03_3126_087E
	public	_o03_3126_08B8
	public	_o03_3126_08F2
	public	_o03_3126_091F
	public	_o03_3126_092C
	public	_o03_3126_0A4D
	public	_o03_3126_0AEF
	public	_o03_3126_0B3F
	public	_o03_3126_0B88
	public	_o03_3126_0C11
	public	_o03_3126_0C1E
	public	_o03_3126_0F5D
	public	_o03_3126_104D
	public	_o03_3126_105A
	public	_o03_3126_1180
	public	_o03_3126_1189
	public	_o03_3126_1192

linebuf	db	320 dup (0)
_o03_3126_0140	proc	far
	push ds
	push es
	push si
	push di
	mov word ptr _g_3DB0, 0B800h
	mov cx, 0C8h
	mov word ptr _g_3DB4, cx
	mov word ptr _g_3DB2, 140h
	mov byte ptr _g_3DDC, 2
	mov byte ptr _g_3DDE, 8
	xor ax, ax
	mov di, 3DFCh
	mov es, word ptr _g_3DAE
L016A:
	stosw
	add ax, 2000h
	jns L0173
	add ax, 80A0h
L0173:
	loop L016A
	les si, dword ptr _g_22DA
	call far ptr _f_1B4E_0165
	mov ax, 9
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	mov ax, ds
	mov es, ax
	lea di, _g_41C0
	lea si, _g_2216
	mov cx, 8
	rep movsw
	pop di
	pop si
	pop es
	pop ds
	retf
_o03_3126_0140	endp

_o03_3126_019E	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	and al, 0Fh
	mov byte ptr _g_3DE0, al
	mov ax, word ptr [bp+8]
	and al, 0Fh
	mov byte ptr _g_3DE2, al
	pop bp
	retf
_o03_3126_019E	endp

_o03_3126_01B3	proc	far
	mov ax, 3
	push ax
	call far ptr _f_1B4E_015B
	pop ax
	retf
_o03_3126_01B3	endp

_o03_3126_01BE	proc	far
	les bx, dword ptr _g_3DA8
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, es
	mov byte ptr _g_3DDC, 6
	mov byte ptr _g_3DDE, 4
	mov word ptr _g_3DDA, 6
	retf
_o03_3126_01BE	endp

_o03_3126_01DB	proc	far
	les bx, dword ptr _g_3DA4
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, es
	mov byte ptr _g_3DDC, 8
	mov byte ptr _g_3DDE, 8
	mov word ptr _g_3DDA, 8
	retf
_o03_3126_01DB	endp

_o03_3126_01F8	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o03_3126_0210
	mov ax, S03A_TEXT
	push ax
	mov ax, 210h
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o03_3126_01F8	endp

_o03_3126_0210	proc	far
	push bp
	mov bp, sp
	sub sp, 6
	push si
	push di
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L0226
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L0226:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L0234
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L0234:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0268
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0268
	cmp dx, word ptr _g_4342
	jl L0268
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0268
	cmp dx, word ptr _g_4340
	jl L0268
	call far ptr _f_1B73_0196
L0268:
	xor bh, bh
	mov bl, byte ptr _g_3DE0
	shl bl, 1
	mov ax, word ptr [bx+_g_22E8]
	mov byte ptr [bp-4], al
	mov es, word ptr _g_3DB0
	mov bx, word ptr [bp+8]
	mov si, bx
	and si, 3
	mov ax, word ptr [bp+0Eh]
	and ax, 0Fh
	shl ax, 1
	shl ax, 1
	add si, ax
	shl si, 1
	mov word ptr [bp-2], si
	mov cx, word ptr [bp+0Ch]
	sub cx, bx
	je L02C3
	mov word ptr [bp+8], cx
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 1
	sar ax, 1
	mov bh, al
	add di, ax
	mov cx, word ptr [bp+0Ah]
	dec cx
	mov dh, cl
	and dh, 1
	sar cx, 1
	sub cl, bh
	inc cl
	jne L02C6
L02C3:
	jmp near ptr L0390
L02C6:
	mov bh, cl
	and bl, bl
	je L0312
	mov cx, word ptr [bp+8]
	push di
	push bx
L02D1:
	mov bx, di
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si+_g_2236]
	mov dl, al
	not dl
	and al, byte ptr [bp-4]
	and dl, byte ptr es:[di]
	or al, dl
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	mov byte ptr es:[di], al
	mov di, bx
	add si, 2
	and si, 0F7h
	add di, 2000h
	jns L0303
	add di, 80A0h
L0303:
	loop L02D1
	pop bx
	pop di
	inc di
	dec bh
	jne L030F
	jmp near ptr L0390
L030F:
	mov si, word ptr [bp-2]
L0312:
	and dh, dh
	jne L031A
	dec bh
	je L0353
L031A:
	mov bl, byte ptr [bp+8]
	xor ch, ch
	push di
L0320:
	push di
	mov cl, bh
	mov ah, byte ptr [si+_g_2236]
L0327:
	mov al, ah
	mov dl, al
	not dl
	and al, byte ptr [bp-4]
	and dl, byte ptr es:[di]
	or al, dl
	stosb
	loop L0327
	pop di
	add si, 2
	and si, 0F7h
	add di, 2000h
	jns L034A
	add di, 80A0h
L034A:
	dec bl
	jne L0320
	pop di
	and dh, dh
	jne L0390
L0353:
	mov bl, bh
	xor bh, bh
	add di, bx
	mov cx, word ptr [bp+8]
L035C:
	mov bx, di
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si+_g_2236]
	mov dl, al
	not dl
	and al, byte ptr [bp-4]
	and dl, byte ptr es:[di]
	or al, dl
	and ah, 0Fh
	and al, 0F0h
	or al, ah
	mov byte ptr es:[di], al
	mov di, bx
	add si, 2
	and si, 0F7h
	add di, 2000h
	jns L038E
	add di, 80A0h
L038E:
	loop L035C
L0390:
	test byte ptr _g_4333, 0FFh
	jne L03B8
	test byte ptr _g_4365, 0FFh
	je L03AC
	test byte ptr _g_4331, 0FFh
	je L03B8
	call far ptr _f_1B73_04BB
	jmp short L03B8
L03AC:
	test byte ptr _g_4366, 0FFh
	jne L03B8
	call far ptr _f_1B73_00D9
L03B8:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o03_3126_0210	endp

_o03_3126_03C2	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o03_3126_03DA
	mov ax, S03A_TEXT
	push ax
	mov ax, 3DAh
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
_o03_3126_03C2	endp

_o03_3126_03DA	proc	far
	push bp
	mov bp, sp
	sub sp, 6
	push si
	push di
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L03F0
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L03F0:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L03FE
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L03FE:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0432
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0432
	cmp dx, word ptr _g_4342
	jl L0432
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0432
	cmp dx, word ptr _g_4340
	jl L0432
	call far ptr _f_1B73_0196
L0432:
	xor bh, bh
	mov bl, byte ptr _g_3DE0
	shl bl, 1
	mov ax, word ptr [bx+_g_22E8]
	mov byte ptr [bp-4], al
	mov bl, byte ptr _g_3DE2
	shl bl, 1
	mov ax, word ptr [bx+_g_22E8]
	mov byte ptr [bp-6], al
	mov es, word ptr _g_3DB0
	mov bx, word ptr [bp+8]
	mov si, bx
	and si, 3
	mov ax, word ptr [bp+0Eh]
	and ax, 0Fh
	shl ax, 1
	shl ax, 1
	add si, ax
	shl si, 1
	mov word ptr [bp-2], si
	mov cx, word ptr [bp+0Ch]
	sub cx, bx
	je L049A
	mov word ptr [bp+8], cx
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 1
	sar ax, 1
	mov bh, al
	add di, ax
	mov cx, word ptr [bp+0Ah]
	dec cx
	mov dh, cl
	and dh, 1
	sar cx, 1
	sub cl, bh
	inc cl
	jne L049D
L049A:
	jmp near ptr L056A
L049D:
	mov bh, cl
	and bl, bl
	je L04E9
	mov cx, word ptr [bp+8]
	push di
	push bx
L04A8:
	mov bx, di
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si+_g_2236]
	mov dl, al
	not dl
	and al, byte ptr [bp-4]
	and dl, byte ptr [bp-6]
	or al, dl
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	mov byte ptr es:[di], al
	mov di, bx
	add si, 2
	and si, 0F7h
	add di, 2000h
	jns L04DA
	add di, 80A0h
L04DA:
	loop L04A8
	pop bx
	pop di
	inc di
	dec bh
	jne L04E6
	jmp near ptr L056A
L04E6:
	mov si, word ptr [bp-2]
L04E9:
	and dh, dh
	jne L04F1
	dec bh
	je L052A
L04F1:
	mov bl, byte ptr [bp+8]
	xor ch, ch
	push di
L04F7:
	push di
	mov cl, bh
	mov ah, byte ptr [si+_g_2236]
L04FE:
	mov al, ah
	mov dl, al
	not dl
	and al, byte ptr [bp-4]
	and dl, byte ptr [bp-6]
	or al, dl
	stosb
	loop L04FE
	pop di
	add si, 2
	and si, 0F7h
	add di, 2000h
	jns L0521
	add di, 80A0h
L0521:
	dec bl
	jne L04F7
	pop di
	and dh, dh
	jne L056A
L052A:
	mov si, word ptr [bp-2]
	mov bl, bh
	xor bh, bh
	add di, bx
	mov cx, word ptr [bp+8]
L0536:
	mov bx, di
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si+_g_2236]
	mov dl, al
	not dl
	and al, byte ptr [bp-4]
	and dl, byte ptr [bp-6]
	or al, dl
	and ah, 0Fh
	and al, 0F0h
	or al, ah
	mov byte ptr es:[di], al
	mov di, bx
	add si, 2
	and si, 0F7h
	add di, 2000h
	jns L0568
	add di, 80A0h
L0568:
	loop L0536
L056A:
	test byte ptr _g_4333, 0FFh
	jne L0592
	test byte ptr _g_4365, 0FFh
	je L0586
	test byte ptr _g_4331, 0FFh
	je L0592
	call far ptr _f_1B73_04BB
	jmp short L0592
L0586:
	test byte ptr _g_4366, 0FFh
	jne L0592
	call far ptr _f_1B73_00D9
L0592:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o03_3126_03DA	endp

_o03_3126_059C	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je L05B4
	mov ax, S03A_TEXT
	push ax
	mov ax, 5B4h
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
L05B4:
	push bp
	mov bp, sp
	push si
	push di
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L05C7
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L05C7:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L05D5
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L05D5:
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0609
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0609
	cmp dx, word ptr _g_4342
	jl L0609
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0609
	cmp dx, word ptr _g_4340
	jl L0609
	call far ptr _f_1B73_0196
L0609:
	mov bx, word ptr [bp+0Eh]
	and bx, 0Fh
	shl bx, 1
	mov dl, byte ptr [bx+_g_22E8]
	mov es, word ptr _g_3DB0
	mov bx, word ptr [bp+8]
	mov cx, word ptr [bp+0Ch]
	sub cx, bx
	je L064B
	mov word ptr [bp+8], cx
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov ax, word ptr [bp+6]
	mov bl, al
	and bl, 1
	sar ax, 1
	mov bh, al
	add di, ax
	mov cx, word ptr [bp+0Ah]
	dec cx
	mov dh, cl
	and dh, 1
	sar cx, 1
	sub cl, bh
	inc cl
	jne L064E
L064B:
	jmp near ptr L06DA
L064E:
	mov bh, cl
	and bl, bl
	je L067F
	mov cx, word ptr [bp+8]
	push di
L0658:
	mov si, di
	mov ah, byte ptr es:[di]
	mov al, dl
L065F:
	and al, al
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	mov byte ptr es:[di], al
	mov di, si
	add di, 2000h
	jns L0677
	add di, 80A0h
L0677:
	loop L0658
	pop di
	inc di
	dec bh
	je L06DA
L067F:
	and dh, dh
	jne L0687
	dec bh
	je L06B0
L0687:
	mov bl, byte ptr [bp+8]
	xor ch, ch
	push di
L068D:
	mov si, di
	mov cl, bh
L0691:
	mov al, dl
	mov ah, byte ptr es:[di]
L0696:
	and al, al
	stosb
	loop L0691
	mov di, si
	add di, 2000h
	jns L06A7
	add di, 80A0h
L06A7:
	dec bl
	jne L068D
	pop di
	and dh, dh
	jne L06DA
L06B0:
	mov bl, bh
	xor bh, bh
	add di, bx
	mov cx, word ptr [bp+8]
L06B9:
	mov si, di
	mov ah, byte ptr es:[di]
	mov al, dl
L06C0:
	and al, al
	and ah, 0Fh
	and al, 0F0h
	or al, ah
	mov byte ptr es:[di], al
	mov di, si
	add di, 2000h
	jns L06D8
	add di, 80A0h
L06D8:
	loop L06B9
L06DA:
	test byte ptr _g_4333, 0FFh
	jne L0702
	test byte ptr _g_4365, 0FFh
	je L06F6
	test byte ptr _g_4331, 0FFh
	je L0702
	call far ptr _f_1B73_04BB
	jmp short L0702
L06F6:
	test byte ptr _g_4366, 0FFh
	jne L0702
	call far ptr _f_1B73_00D9
L0702:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o03_3126_059C	endp

_o03_3126_070A	proc	far
	push bp
	mov bp, sp
	call near ptr L0EB8
	mov ax, 0Fh
	push ax
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o03_3126_059C
	add sp, 0Ah
	call near ptr L0EDA
	pop bp
	retf
_o03_3126_070A	endp

_o03_3126_072D	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+0Ah]
	dec ax
	sar ax, 1
	mov bx, word ptr [bp+6]
	sar bx, 1
	sub ax, bx
	inc ax
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	mul bx
	add ax, 4
	adc dx, 0
	pop bp
	retf
_o03_3126_072D	endp

_o03_3126_074E	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0788
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0788
	cmp dx, word ptr _g_4342
	jl L0788
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0788
	cmp dx, word ptr _g_4340
	jl L0788
	call far ptr _f_1B73_0196
L0788:
	les di, dword ptr [bp+0Eh]
	mov bx, 0A0h
	mov si, word ptr [bp+8]
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov dx, bx
	mov ax, word ptr [bp+6]
	sar ax, 1
	add si, ax
	mov bx, ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	sar ax, 1
	sub ax, bx
	inc ax
	push ax
	shl ax, 1
	stosw
	pop ax
	mov dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	je L07D9
	mov word ptr es:[di], dx
	add di, 2
	mov ds, word ptr _g_3DB0
	xor ch, ch
L07C4:
	mov bx, si
	mov cl, al
	rep movsb
	mov si, bx
	add si, 2000h
	jns L07D6
	add si, 80A0h
L07D6:
	dec dx
	jne L07C4
L07D9:
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0802
	test byte ptr _g_4365, 0FFh
	je L07F6
	test byte ptr _g_4331, 0FFh
	je L0802
	call far ptr _f_1B73_04BB
	jmp short L0802
L07F6:
	test byte ptr _g_4366, 0FFh
	jne L0802
	call far ptr _f_1B73_00D9
L0802:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o03_3126_074E	endp

_o03_3126_080A	proc	far
	mov ax, word ptr cs:L091B
	mov word ptr cs:L0B05, ax
	mov word ptr cs:L0B21, ax
	mov word ptr cs:L0B2F, ax
	mov word ptr cs:L0BD8, ax
	mov word ptr cs:L0BF3, ax
	mov word ptr cs:L0C01, ax
	mov word ptr cs:L0E68, ax
	mov word ptr cs:L0E87, ax
	mov word ptr cs:L0E9B, ax
	mov word ptr cs:L0FAD, ax
	mov word ptr cs:L0FCC, ax
	mov word ptr cs:L0FDC, ax
	mov byte ptr _g_3DD2, 18h
	retf
_o03_3126_080A	endp

_o03_3126_0844	proc	far
	mov ax, word ptr cs:L0EEB
	mov word ptr cs:L0E68, ax
	mov word ptr cs:L0E87, ax
	mov word ptr cs:L0E9B, ax
	mov word ptr cs:L0FAD, ax
	mov word ptr cs:L0FCC, ax
	mov word ptr cs:L0FDC, ax
	mov word ptr cs:L0B05, ax
	mov word ptr cs:L0B21, ax
	mov word ptr cs:L0B2F, ax
	mov word ptr cs:L0BD8, ax
	mov word ptr cs:L0BF3, ax
	mov word ptr cs:L0C01, ax
	mov byte ptr _g_3DD2, 0
	retf
_o03_3126_0844	endp

_o03_3126_087E	proc	far
	mov ax, word ptr cs:L0919
	mov word ptr cs:L0E68, ax
	mov word ptr cs:L0E87, ax
	mov word ptr cs:L0E9B, ax
	mov word ptr cs:L0FAD, ax
	mov word ptr cs:L0FCC, ax
	mov word ptr cs:L0FDC, ax
	mov word ptr cs:L0B05, ax
	mov word ptr cs:L0B21, ax
	mov word ptr cs:L0B2F, ax
	mov word ptr cs:L0BD8, ax
	mov word ptr cs:L0BF3, ax
	mov word ptr cs:L0C01, ax
	mov byte ptr _g_3DD2, 8
	retf
_o03_3126_087E	endp

_o03_3126_08B8	proc	far
	mov ax, word ptr cs:L091D
	mov word ptr cs:L0E68, ax
	mov word ptr cs:L0E87, ax
	mov word ptr cs:L0E9B, ax
	mov word ptr cs:L0FAD, ax
	mov word ptr cs:L0FCC, ax
	mov word ptr cs:L0FDC, ax
	mov word ptr cs:L0B05, ax
	mov word ptr cs:L0B21, ax
	mov word ptr cs:L0B2F, ax
	mov word ptr cs:L0BD8, ax
	mov word ptr cs:L0BF3, ax
	mov word ptr cs:L0C01, ax
	mov byte ptr _g_3DD2, 10h
	retf
_o03_3126_08B8	endp

_o03_3126_08F2	proc	far
	push bp
	mov bp, sp
	push cs
	mov ax, word ptr [bp+6]
	cmp al, 10h
	jne L0902
	call near ptr _o03_3126_08B8
	jmp short L0917
L0902:
	cmp al, 18h
	jne L090B
	call near ptr _o03_3126_080A
	jmp short L0917
L090B:
	cmp al, 8
	jne L0914
	call near ptr _o03_3126_087E
	jmp short L0917
L0914:
	call near ptr _o03_3126_0844
L0917:
	pop bp
	retf
L0919:
	and al, ah
L091B:
	xor al, ah
L091D:
	or al, ah
_o03_3126_08F2	endp

_o03_3126_091F	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o03_3126_092C
	call far ptr _f_1D8E_09DE
	retf
_o03_3126_091F	endp

_o03_3126_092C	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0975
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L0975
	cmp dx, word ptr _g_4342
	jl L0975
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L0975
	cmp dx, word ptr _g_4340
	jl L0975
	call far ptr _f_1B73_0196
L0975:
	mov bx, word ptr [bp+8]
	add bx, bx
	mov di, word ptr [bx+_g_3DFC]
	mov ax, word ptr [bp+6]
	test al, 1
	je L0988
	jmp near ptr L0A2A
L0988:
	cmp word ptr [bp+0Eh], 8
	jne L09B8
	cmp word ptr _fd_55B3_3DE6, 0
	jne L09B8
	cmp word ptr _fd_55B3_3DE8, 0
	jne L09B8
	mov cx, word ptr [bp+10h]
	mov es, word ptr _g_3DB0
	lds si, dword ptr [bp+0Ah]
	sar ax, 1
L09A8:
	add di, ax
	movsw
	movsw
	inc bx
	inc bx
	mov di, word ptr ss:[bx+3DFCh]
	loop L09A8
	jmp L09E1
L09B8:
	sar ax, 1
	add di, ax
	call near ptr _o03_3126_0A4D
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
	cmp byte ptr ss:_g_3DD2, 0
	je L0A14
L09CD:
	push di
	call near ptr _o03_3126_0AEF
	pop di
	add di, 2000h
	jns L09DC
	add di, 80A0h
L09DC:
	dec word ptr [bp-2]
	jne L09CD
L09E1:
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0A0A
	test byte ptr _g_4365, 0FFh
	je L09FE
	test byte ptr _g_4331, 0FFh
	je L0A0A
	call far ptr _f_1B73_04BB
	jmp short L0A0A
L09FE:
	test byte ptr _g_4366, 0FFh
	jne L0A0A
	call far ptr _f_1B73_00D9
L0A0A:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0A14:
	push di
	call near ptr _o03_3126_0B3F
	pop di
	add di, 2000h
	jns L0A23
	add di, 80A0h
L0A23:
	dec word ptr [bp-2]
	jne L0A14
	jmp L09E1
L0A2A:
	sar ax, 1
	add di, ax
	call near ptr _o03_3126_0A4D
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L0A37:
	push di
	call near ptr _o03_3126_0B88
	pop di
	add di, 2000h
	jns L0A46
	add di, 80A0h
L0A46:
	dec word ptr [bp-2]
	jne L0A37
	jmp L09E1
_o03_3126_092C	endp

_o03_3126_0A4D	proc	far
	mov ax, word ptr _fd_55B3_3DE6
	mov bx, word ptr [bp+6]
	mov bh, al
	and bl, 1
	and bh, 1
	add bl, bh
	sar bl, 1
	mov byte ptr _g_3DEF, bl
	sar ax, 1
	push ax
	mov byte ptr _g_3DEA, al
	mov bx, word ptr [bp+6]
	and bx, 1
	mov dx, bx
	shl bl, 1
	shl bl, 1
	mov byte ptr _g_3DEE, bl
	mov bx, dx
	add bx, word ptr _fd_55B3_3DE6
	and bx, 1
	mov ch, byte ptr [bx+_g_22DF]
	mov byte ptr _g_3DEC, ch
	mov ax, word ptr [bp+0Eh]
	mov bx, ax
	inc bx
	sar bx, 1
	mov byte ptr _g_3DF2, bl
	add ax, dx
	mov bx, ax
	inc ax
	shr ax, 1
	mov dl, al
	sub bx, word ptr _fd_55B3_3DE8
	mov ax, bx
	dec bx
	and bx, 1
	mov ch, byte ptr [bx+_g_22E2]
	mov byte ptr _g_3DED, ch
	add ax, 1
	shr ax, 1
	sub al, byte ptr _g_3DEA
	mov bl, al
	sub dl, al
	mov byte ptr _g_3DEA, dl
	cmp bl, 1
	jne L0AD7
	mov bh, byte ptr _g_3DEC
	and bh, byte ptr _g_3DED
	mov byte ptr _g_3DEC, bh
	mov byte ptr _g_3DED, bh
L0AD7:
	mov es, word ptr ss:_g_3DB0
	lds si, dword ptr [bp+0Ah]
	pop ax
	add di, ax
	add di, word ptr ss:_g_3DEF
	add si, ax
	sub bl, byte ptr ss:_g_3DEF
	retn
_o03_3126_0A4D	endp

_o03_3126_0AEF	proc	far
	add si, word ptr ss:_g_3DEF
	xor ch, ch
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L0B13
	mov ah, byte ptr es:[di]
	lodsb
L0B05:
	and al, al
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	stosb
	dec cl
	je L0B39
L0B13:
	mov bh, byte ptr ss:_g_3DED
	test bh, 0Fh
	je L0B24
L0B1D:
	mov ah, byte ptr es:[di]
	lodsb
L0B21:
	and al, al
	stosb
L0B24:
	loop L0B1D
	test bh, 0Fh
	jne L0B39
	mov ah, byte ptr es:[di]
	lodsb
L0B2F:
	and al, al
	and ah, 0Fh
	and al, 0F0h
	or al, ah
	stosb
L0B39:
	add si, word ptr ss:_g_3DEA
	retn
_o03_3126_0AEF	endp

_o03_3126_0B3F	proc	far
	add si, word ptr ss:_g_3DEF
	xor ch, ch
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L0B61
	mov ah, byte ptr es:[di]
	lodsb
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	stosb
	dec cl
	je L0B82
L0B61:
	mov bh, byte ptr ss:_g_3DED
	test bh, 0Fh
	je L0B6F
L0B6B:
	rep movsb
	jmp short L0B71
L0B6F:
	loop L0B6B
L0B71:
	test bh, 0Fh
	jne L0B82
	mov ah, byte ptr es:[di]
	lodsb
	and ah, 0Fh
	and al, 0F0h
	or al, ah
	stosb
L0B82:
	add si, word ptr ss:_g_3DEA
	retn
_o03_3126_0B3F	endp

_o03_3126_0B88	proc	far
	push ds
	push bp
	mov bp, sp
	sub sp, 0A2h
	push bx
	push ax
	mov ch, byte ptr ss:_g_3DF2
	xor dh, dh
	lea bx, [bp-0A2h]
L0B9D:
	lodsb
	mov ah, al
	xor al, al
	shr ax, 1
	shr ax, 1
	shr ax, 1
	shr ax, 1
	or ah, dh
	mov byte ptr ss:[bx], ah
	inc bx
	mov dh, al
	dec ch
	jne L0B9D
	mov byte ptr ss:[bx], dh
	pop ax
	pop bx
	mov ax, ss
	mov ds, ax
	push si
	lea si, [bp-0A2h]
	add si, word ptr _g_3DEF
	xor ch, ch
	mov cl, bl
	mov bh, byte ptr _g_3DEC
	and bh, bh
	js L0BE6
	mov ah, byte ptr es:[di]
	lodsb
L0BD8:
	and al, al
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	stosb
	dec cl
	je L0C0B
L0BE6:
	mov bh, byte ptr _g_3DED
	test bh, 1
	je L0BF6
L0BEF:
	mov ah, byte ptr es:[di]
	lodsb
L0BF3:
	and al, al
	stosb
L0BF6:
	loop L0BEF
	test bh, 1
	jne L0C0B
	mov ah, byte ptr es:[di]
	lodsb
L0C01:
	and al, al
	and ah, 0Fh
	and al, 0F0h
	or al, ah
	stosb
L0C0B:
	pop si
	mov sp, bp
	pop bp
	pop ds
	retn
_o03_3126_0B88	endp

_o03_3126_0C11	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o03_3126_0C1E
	call far ptr _f_1D8E_08EA
	retf
_o03_3126_0C11	endp

_o03_3126_0C1E	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0C67
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L0C67
	cmp dx, word ptr _g_4342
	jl L0C67
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L0C67
	cmp dx, word ptr _g_4340
	jl L0C67
	call far ptr _f_1B73_0196
L0C67:
	mov bl, byte ptr _g_3DE0
	shl bl, 1
	xor bh, bh
	mov al, byte ptr [bx+_g_22E8]
	mov byte ptr _g_2229, al
	mov bl, byte ptr _g_3DE2
	shl bl, 1
	xor bh, bh
	mov ah, byte ptr [bx+_g_22E8]
	mov byte ptr _g_2226, ah
	mov bl, ah
	xor bl, al
	and bl, 0F0h
	xor bl, al
	mov byte ptr _g_2227, bl
	rol bl, 1
	rol bl, 1
	rol bl, 1
	rol bl, 1
	mov byte ptr _g_2228, bl
	mov ax, word ptr [bp+8]
	mov di, ax
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	test ax, 1
	jne L0D06
	sar ax, 1
	add di, ax
	call near ptr L0D29
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L0CBF:
	push di
	call near ptr L0DDC
	pop di
	add di, 2000h
	jns L0CCE
	add di, 80A0h
L0CCE:
	dec word ptr [bp-2]
	jne L0CBF
L0CD3:
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L0CFC
	test byte ptr _g_4365, 0FFh
	je L0CF0
	test byte ptr _g_4331, 0FFh
	je L0CFC
	call far ptr _f_1B73_04BB
	jmp short L0CFC
L0CF0:
	test byte ptr _g_4366, 0FFh
	jne L0CFC
	call far ptr _f_1B73_00D9
L0CFC:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0D06:
	sar ax, 1
	add di, ax
	call near ptr L0D29
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L0D13:
	push di
	call near ptr L0EEF
	pop di
	add di, 2000h
	jns L0D22
	add di, 80A0h
L0D22:
	dec word ptr [bp-2]
	jne L0D13
	jmp L0CD3
L0D29:
	mov ax, word ptr _fd_55B3_3DE6
	mov bx, word ptr [bp+6]
	mov bh, al
	and bl, 1
	and bh, 1
	add bl, bh
	sar bl, 1
	mov byte ptr _g_3DEF, bl
	sar ax, 1
	push ax
	mov byte ptr _g_3DEA, al
	mov bx, word ptr [bp+6]
	and bx, 1
	mov dx, bx
	shl bl, 1
	shl bl, 1
	mov byte ptr _g_3DEE, bl
	mov bx, dx
	add bx, word ptr _fd_55B3_3DE6
	and bx, 1
	mov ch, byte ptr [bx+_g_22DF]
	mov byte ptr _g_3DEC, ch
	mov ax, word ptr [bp+0Eh]
	mov bx, ax
	add bx, 7
	shr bx, 1
	shr bx, 1
	shr bx, 1
	mov word ptr _g_222A, bx
	mov bx, ax
	inc bx
	sar bx, 1
	mov byte ptr _g_3DF2, bl
	add ax, dx
	mov bx, ax
	inc ax
	shr ax, 1
	mov dl, al
	sub bx, word ptr _fd_55B3_3DE8
	mov ax, bx
	dec bx
	and bx, 1
	mov ch, byte ptr [bx+_g_22E2]
	mov byte ptr _g_3DED, ch
	add ax, 1
	shr ax, 1
	sub al, byte ptr _g_3DEA
	mov bl, al
	sub dl, al
	mov byte ptr _g_3DEA, dl
	cmp bl, 1
	jne L0DC2
	mov bh, byte ptr _g_3DEC
	and bh, byte ptr _g_3DED
	mov byte ptr _g_3DEC, bh
	mov byte ptr _g_3DED, bh
L0DC2:
	mov es, word ptr ss:_g_3DB0
	lds si, dword ptr [bp+0Ah]
	pop ax
	add di, ax
	add di, word ptr ss:_g_3DEF
	mov word ptr ss:_g_222C, ax
	sub bl, byte ptr ss:_g_3DEF
	retn
L0DDC:
	push bx
	push di
	mov cx, word ptr ss:_g_222A
	lea di, ds:[0]
L0DE7:
	mov bh, byte ptr [si]
	inc si
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	mov bh, dl
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	mov bh, dl
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	mov bh, dl
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	loop L0DE7
	pop di
	pop bx
	push si
	lea si, ds:[0]
	add si, word ptr ss:_g_222C
	xor ch, ch
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L0EA4
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L0E74
	mov al, byte ptr cs:[si]
	inc si
	mov ah, byte ptr es:[di]
L0E68:
	and al, al
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	stosb
	dec cl
L0E74:
	xor ch, ch
	mov bh, byte ptr ss:_g_3DED
	test bh, 0Fh
	je L0E8A
L0E80:
	mov al, byte ptr cs:[si]
	inc si
	mov ah, byte ptr es:[di]
L0E87:
	and al, al
	stosb
L0E8A:
	loop L0E80
	test bh, 0Fh
	jne L0EA2
	mov cx, 0FF0h
L0E94:
	mov al, byte ptr cs:[si]
	inc si
	mov ah, byte ptr es:[di]
L0E9B:
	and al, al
	and ax, cx
	or al, ah
	stosb
L0EA2:
	pop si
	retn
L0EA4:
	mov cx, 0FFh
	cmp bh, 0FFh
	je L0E94
	mov cx, 0FF0h
	test bh, 0Fh
	je L0E94
	xchg cl, ch
	jmp L0E94
L0EB8:
	mov ax, word ptr cs:L091B
	mov word ptr cs:L065F, ax
	mov word ptr cs:L0696, ax
	mov word ptr cs:L06C0, ax
	retn
	mov ax, word ptr cs:L091D
	mov word ptr cs:L065F, ax
	mov word ptr cs:L0696, ax
	mov word ptr cs:L06C0, ax
	retn
L0EDA:
	mov ax, word ptr cs:L0EEB
	mov word ptr cs:L065F, ax
	mov word ptr cs:L0696, ax
	mov word ptr cs:L06C0, ax
	retn
L0EEB:
	and al, al
	not al
L0EEF:
	push bx
	push di
	mov cx, word ptr ss:_g_222A
	lea di, ds:[0]
L0EFA:
	mov bh, byte ptr [si]
	inc si
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	mov bh, dl
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	mov bh, dl
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	mov bh, dl
	xor bl, bl
	rol bx, 1
	rol bx, 1
	mov dl, bh
	xor bh, bh
	mov al, byte ptr ss:[bx+2226h]
	mov byte ptr cs:[di], al
	inc di
	loop L0EFA
	pop di
	pop bx
	push si
	lea si, ds:[0]
	add si, word ptr ss:_g_222C
_o03_3126_0C1E	endp

_o03_3126_0F5D	proc	far
	push bp
	mov bp, sp
	sub sp, 0A2h
	push bx
	push ax
	mov ch, byte ptr ss:_g_3DF2
	xor dh, dh
	lea bx, [bp-0A2h]
L0F71:
	mov al, byte ptr cs:[si]
	inc si
	mov ah, al
	xor al, al
	shr ax, 1
	shr ax, 1
	shr ax, 1
	shr ax, 1
	or ah, dh
	mov byte ptr ss:[bx], ah
	inc bx
	mov dh, al
	dec ch
	jne L0F71
	mov byte ptr ss:[bx], dh
	pop ax
	pop bx
	lea si, [bp-0A2h]
	add si, word ptr ss:_g_3DEF
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L0FBB
	mov al, byte ptr ss:[si]
	inc si
	mov ah, byte ptr es:[di]
L0FAD:
	and al, al
	and ah, 0F0h
	and al, 0Fh
	or al, ah
	stosb
	dec cl
	je L0FE7
L0FBB:
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L0FCF
L0FC5:
	mov al, byte ptr ss:[si]
	inc si
	mov ah, byte ptr es:[di]
L0FCC:
	and al, al
	stosb
L0FCF:
	loop L0FC5
	test bh, 1
	jne L0FE7
	mov al, byte ptr ss:[si]
	mov ah, byte ptr es:[di]
L0FDC:
	and al, al
	and ah, 0Fh
	and al, 0F0h
	inc si
	or al, ah
	stosb
L0FE7:
	mov sp, bp
	pop bp
	pop si
	retn
	cmp bl, 1
	je L1032
	mov ah, byte ptr ss:_g_3DEC
	and ah, ah
	js L1013
	mov cl, bl
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si]
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	and al, byte ptr ss:_g_22E4
	stosb
	dec cl
L1013:
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	jne L101F
	dec cl
L101F:
	xor ch, ch
	mov al, byte ptr [si]
	mov ah, byte ptr es:[di]
	and al, byte ptr ss:_g_22E4
	rep stosb
	test bh, 1
	jne L1047
L1032:
	mov ah, byte ptr es:[di]
	mov dh, bh
	not dh
	and ah, dh
	mov al, byte ptr [si]
	and al, bh
	or al, ah
	and al, byte ptr ss:_g_22E4
	stosb
L1047:
	add si, word ptr ss:_g_3DEA
	retn
_o03_3126_0F5D	endp

_o03_3126_104D	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o03_3126_105A
	call far ptr _f_1D8E_0435
	retf
_o03_3126_104D	endp

_o03_3126_105A	proc	far
	push bp
	mov bp, sp
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L109D
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, dx
	jle L1075
	xchg dx, ax
L1075:
	cmp ax, word ptr _g_4344
	jg L109D
	cmp dx, word ptr _g_4342
	jl L109D
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, dx
	jle L108C
	xchg dx, ax
L108C:
	cmp ax, word ptr _g_4346
	jg L109D
	cmp dx, word ptr _g_4340
	jl L109D
	call far ptr _f_1B73_0196
L109D:
	mov bx, word ptr [bp+0Eh]
	and bx, 0Fh
	add bx, bx
	mov dx, word ptr [bx+_g_22E8]
	push dx
	mov ax, word ptr [bp+6]
	mov bx, word ptr [bp+8]
	mov es, word ptr [bp+0Ch]
	mov bp, word ptr [bp+0Ah]
	mov si, 1
	mov di, 1
	mov dx, es
	sub dx, bx
	jge L10C6
	neg di
	neg dx
L10C6:
	mov word ptr _g_220E, di
	mov cx, bp
	sub cx, ax
	jge L10D4
	neg si
	neg cx
L10D4:
	mov word ptr _g_2210, si
	cmp cx, dx
	jge L10E3
	xor si, si
	xchg cx, dx
	jmp L10E5
L10E3:
	xor di, di
L10E5:
	mov word ptr _g_2214, si
	mov word ptr _g_2212, di
	mov si, ax
	mov di, bx
	mov ax, dx
	shl ax, 1
	mov dx, ax
	sub ax, cx
	mov bx, ax
	sub ax, cx
	inc cx
	mov bp, 0B800h
	mov es, bp
	pop bp
L1104:
	push ax
	push di
	shl di, 1
	mov di, word ptr [di+_g_3DFC]
	mov ax, si
	sar ax, 1
	add di, ax
	mov ax, bp
	mov ah, 0F0h
	and al, 0Fh
	test si, 1
	jne L1128
	not ah
	shl al, 1
	shl al, 1
	shl al, 1
	shl al, 1
L1128:
	and byte ptr es:[di], ah
	or byte ptr es:[di], al
	pop di
	pop ax
	cmp bx, 0
	jge L1144
	add si, word ptr _g_2214
	add di, word ptr _g_2212
	add bx, dx
	loop L1104
	jmp L1150
L1144:
	add si, word ptr _g_2210
	add di, word ptr _g_220E
	add bx, ax
	loop L1104
L1150:
	test byte ptr _g_4333, 0FFh
	jne L1178
	test byte ptr _g_4365, 0FFh
	je L116C
	test byte ptr _g_4331, 0FFh
	je L1178
	call far ptr _f_1B73_04BB
	jmp short L1178
L116C:
	test byte ptr _g_4366, 0FFh
	jne L1178
	call far ptr _f_1B73_00D9
L1178:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o03_3126_105A	endp

_o03_3126_1180	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pop di
	pop si
	pop bp
	retf
_o03_3126_1180	endp

_o03_3126_1189	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pop di
	pop si
	pop bp
	retf
_o03_3126_1189	endp

_o03_3126_1192	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L11CF
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L11CF
	cmp dx, word ptr _g_4342
	jl L11CF
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L11CF
	cmp dx, word ptr _g_4340
	jl L11CF
	call far ptr _f_1B73_0196
	jmp L1202
L11CF:
	mov ax, word ptr [bp+0Eh]
	mov dx, ax
	add dx, word ptr [bp+0Ah]
	sub dx, word ptr [bp+6]
	cmp ax, word ptr _g_4346
	jg L1202
	cmp dx, word ptr _g_4340
	jl L1202
	mov ax, word ptr [bp+10h]
	mov dx, ax
	add dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	cmp ax, word ptr _g_4344
	jg L1202
	cmp dx, word ptr _g_4342
	jl L1202
	call far ptr _f_1B73_0196
L1202:
	mov cx, word ptr [bp+10h]
	mov dx, 0A0h
	mov ax, word ptr [bp+8]
	cmp ax, cx
	jge L1219
	mov ax, word ptr [bp+0Ch]
	add cx, ax
	sub cx, word ptr [bp+8]
	neg dx
L1219:
	mov si, ax
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov di, cx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	sar ax, 1
	add si, ax
	mov bx, word ptr [bp+0Eh]
	sar bx, 1
	add di, bx
	mov bh, al
	mov ax, word ptr [bp+0Ah]
	sar ax, 1
	sub al, bh
	inc al
	cmp bh, bl
	jge L1251
	std
	add dx, ax
	add di, ax
	dec di
	add si, ax
	dec si
	jmp short L1253
L1251:
	sub dx, ax
L1253:
	mov bx, word ptr _g_3DB0
	mov ds, bx
	mov es, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	inc bx
	and dx, dx
	js L12B7
L1266:
	mov cx, ax
	push di
	push si
	rep movsb
	pop si
	pop di
	add di, 2000h
	jns L1278
	add di, 80A0h
L1278:
	add si, 2000h
	jns L1282
	add si, 80A0h
L1282:
	dec bx
	jne L1266
L1285:
	cld
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L12AF
	test byte ptr _g_4365, 0FFh
	je L12A3
	test byte ptr _g_4331, 0FFh
	je L12AF
	call far ptr _f_1B73_04BB
	jmp short L12AF
L12A3:
	test byte ptr _g_4366, 0FFh
	jne L12AF
	call far ptr _f_1B73_00D9
L12AF:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
L12B7:
	mov cx, ax
	push si
	push di
	rep movsb
	pop di
	pop si
	sub di, 2000h
	jns L12C9
	sub di, 80A0h
L12C9:
	sub si, 2000h
	jns L12D3
	sub si, 80A0h
L12D3:
	dec bx
	jne L12B7
	jmp L1285
_o03_3126_1192	endp

S03A_TEXT	ends
	end
