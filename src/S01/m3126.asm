; Display driver S01 (dispatch table DGROUP:211A, 25 entries): screen, blit and raster-op procs.
; Overlay section S01, code frame 3126, linear 31260-328EA.
; Genuine assembly, reproduced byte for byte by MASM 5.10.  Evidence against compiler output:
; framed procs save "push si; push di" (MSC always saves DI first, probe ASM-2 in
; build/workers/ovlA/probe), raster operations are selected by self-modifying code
; (instruction templates copied over loop instructions with "mov cs:[...],ax"), and near
; subroutines return with retn inside far procs.  o01_3126_1637 reprograms the 6845 CRTC
; from the DGROUP table g_2190 and sets BIOS video mode 7 (Hercules/MDA text) directly.
; The far pointers to the 25 entries live in the DGROUP dispatch table at 211A (not reconstructed here).

_DATA	segment word public 'DATA'
	extrn	_fd_55B3_3DE6:byte
	extrn	_fd_55B3_3DE8:byte
	extrn	_g_2100:byte
	extrn	_g_2118:byte
	extrn	_g_217E:byte
	extrn	_g_2182:byte
	extrn	_g_2184:byte
	extrn	_g_2190:byte
	extrn	_g_3D20:byte
	extrn	_g_3DA4:byte
	extrn	_g_3DA8:byte
	extrn	_g_3DAC:byte
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
	extrn	_g_3DE0:byte
	extrn	_g_3DE2:byte
	extrn	_g_3DE4:byte
	extrn	_g_3DE5:byte
	extrn	_g_3DEA:byte
	extrn	_g_3DEC:byte
	extrn	_g_3DED:byte
	extrn	_g_3DEE:byte
	extrn	_g_3DEF:byte
	extrn	_g_3DF1:byte
	extrn	_g_3DF2:byte
	extrn	_g_3DFC:byte
	extrn	_g_4220:byte
	extrn	_g_4331:byte
	extrn	_g_4333:byte
	extrn	_g_4340:byte
	extrn	_g_4342:byte
	extrn	_g_4344:byte
	extrn	_g_4346:byte
	extrn	_g_4365:byte
	extrn	_g_4366:byte
	extrn	_g_5AAE:byte
	extrn	_g_9188:byte
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

S01A_TEXT	segment word public 'CODE'
	assume	cs:S01A_TEXT, ds:DGROUP

	public	_o01_3126_0000
	public	_o01_3126_0068
	public	_o01_3126_007D
	public	_o01_3126_010A
	public	_o01_3126_0167
	public	_o01_3126_019A
	public	_o01_3126_01B2
	public	_o01_3126_01CA
	public	_o01_3126_024C
	public	_o01_3126_0414
	public	_o01_3126_0437
	public	_o01_3126_045D
	public	_o01_3126_0516
	public	_o01_3126_0523
	public	_o01_3126_069C
	public	_o01_3126_073C
	public	_o01_3126_0749
	public	_o01_3126_083D
	public	_o01_3126_08E3
	public	_o01_3126_093C
	public	_o01_3126_098E
	public	_o01_3126_0A20
	public	_o01_3126_0A7A
	public	_o01_3126_0ACC
	public	_o01_3126_0B26
	public	_o01_3126_0C53
	public	_o01_3126_0C7A
	public	_o01_3126_0C87
	public	_o01_3126_0F33
	public	_o01_3126_0F66
	public	_o01_3126_0F6F
	public	_o01_3126_0F78
	public	_o01_3126_0F83
	public	_o01_3126_109D
	public	_o01_3126_11F0
	public	_o01_3126_1343
	public	_o01_3126_14B6
	public	_o01_3126_1610
	public	_o01_3126_1637
	public	_o01_3126_1658

_o01_3126_0000	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push ds
	push es
	push si
	push di
	mov word ptr _g_3DB0, 0B800h
	mov cx, 190h
	mov word ptr _g_3DB4, cx
	mov word ptr _g_3DB2, 280h
	xor ax, ax
	mov di, 3DFCh
	mov es, word ptr _g_3DAE
L0026:
	stosw
	add ax, 2000h
	jns L002F
	add ax, 8050h
L002F:
	loop L0026
	les si, dword ptr _g_217E
	call far ptr _f_1B4E_0165
	lea bx, _g_9188
	mov ax, 11F0h
	mov word ptr [bx], ax
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	mov word ptr _g_3DAC, ax
	mov word ptr _g_2182, 40h
	push word ptr _g_2182
	call far ptr _f_1B4E_015B
	pop ax
	xor ax, ax
	pop di
	pop si
	pop es
	pop ds
	mov sp, bp
	pop bp
	retf
_o01_3126_0000	endp

_o01_3126_0068	proc	far
	push bp
	mov bp, sp
	sub sp, 6
	push ds
	push es
	push si
	push di
	mov cx, 1E0h
	mov word ptr _g_2182, 11h
	jmp short L00A1
_o01_3126_0068	endp

_o01_3126_007D	proc	far
	push bp
	mov bp, sp
	sub sp, 6
	push ds
	push es
	push si
	push di
	xor ax, ax
	mov es, ax
	cmp byte ptr es:[463h], 0D4h
	je L0098
	mov ax, 0Fh
	jmp short L009B
L0098:
	mov ax, 10h
L009B:
	mov word ptr _g_2182, ax
	mov cx, 15Eh
L00A1:
	mov word ptr _g_3DB4, cx
	mov word ptr _g_3DB2, 280h
	xor ax, ax
	mov di, 3DFCh
	mov es, word ptr _g_3DAE
L00B4:
	stosw
	add ax, 50h
	loop L00B4
	les si, dword ptr _g_217E
	call far ptr _f_1B4E_0165
	lea bx, _g_9188
	mov ax, 0F83h
	mov word ptr [bx], ax
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	mov word ptr _g_3DAC, ax
	push word ptr _g_2182
	call far ptr _f_1B4E_015B
	pop ax
	call near ptr _o01_3126_0F33
	mov al, 1
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 0
	out dx, al
	mov al, 4
	mov dx, 3CEh
	out dx, al
	inc dx
	mov al, 1
	out dx, al
	mov al, 2
	mov dx, 3C4h
	out dx, al
	inc dx
	mov al, 0Fh
	out dx, al
	pop di
	pop si
	pop es
	pop ds
	mov sp, bp
	pop bp
	retf
_o01_3126_007D	endp

_o01_3126_010A	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push ds
	push es
	push si
	push di
	mov word ptr _g_3DB0, 0B000h
	mov cx, 15Ch
	mov word ptr _g_3DB4, cx
	mov word ptr _g_3DB2, 2D0h
	xor ax, ax
	mov di, 3DFCh
	mov es, word ptr _g_3DAE
L0130:
	stosw
	add ax, 2000h
	jns L0139
	add ax, 805Ah
L0139:
	loop L0130
	les si, dword ptr _g_217E
	call far ptr _f_1B4E_0165
	lea bx, _g_9188
	mov ax, 109Dh
	mov word ptr [bx], ax
	xor ax, ax
	mov es, ax
	mov al, byte ptr es:[449h]
	mov word ptr _g_3DAC, ax
	call far ptr _o01_3126_1610
	xor ax, ax
	pop di
	pop si
	pop es
	pop ds
	mov sp, bp
	pop bp
	retf
_o01_3126_010A	endp

_o01_3126_0167	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+0Ah]
	mov ah, al
	mov bx, word ptr _g_3DE4
	and ax, 70F0h
	mov word ptr _g_3DE4, ax
	mov word ptr _g_3DE0, ax
	mov cx, word ptr [bp+8]
	mov word ptr _g_3DE2, cx
	xor bx, ax
	test bx, 80h
	je L0198
	test ax, 80h
	jne L0195
	call near ptr L0B9D
	jmp short L0198
L0195:
	call near ptr L0B80
L0198:
	pop bp
	retf
_o01_3126_0167	endp

_o01_3126_019A	proc	far
	mov byte ptr _g_3DDC, 8
	les bx, dword ptr _g_3DA8
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, es
	mov word ptr _g_3DDA, 8
	retf
_o01_3126_019A	endp

_o01_3126_01B2	proc	far
	mov byte ptr _g_3DDC, 0Eh
	les bx, dword ptr _g_3DA4
	mov word ptr _g_3DD6, bx
	mov word ptr _g_3DD8, es
	mov word ptr _g_3DDA, 0Eh
	retf
_o01_3126_01B2	endp

_o01_3126_01CA	proc	far
	push bp
	mov bp, sp
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0201
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0201
	cmp dx, word ptr _g_4342
	jl L0201
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0201
	cmp dx, word ptr _g_4340
	jl L0201
	call far ptr _f_1B73_0196
L0201:
	call near ptr L0BBA
	push word ptr [bp+0Eh]
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o01_3126_024C
	add sp, 0Ah
	call near ptr L0BCB
	test byte ptr _g_4333, 0FFh
	jne L0246
	test byte ptr _g_4365, 0FFh
	je L023A
	test byte ptr _g_4331, 0FFh
	je L0246
	call far ptr _f_1B73_04BB
	jmp short L0246
L023A:
	test byte ptr _g_4366, 0FFh
	jne L0246
	call far ptr _f_1B73_00D9
L0246:
	dec byte ptr _g_3DD4
	pop bp
	retf
_o01_3126_01CA	endp

_o01_3126_024C	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je L0264
	mov ax, S01A_TEXT
	push ax
	mov ax, 264h
	push ax
	call far ptr _f_1D8E_0384
	add sp, 4
	retf
L0264:
	push bp
	mov bp, sp
	sub sp, 8
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L02A0
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L02A0
	cmp dx, word ptr _g_4342
	jl L02A0
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L02A0
	cmp dx, word ptr _g_4340
	jl L02A0
	call far ptr _f_1B73_0196
L02A0:
	mov ax, word ptr [bp+6]
	cmp ax, word ptr [bp+0Ah]
	jb L02AE
	xchg word ptr [bp+0Ah], ax
	xchg word ptr [bp+6], ax
L02AE:
	mov ax, word ptr [bp+8]
	cmp ax, word ptr [bp+0Ch]
	jb L02BC
	xchg word ptr [bp+0Ch], ax
	xchg word ptr [bp+8], ax
L02BC:
	mov es, word ptr _g_3DB0
	mov ax, word ptr [bp+8]
	mov si, word ptr [bp+0Eh]
	and si, 70h
	mov bx, ax
	and bx, 3
	shl bx, 1
	add si, bx
	mov word ptr [bp-2], si
	mov cx, word ptr [bp+0Ch]
	sub cx, ax
	jle L030E
	mov word ptr [bp+8], cx
	mov di, ax
	add di, di
	mov word ptr [bp-6], di
	mov ax, word ptr [bp+6]
	mov cl, al
	and cl, 7
	sar ax, 1
	sar ax, 1
	sar ax, 1
	mov dh, al
	mov word ptr [bp-8], ax
	mov ax, word ptr [bp+0Ah]
	dec ax
	mov bl, al
	and bl, 7
	sar ax, 1
	sar ax, 1
	sar ax, 1
	mov bh, al
	sub bh, dh
	jge L0311
L030E:
	jmp near ptr L03E2
L0311:
	inc bh
	mov si, di
	and cl, cl
	je L0365
	xor ch, ch
	mov si, cx
	mov dl, byte ptr [si+_g_3DC1]
	dec bh
	jne L032E
	mov si, bx
	and dl, byte ptr [si+_g_3DCA]
	jmp near ptr L03B3
L032E:
	mov dh, dl
	not dh
	push di
	mov cx, word ptr [bp+8]
	mov si, word ptr [bp-2]
L0339:
	push di
	mov di, word ptr [di+_g_3DFC]
	add di, word ptr [bp-8]
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si+_g_4220]
L0348:
	and al, al
	and ah, dh
	and al, dl
	or al, ah
	mov byte ptr es:[di], al
	pop di
	inc di
	inc di
	add si, 2
	and si, -9
	loop L0339
	mov si, word ptr [bp-2]
	pop di
	inc word ptr [bp-8]
L0365:
	cmp bl, 7
	je L036E
	dec bh
	je L03A7
L036E:
	xor ch, ch
	push di
	mov ax, word ptr [bp+8]
	mov word ptr [bp-4], ax
	mov si, word ptr [bp-2]
L037A:
	push di
	mov di, word ptr ss:[di+3DFCh]
	add di, word ptr [bp-8]
	mov cl, bh
	mov dl, byte ptr [si+_g_4220]
L0389:
	mov al, dl
	mov ah, byte ptr es:[di]
L038E:
	and al, al
	stosb
	loop L0389
	pop di
	inc di
	inc di
	add si, 2
	and si, -9
	dec word ptr [bp-4]
	jne L037A
	pop di
	cmp bl, 7
	je L03E2
L03A7:
	mov al, bh
	cbw
	add word ptr [bp-8], ax
	xor bh, bh
	mov dl, byte ptr [bx+_g_3DCA]
L03B3:
	mov dh, dl
	not dh
	mov cx, word ptr [bp+8]
	mov si, word ptr [bp-2]
L03BD:
	push di
	mov di, word ptr [di+_g_3DFC]
	add di, word ptr [bp-8]
	mov ah, byte ptr es:[di]
	mov al, byte ptr [si+_g_4220]
L03CC:
	and al, al
	and ah, dh
	and al, dl
	or ah, al
	mov byte ptr es:[di], ah
	pop di
	inc di
	inc di
	add si, 2
	and si, -9
	loop L03BD
L03E2:
	test byte ptr _g_4333, 0FFh
	jne L040A
	test byte ptr _g_4365, 0FFh
	je L03FE
	test byte ptr _g_4331, 0FFh
	je L040A
	call far ptr _f_1B73_04BB
	jmp short L040A
L03FE:
	test byte ptr _g_4366, 0FFh
	jne L040A
	call far ptr _f_1B73_00D9
L040A:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o01_3126_024C	endp

_o01_3126_0414	proc	far
	push bp
	mov bp, sp
	call near ptr L0BDC
	mov ax, 40h
	push ax
	push word ptr [bp+0Ch]
	push word ptr [bp+0Ah]
	push word ptr [bp+8]
	push word ptr [bp+6]
	call far ptr _o01_3126_024C
	add sp, 0Ah
	call near ptr L0BCB
	pop bp
	retf
_o01_3126_0414	endp

_o01_3126_0437	proc	far
	push bp
	mov bp, sp
	call near ptr L0444
	xor dx, dx
	add ax, 4
	pop bp
	retf
L0444:
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
_o01_3126_0437	endp

_o01_3126_045D	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L049A
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L049A
	cmp dx, word ptr _g_4342
	jl L049A
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L049A
	cmp dx, word ptr _g_4340
	jl L049A
	call far ptr _f_1B73_0196
L049A:
	les di, dword ptr [bp+0Eh]
	mov si, word ptr [bp+8]
	add si, si
	mov dx, bx
	mov cl, 3
	mov ax, word ptr [bp+6]
	sar ax, cl
	mov word ptr [bp-2], ax
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
	mov bx, si
L04D2:
	mov si, word ptr ss:[bx+3DFCh]
	add si, word ptr [bp-2]
	mov cl, al
	rep movsb
	inc bx
	inc bx
	dec dx
	jne L04D2
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L050C
	test byte ptr _g_4365, 0FFh
	je L0500
	test byte ptr _g_4331, 0FFh
	je L050C
	call far ptr _f_1B73_04BB
	jmp short L050C
L0500:
	test byte ptr _g_4366, 0FFh
	jne L050C
	call far ptr _f_1B73_00D9
L050C:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
_o01_3126_045D	endp

_o01_3126_0516	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o01_3126_0523
	call far ptr _f_1D8E_070E
	retf
_o01_3126_0516	endp

_o01_3126_0523	proc	far
	push bp
	mov bp, sp
	sub sp, 4
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L056C
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L056C
	cmp dx, word ptr _g_4342
	jl L056C
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L056C
	cmp dx, word ptr _g_4340
	jl L056C
	call far ptr _f_1B73_0196
L056C:
	mov di, word ptr [bp+8]
	add di, di
	mov dx, bx
	mov cl, 3
	mov ax, word ptr [bp+6]
	test ax, 7
	je L0580
	jmp L05F4
L0580:
	sar ax, cl
	mov word ptr [bp-4], ax
	call near ptr _o01_3126_083D
	mov bx, word ptr [bp+8]
	and bx, 3
	shl bx, 1
	add bl, byte ptr ss:_g_3DE5
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L059B:
	push di
	push bx
	mov di, word ptr ss:[di+3DFCh]
	add di, word ptr [bp-4]
	mov bh, byte ptr ss:[bx+4220h]
	mov byte ptr ss:_g_2118, bh
	call near ptr L062E
	pop bx
	inc bx
	inc bx
	and bx, 0F7h
	pop di
	inc di
	inc di
	dec word ptr [bp-2]
	jne L059B
L05C1:
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L05EA
	test byte ptr _g_4365, 0FFh
	je L05DE
	test byte ptr _g_4331, 0FFh
	je L05EA
	call far ptr _f_1B73_04BB
	jmp short L05EA
L05DE:
	test byte ptr _g_4366, 0FFh
	jne L05EA
	call far ptr _f_1B73_00D9
L05EA:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L05F4:
	sar ax, cl
	mov word ptr [bp-4], ax
	call near ptr _o01_3126_083D
	mov bx, word ptr [bp+8]
	and bx, 3
	shl bx, 1
	add bl, byte ptr ss:_g_3DE5
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L060F:
	push di
	push bx
	mov di, word ptr ss:[di+3DFCh]
	add di, word ptr [bp-4]
	call near ptr _o01_3126_069C
	pop bx
	add bx, 2
	and bx, 0F7h
	pop di
	inc di
	inc di
	dec word ptr [bp-2]
	jne L060F
	jmp L05C1
L062E:
	add si, word ptr ss:_g_3DEF
	mov bl, byte ptr ss:_g_3DF1
	mov bh, byte ptr ss:_g_2118
	cmp bl, 1
	je L067E
	mov cl, bl
	mov ch, byte ptr ss:_g_3DEC
	and ch, ch
	js L0662
	lodsb
L064E:
	and al, al
	mov ah, byte ptr es:[di]
L0653:
	and al, al
	mov dh, ch
	not dh
	and ah, dh
	and al, ch
	or al, ah
	stosb
	dec cl
L0662:
	xor ch, ch
	mov bl, byte ptr ss:_g_3DED
	test bl, 1
	je L0677
L066E:
	lodsb
L066F:
	and al, al
	mov ah, byte ptr es:[di]
L0674:
	and al, al
	stosb
L0677:
	loop L066E
	test bl, 1
	jne L0696
L067E:
	mov bl, byte ptr ss:_g_3DED
	lodsb
L0684:
	and al, al
	mov ah, byte ptr es:[di]
L0689:
	and al, al
	mov dh, bl
	not dh
	and ah, dh
	and al, bl
	or al, ah
	stosb
L0696:
	add si, word ptr ss:_g_3DEA
	retn
_o01_3126_0523	endp

_o01_3126_069C	proc	far
	push bp
	mov bp, sp
	sub sp, 5Ch
	push ax
	mov cl, byte ptr ss:_g_3DEE
	mov ch, byte ptr ss:_g_3DF2
	xor dh, dh
	lea bx, [bp-5Ch]
L06B2:
	lodsb
	mov ah, al
	xor al, al
	shr ax, cl
	or ah, dh
	mov byte ptr ss:[bx], ah
	inc bx
	mov dh, al
	dec ch
	jne L06B2
	mov byte ptr ss:[bx], dh
	pop ax
	push si
	lea si, [bp-5Ch]
	add si, word ptr ss:_g_3DEF
	mov cl, byte ptr ss:_g_3DF1
	cmp cl, 1
	je L071C
	xor ch, ch
	mov bl, byte ptr ss:_g_3DEC
	and bl, bl
	js L06FF
	mov al, byte ptr ss:[si]
	inc si
L06EB:
	and al, al
	mov ah, byte ptr es:[di]
L06F0:
	and al, al
	mov dh, bl
	not dh
	and ah, dh
	and al, bl
	or al, ah
	stosb
	dec cl
L06FF:
	mov bl, byte ptr ss:_g_3DED
	test bl, 1
	je L0715
L0709:
	mov al, byte ptr ss:[si]
	inc si
L070D:
	and al, al
	mov ah, byte ptr es:[di]
L0712:
	and al, al
	stosb
L0715:
	loop L0709
	test bl, 1
	jne L0737
L071C:
	mov bl, byte ptr ss:_g_3DED
	mov al, byte ptr ss:[si]
	inc si
L0725:
	and al, al
	mov ah, byte ptr es:[di]
L072A:
	and al, al
	mov dh, bl
	not dh
	and ah, dh
	and al, bl
	or al, ah
	stosb
L0737:
	pop si
	mov sp, bp
	pop bp
	retn
_o01_3126_069C	endp

_o01_3126_073C	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o01_3126_0749
	call far ptr _f_1D8E_07F6
	retf
_o01_3126_073C	endp

_o01_3126_0749	proc	far
	push bp
	mov bp, sp
	sub sp, 4
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0792
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+10h]
	add dx, ax
	cmp ax, word ptr _g_4344
	jg L0792
	cmp dx, word ptr _g_4342
	jl L0792
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Eh]
	add dx, ax
	sub dx, word ptr _fd_55B3_3DE8
	add ax, word ptr _fd_55B3_3DE6
	cmp ax, word ptr _g_4346
	jg L0792
	cmp dx, word ptr _g_4340
	jl L0792
	call far ptr _f_1B73_0196
L0792:
	mov bx, word ptr [bp+8]
	add bx, bx
	mov di, bx
	mov cl, 3
	mov ax, word ptr [bp+6]
	test ax, 7
	je L07A6
	jmp L0819
L07A6:
	sar ax, cl
	mov word ptr [bp-4], ax
	call near ptr _o01_3126_083D
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
	cmp byte ptr ss:_g_3DD2, 0
	je L0803
L07BC:
	push di
	mov di, word ptr ss:[di+3DFCh]
	add di, word ptr [bp-4]
	call near ptr _o01_3126_08E3
	pop di
	inc di
	inc di
	dec word ptr [bp-2]
	jne L07BC
L07D0:
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L07F9
	test byte ptr _g_4365, 0FFh
	je L07ED
	test byte ptr _g_4331, 0FFh
	je L07F9
	call far ptr _f_1B73_04BB
	jmp short L07F9
L07ED:
	test byte ptr _g_4366, 0FFh
	jne L07F9
	call far ptr _f_1B73_00D9
L07F9:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0803:
	push di
	mov di, word ptr ss:[di+3DFCh]
	add di, word ptr [bp-4]
	call near ptr _o01_3126_093C
	pop di
	inc di
	inc di
	dec word ptr [bp-2]
	jne L0803
	jmp L07D0
L0819:
	sar ax, cl
	mov word ptr [bp-4], ax
	call near ptr _o01_3126_083D
	mov dx, word ptr [bp+10h]
	mov word ptr [bp-2], dx
L0827:
	push di
	mov di, word ptr ss:[di+3DFCh]
	add di, word ptr [bp-4]
	call near ptr _o01_3126_098E
	pop di
	inc di
	inc di
	dec word ptr [bp-2]
	jne L0827
	jmp L07D0
_o01_3126_0749	endp

_o01_3126_083D	proc	far
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
	jne L08C8
	mov bh, byte ptr _g_3DEC
	and bh, byte ptr _g_3DED
	mov byte ptr _g_3DED, bh
L08C8:
	mov es, word ptr ss:_g_3DB0
	lds si, dword ptr [bp+0Ah]
	mov ax, word ptr ss:_g_3DEF
	add word ptr [bp-4], ax
	pop ax
	add word ptr [bp-4], ax
	add si, ax
	mov byte ptr ss:_g_3DF1, bl
	retn
_o01_3126_083D	endp

_o01_3126_08E3	proc	far
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L0925
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L090B
	mov ah, byte ptr es:[di]
	lodsb
L08FC:
	and al, al
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	stosb
	dec cl
L090B:
	xor ch, ch
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L091E
L0917:
	lodsb
	mov ah, byte ptr es:[di]
L091B:
	and al, al
	stosb
L091E:
	loop L0917
	test bh, 1
	jne L0936
L0925:
	lodsb
	mov ah, byte ptr es:[di]
L0929:
	and al, al
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	stosb
L0936:
	add si, word ptr ss:_g_3DEA
	retn
_o01_3126_08E3	endp

_o01_3126_093C	proc	far
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L0979
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L0962
	mov ah, byte ptr es:[di]
	lodsb
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	stosb
	dec cl
L0962:
	xor ch, ch
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L0972
L096E:
	rep movsb
	jmp short L0974
L0972:
	loop L096E
L0974:
	test bh, 1
	jne L0988
L0979:
	lodsb
	mov ah, byte ptr es:[di]
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	stosb
L0988:
	add si, word ptr ss:_g_3DEA
	retn
_o01_3126_093C	endp

_o01_3126_098E	proc	far
	push bp
	mov bp, sp
	sub sp, 5Ch
	push bx
	push ax
	mov cl, byte ptr ss:_g_3DEE
	mov ch, byte ptr ss:_g_3DF2
	xor dh, dh
	lea bx, [bp-5Ch]
L09A5:
	lodsb
	mov ah, al
	xor al, al
	shr ax, cl
	or ah, dh
	mov byte ptr ss:[bx], ah
	inc bx
	mov dh, al
	dec ch
	jne L09A5
	mov byte ptr ss:[bx], dh
	pop ax
	pop bx
	push si
	lea si, [bp-5Ch]
	add si, word ptr ss:_g_3DEF
	cmp bl, 1
	je L0A07
	mov cl, bl
	mov bh, byte ptr ss:_g_3DEC
	and bh, bh
	js L09EC
	mov ah, byte ptr es:[di]
	mov al, byte ptr ss:[si]
	inc si
L09DD:
	and al, al
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	stosb
	dec cl
L09EC:
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	je L0A00
L09F6:
	mov al, byte ptr ss:[si]
	inc si
	mov ah, byte ptr es:[di]
L09FD:
	and al, al
	stosb
L0A00:
	loop L09F6
	test bh, 1
	jne L0A1B
L0A07:
	mov ah, byte ptr es:[di]
	mov al, byte ptr ss:[si]
	inc si
L0A0E:
	and al, al
	mov dh, bh
	not dh
	and ah, dh
	and al, bh
	or al, ah
	stosb
L0A1B:
	pop si
	mov sp, bp
	pop bp
	retn
_o01_3126_098E	endp

_o01_3126_0A20	proc	far
	mov ax, word ptr cs:L0BFB
	mov word ptr cs:L0653, ax
	mov word ptr cs:L0674, ax
	mov word ptr cs:L0689, ax
	mov word ptr cs:L06F0, ax
	mov word ptr cs:L0712, ax
	mov word ptr cs:L072A, ax
	mov word ptr cs:L08FC, ax
	mov word ptr cs:L091B, ax
	mov word ptr cs:L0929, ax
	mov word ptr cs:L09DD, ax
	mov word ptr cs:L09FD, ax
	mov word ptr cs:L0A0E, ax
	mov ax, word ptr cs:L0BFF
	mov word ptr cs:L0D54, ax
	mov ax, word ptr cs:L0C01
	mov word ptr cs:L0D39, ax
	mov word ptr cs:L0D6A, ax
	mov word ptr cs:L0E39, ax
	mov word ptr cs:L0EA7, ax
	mov word ptr cs:L0F03, ax
	mov byte ptr _g_3DD2, 18h
	retf
_o01_3126_0A20	endp

_o01_3126_0A7A	proc	far
	mov ax, word ptr cs:L0BED
	mov word ptr cs:L0653, ax
	mov word ptr cs:L0674, ax
	mov word ptr cs:L0689, ax
	mov word ptr cs:L06F0, ax
	mov word ptr cs:L0712, ax
	mov word ptr cs:L072A, ax
	mov word ptr cs:L08FC, ax
	mov word ptr cs:L091B, ax
	mov word ptr cs:L0929, ax
	mov word ptr cs:L09DD, ax
	mov word ptr cs:L09FD, ax
	mov word ptr cs:L0A0E, ax
	mov word ptr cs:L0D39, ax
	mov word ptr cs:L0D6A, ax
	mov word ptr cs:L0E39, ax
	mov word ptr cs:L0EA7, ax
	mov word ptr cs:L0F03, ax
	mov word ptr cs:L0D54, ax
	mov byte ptr _g_3DD2, 0
	retf
_o01_3126_0A7A	endp

_o01_3126_0ACC	proc	far
	mov ax, word ptr cs:L0BF1
	mov word ptr cs:L0653, ax
	mov word ptr cs:L0674, ax
	mov word ptr cs:L0689, ax
	mov word ptr cs:L06F0, ax
	mov word ptr cs:L0712, ax
	mov word ptr cs:L072A, ax
	mov word ptr cs:L08FC, ax
	mov word ptr cs:L091B, ax
	mov word ptr cs:L0929, ax
	mov word ptr cs:L09DD, ax
	mov word ptr cs:L09FD, ax
	mov word ptr cs:L0A0E, ax
	mov ax, word ptr cs:L0BF3
	mov word ptr cs:L0D54, ax
	mov ax, word ptr cs:L0BF5
	mov word ptr cs:L0D39, ax
	mov word ptr cs:L0D6A, ax
	mov word ptr cs:L0E39, ax
	mov word ptr cs:L0EA7, ax
	mov word ptr cs:L0F03, ax
	mov byte ptr _g_3DD2, 8
	retf
_o01_3126_0ACC	endp

_o01_3126_0B26	proc	far
	mov ax, word ptr cs:L0BFD
	mov word ptr cs:L0653, ax
	mov word ptr cs:L0674, ax
	mov word ptr cs:L0689, ax
	mov word ptr cs:L06F0, ax
	mov word ptr cs:L0712, ax
	mov word ptr cs:L072A, ax
	mov word ptr cs:L08FC, ax
	mov word ptr cs:L091B, ax
	mov word ptr cs:L0929, ax
	mov word ptr cs:L09DD, ax
	mov word ptr cs:L09FD, ax
	mov word ptr cs:L0A0E, ax
	mov ax, word ptr cs:L0BF7
	mov word ptr cs:L0D54, ax
	mov ax, word ptr cs:L0BF9
	mov word ptr cs:L0D39, ax
	mov word ptr cs:L0D6A, ax
	mov word ptr cs:L0E39, ax
	mov word ptr cs:L0EA7, ax
	mov word ptr cs:L0F03, ax
	mov byte ptr _g_3DD2, 10h
	retf
L0B80:
	mov ax, word ptr cs:L0BEF
	mov word ptr cs:L064E, ax
	mov word ptr cs:L066F, ax
	mov word ptr cs:L0684, ax
	mov word ptr cs:L06EB, ax
	mov word ptr cs:L070D, ax
	mov word ptr cs:L0725, ax
	retn
L0B9D:
	mov ax, word ptr cs:L0BED
	mov word ptr cs:L064E, ax
	mov word ptr cs:L066F, ax
	mov word ptr cs:L0684, ax
	mov word ptr cs:L06EB, ax
	mov word ptr cs:L070D, ax
	mov word ptr cs:L0725, ax
	retn
L0BBA:
	mov ax, word ptr cs:L0BFD
	mov word ptr cs:L0348, ax
	mov word ptr cs:L038E, ax
	mov word ptr cs:L03CC, ax
	retn
L0BCB:
	mov ax, word ptr cs:L0BED
	mov word ptr cs:L0348, ax
	mov word ptr cs:L038E, ax
	mov word ptr cs:L03CC, ax
	retn
L0BDC:
	mov ax, word ptr cs:L0BFB
	mov word ptr cs:L0348, ax
	mov word ptr cs:L038E, ax
	mov word ptr cs:L03CC, ax
	retn
L0BED:
	and al, al
L0BEF:
	not al
L0BF1:
	and al, ah
L0BF3:
	and al, dh
L0BF5:
	and ah, dl
L0BF7:
	or al, dh
L0BF9:
	or ah, dl
L0BFB:
	xor al, ah
L0BFD:
	or al, ah
L0BFF:
	xor al, dh
L0C01:
	xor ah, dl
	cmp bl, 1
	je L0C3D
	mov ah, byte ptr ss:_g_3DEC
	and ah, ah
	js L0C25
	mov cl, bl
	mov ah, byte ptr es:[di]
	mov dh, bh
	not dh
	and ah, dh
	mov al, byte ptr [si]
	and al, bh
	or al, ah
	stosb
	dec cl
L0C25:
	mov bh, byte ptr ss:_g_3DED
	test bh, 1
	jne L0C31
	dec cl
L0C31:
	xor ch, ch
L0C33:
	mov al, byte ptr [si]
	stosb
	loop L0C33
	test bh, 1
	jne L0C4D
L0C3D:
	mov ah, byte ptr es:[di]
	mov dh, bh
	not dh
	and ah, dh
	mov al, byte ptr [si]
	and al, bh
	or al, ah
	stosb
L0C4D:
	add si, word ptr ss:_g_3DEA
	retn
_o01_3126_0B26	endp

_o01_3126_0C53	proc	far
	push bp
	mov bp, sp
	push cs
	mov ax, word ptr [bp+6]
	cmp al, 10h
	jne L0C63
	call near ptr _o01_3126_0B26
	jmp short L0C78
L0C63:
	cmp al, 18h
	jne L0C6C
	call near ptr _o01_3126_0A20
	jmp short L0C78
L0C6C:
	cmp al, 8
	jne L0C75
	call near ptr _o01_3126_0ACC
	jmp short L0C78
L0C75:
	call near ptr _o01_3126_0A7A
L0C78:
	pop bp
	retf
_o01_3126_0C53	endp

_o01_3126_0C7A	proc	far
	mov ax, word ptr _g_5AAE
	and ax, ax
	je _o01_3126_0C87
	call far ptr _f_1D8E_0435
	retf
_o01_3126_0C7A	endp

_o01_3126_0C87	proc	far
	push bp
	mov bp, sp
	sub sp, 0Ch
	push si
	push di
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0CCD
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, dx
	jle L0CA5
	xchg dx, ax
L0CA5:
	cmp ax, word ptr _g_4344
	jg L0CCD
	cmp dx, word ptr _g_4342
	jl L0CCD
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, dx
	jle L0CBC
	xchg dx, ax
L0CBC:
	cmp ax, word ptr _g_4346
	jg L0CCD
	cmp dx, word ptr _g_4340
	jl L0CCD
	call far ptr _f_1B73_0196
L0CCD:
	mov ax, word ptr _g_3DB0
	mov es, ax
	mov bx, word ptr [bp+0Eh]
	and bx, 70h
	mov cx, word ptr [bp+8]
	cmp cx, word ptr [bp+0Ch]
	je L0CE3
	jmp near ptr L0D76
L0CE3:
	mov di, cx
	and cx, 3
	shr cx, 1
	add bx, cx
	mov dx, word ptr [bx+_g_4220]
	mov word ptr [bp-0Ah], dx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov bx, word ptr [bp+6]
	mov cx, word ptr [bp+0Ah]
	cmp bx, cx
	jle L0D05
	xchg cx, bx
L0D05:
	mov si, bx
	and si, 7
	mov al, byte ptr [si+_g_3DC1]
	mov si, cx
	and si, 7
	mov ah, byte ptr [si+_g_3DCA]
	sar cx, 1
	sar cx, 1
	sar cx, 1
	sar bx, 1
	sar bx, 1
	sar bx, 1
	add di, bx
	sub cx, bx
	jne L0D2D
	and ah, al
	jmp short L0D5E
L0D2D:
	mov dh, al
	not dh
	mov dl, byte ptr es:[di]
	mov bh, ah
	mov ah, byte ptr [bp-0Ah]
L0D39:
	and al, al
	and dl, dh
	and al, ah
	or al, dl
	stosb
	mov ah, bh
	cmp ah, 0FFh
	je L0D4C
	dec cx
	je L0D5E
L0D4C:
	mov ah, byte ptr [bp-0Ah]
L0D4F:
	mov al, ah
	mov dh, byte ptr es:[di]
L0D54:
	and al, al
	stosb
	loop L0D4F
	cmp ah, 0FFh
	je L0D73
L0D5E:
	mov dh, ah
	not dh
	mov dl, byte ptr es:[di]
	mov al, ah
	mov ah, byte ptr [bp-0Ah]
L0D6A:
	and al, al
	and dl, dh
	and al, ah
	or al, dl
	stosb
L0D73:
	jmp L0DE5
L0D76:
	mov word ptr [bp+0Eh], bx
	mov word ptr [bp-8], 1
	mov dx, word ptr [bp+0Ch]
	mov ax, word ptr [bp+0Ah]
	mov di, ax
	mov bx, word ptr [bp+6]
	sub ax, bx
	jge L0D96
	mov bx, di
	xchg dx, cx
	neg ax
	mov word ptr [bp+6], bx
L0D96:
	mov word ptr [bp+8], ax
	sub dx, cx
	jge L0DA2
	neg word ptr [bp-8]
	neg dx
L0DA2:
	mov word ptr [bp+0Ch], dx
	mov si, bx
	and bx, 7
	mov al, byte ptr [bx+_g_2100]
	sar si, 1
	sar si, 1
	sar si, 1
	mov word ptr [bp-2], cx
	and cx, 3
	shl cx, 1
	mov bx, word ptr [bp+0Eh]
	add bx, cx
	mov bl, byte ptr [bx+_g_4220]
	mov byte ptr [bp-0Ch], bl
	mov bx, word ptr [bp-2]
	add bx, bx
	mov bx, word ptr [bx+_g_3DFC]
	mov cx, 0
	mov dx, word ptr [bp+8]
	cmp dx, word ptr [bp+0Ch]
	jl L0DE2
	call near ptr L0E17
	jmp L0DE5
L0DE2:
	call near ptr L0E81
L0DE5:
	test byte ptr _g_4333, 0FFh
	jne L0E0D
	test byte ptr _g_4365, 0FFh
	je L0E01
	test byte ptr _g_4331, 0FFh
	je L0E0D
	call far ptr _f_1B73_04BB
	jmp short L0E0D
L0E01:
	test byte ptr _g_4366, 0FFh
	jne L0E0D
	call far ptr _f_1B73_00D9
L0E0D:
	dec byte ptr _g_3DD4
	pop di
	pop si
	mov sp, bp
	pop bp
	retf
L0E17:
	cmp si, 50h
	jge L0E80
	mov di, word ptr [bp+0Ch]
	mov dx, word ptr [bp+8]
	mov word ptr [bp-4], dx
	shr dx, 1
	mov word ptr [bp-6], dx
	mov dh, al
	not dh
	cmp si, 0
	jl L0E44
L0E33:
	mov ah, byte ptr [bp-0Ch]
	mov dl, byte ptr es:[bx+si]
L0E39:
	and al, al
	and ah, al
	and dl, dh
	or dl, ah
	mov byte ptr es:[bx+si], dl
L0E44:
	ror dh, 1
	ror al, 1
	jae L0E50
	inc si
	cmp si, 50h
	je L0E80
L0E50:
	add cx, di
	cmp cx, word ptr [bp-6]
	jle L0E7B
	sub cx, word ptr [bp+8]
	mov bx, word ptr [bp-2]
	add bx, word ptr [bp-8]
	mov word ptr [bp-2], bx
	and bx, 3
	add bx, bx
	add bx, word ptr [bp+0Eh]
	mov bl, byte ptr [bx+_g_4220]
	mov byte ptr [bp-0Ch], bl
	mov bx, word ptr [bp-2]
	add bx, bx
	mov bx, word ptr [bx+_g_3DFC]
L0E7B:
	dec word ptr [bp-4]
	jge L0E33
L0E80:
	retn
L0E81:
	cmp si, 50h
	jge L0EEE
	mov di, word ptr [bp+8]
	or di, di
	je L0EEF
	mov dx, word ptr [bp+0Ch]
	mov word ptr [bp-4], dx
	shr dx, 1
	mov word ptr [bp-6], dx
	mov dh, al
	not dh
L0E9C:
	cmp si, 0
	jl L0EB2
	mov dl, byte ptr es:[bx+si]
	mov ah, byte ptr [bp-0Ch]
L0EA7:
	and al, al
	and dl, dh
	and ah, al
	or ah, dl
	mov byte ptr es:[bx+si], ah
L0EB2:
	mov bx, word ptr [bp-2]
	add bx, word ptr [bp-8]
	mov word ptr [bp-2], bx
	add bx, bx
	and bx, 6
	add bx, word ptr [bp+0Eh]
	mov bl, byte ptr [bx+_g_4220]
	mov byte ptr [bp-0Ch], bl
	mov bx, word ptr [bp-2]
	add bx, bx
	mov bx, word ptr [bx+_g_3DFC]
	add cx, di
	cmp cx, word ptr [bp-6]
	jle L0EE9
	sub cx, word ptr [bp+0Ch]
	ror dh, 1
	ror al, 1
	jae L0EE9
	inc si
	cmp si, 50h
	je L0EEE
L0EE9:
	dec word ptr [bp-4]
	jge L0E9C
L0EEE:
	retn
L0EEF:
	cmp si, 0
	jl L0EEE
	mov cx, word ptr [bp+0Ch]
	mov dh, al
	not dh
L0EFB:
	add bx, si
	mov dl, byte ptr es:[bx]
	mov ah, byte ptr [bp-0Ch]
L0F03:
	and al, al
	and dl, dh
	and ah, al
	or ah, dl
	mov byte ptr es:[bx], ah
	mov bx, word ptr [bp-2]
	add bx, word ptr [bp-8]
	mov word ptr [bp-2], bx
	and bx, 3
	add bx, bx
	add bx, word ptr [bp+0Eh]
	mov bl, byte ptr [bx+_g_4220]
	mov byte ptr [bp-0Ch], bl
	mov bx, word ptr [bp-2]
	add bx, bx
	mov bx, word ptr [bx+_g_3DFC]
	dec cx
	jge L0EFB
	retn
_o01_3126_0C87	endp

_o01_3126_0F33	proc	far
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
	retn
_o01_3126_0F33	endp

_o01_3126_0F66	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pop di
	pop si
	pop bp
	retf
_o01_3126_0F66	endp

_o01_3126_0F6F	proc	far
	push bp
	mov bp, sp
	push si
	push di
	pop di
	pop si
	pop bp
	retf
_o01_3126_0F6F	endp

_o01_3126_0F78	proc	far
	push word ptr _g_3DAC
	call far ptr _f_1B4E_015B
	pop ax
	retf
_o01_3126_0F78	endp

_o01_3126_0F83	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L0FC0
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L0FC0
	cmp dx, word ptr _g_4342
	jl L0FC0
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L0FC0
	cmp dx, word ptr _g_4340
	jl L0FC0
	call far ptr _f_1B73_0196
	jmp L0FF3
L0FC0:
	mov ax, word ptr [bp+0Eh]
	mov dx, ax
	add dx, word ptr [bp+0Ah]
	sub dx, word ptr [bp+6]
	cmp ax, word ptr _g_4346
	jg L0FF3
	cmp dx, word ptr _g_4340
	jl L0FF3
	mov ax, word ptr [bp+10h]
	mov dx, ax
	add dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	cmp ax, word ptr _g_4344
	jg L0FF3
	cmp dx, word ptr _g_4342
	jl L0FF3
	call far ptr _f_1B73_0196
L0FF3:
	mov cx, word ptr [bp+10h]
	mov dx, word ptr _g_3DB6
	mov ax, word ptr [bp+8]
	cmp ax, cx
	jge L100B
	mov ax, word ptr [bp+0Ch]
	add cx, ax
	sub cx, word ptr [bp+8]
	neg dx
L100B:
	mov si, ax
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov di, cx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	sar ax, 1
	sar ax, 1
	sar ax, 1
	add si, ax
	mov bx, word ptr [bp+0Eh]
	sar bx, 1
	sar bx, 1
	sar bx, 1
	add di, bx
	mov bh, al
	mov ax, word ptr [bp+0Ah]
	sar ax, 1
	sar ax, 1
	sar ax, 1
	sub al, bh
	inc al
	cmp bh, bl
	jge L104F
	std
	add dx, ax
	add di, ax
	dec di
	add si, ax
	dec si
	jmp short L1051
L104F:
	sub dx, ax
L1051:
	mov bx, word ptr _g_3DB0
	mov ds, bx
	mov es, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	inc bx
L1060:
	mov cx, ax
	rep movsb
	add di, dx
	add si, dx
	dec bx
	jne L1060
	cld
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L1095
	test byte ptr _g_4365, 0FFh
	je L1089
	test byte ptr _g_4331, 0FFh
	je L1095
	call far ptr _f_1B73_04BB
	jmp short L1095
L1089:
	test byte ptr _g_4366, 0FFh
	jne L1095
	call far ptr _f_1B73_00D9
L1095:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
_o01_3126_0F83	endp

_o01_3126_109D	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L10DA
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L10DA
	cmp dx, word ptr _g_4342
	jl L10DA
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L10DA
	cmp dx, word ptr _g_4340
	jl L10DA
	call far ptr _f_1B73_0196
	jmp L110D
L10DA:
	mov ax, word ptr [bp+0Eh]
	mov dx, ax
	add dx, word ptr [bp+0Ah]
	sub dx, word ptr [bp+6]
	cmp ax, word ptr _g_4346
	jg L110D
	cmp dx, word ptr _g_4340
	jl L110D
	mov ax, word ptr [bp+10h]
	mov dx, ax
	add dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	cmp ax, word ptr _g_4344
	jg L110D
	cmp dx, word ptr _g_4342
	jl L110D
	call far ptr _f_1B73_0196
L110D:
	mov cx, word ptr [bp+10h]
	mov dx, word ptr _g_3DB6
	mov ax, word ptr [bp+8]
	cmp ax, cx
	jge L1125
	mov ax, word ptr [bp+0Ch]
	add cx, ax
	sub cx, word ptr [bp+8]
	neg dx
L1125:
	mov si, ax
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov di, cx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	sar ax, 1
	sar ax, 1
	sar ax, 1
	add si, ax
	mov bx, word ptr [bp+0Eh]
	sar bx, 1
	sar bx, 1
	sar bx, 1
	add di, bx
	mov bh, al
	mov ax, word ptr [bp+0Ah]
	sar ax, 1
	sar ax, 1
	sar ax, 1
	sub al, bh
	inc al
	cmp bh, bl
	jge L1169
	std
	add dx, ax
	add di, ax
	dec di
	add si, ax
	dec si
	jmp short L116B
L1169:
	sub dx, ax
L116B:
	mov bx, word ptr _g_3DB0
	mov ds, bx
	mov es, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	inc bx
	and dx, dx
	js L11CF
L117E:
	mov cx, ax
	push di
	push si
	rep movsb
	pop si
	pop di
	add di, 2000h
	jns L1190
	add di, 805Ah
L1190:
	add si, 2000h
	jns L119A
	add si, 805Ah
L119A:
	dec bx
	jne L117E
L119D:
	cld
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L11C7
	test byte ptr _g_4365, 0FFh
	je L11BB
	test byte ptr _g_4331, 0FFh
	je L11C7
	call far ptr _f_1B73_04BB
	jmp short L11C7
L11BB:
	test byte ptr _g_4366, 0FFh
	jne L11C7
	call far ptr _f_1B73_00D9
L11C7:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
L11CF:
	mov cx, ax
	push si
	push di
	rep movsb
	pop di
	pop si
	sub di, 2000h
	jns L11E1
	sub di, 805Ah
L11E1:
	sub si, 2000h
	jns L11EB
	sub si, 805Ah
L11EB:
	dec bx
	jne L11CF
	jmp L119D
_o01_3126_109D	endp

_o01_3126_11F0	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	inc byte ptr _g_3DD4
	test byte ptr _g_4333, 0FFh
	jne L122D
	mov ax, word ptr [bp+8]
	mov dx, word ptr [bp+0Ch]
	cmp ax, word ptr _g_4344
	jg L122D
	cmp dx, word ptr _g_4342
	jl L122D
	mov ax, word ptr [bp+6]
	mov dx, word ptr [bp+0Ah]
	cmp ax, word ptr _g_4346
	jg L122D
	cmp dx, word ptr _g_4340
	jl L122D
	call far ptr _f_1B73_0196
	jmp L1260
L122D:
	mov ax, word ptr [bp+0Eh]
	mov dx, ax
	add dx, word ptr [bp+0Ah]
	sub dx, word ptr [bp+6]
	cmp ax, word ptr _g_4346
	jg L1260
	cmp dx, word ptr _g_4340
	jl L1260
	mov ax, word ptr [bp+10h]
	mov dx, ax
	add dx, word ptr [bp+0Ch]
	sub dx, word ptr [bp+8]
	cmp ax, word ptr _g_4344
	jg L1260
	cmp dx, word ptr _g_4342
	jl L1260
	call far ptr _f_1B73_0196
L1260:
	mov cx, word ptr [bp+10h]
	mov dx, word ptr _g_3DB6
	mov ax, word ptr [bp+8]
	cmp ax, cx
	jge L1278
	mov ax, word ptr [bp+0Ch]
	add cx, ax
	sub cx, word ptr [bp+8]
	neg dx
L1278:
	mov si, ax
	add si, si
	mov si, word ptr [si+_g_3DFC]
	mov di, cx
	add di, di
	mov di, word ptr [di+_g_3DFC]
	mov ax, word ptr [bp+6]
	sar ax, 1
	sar ax, 1
	sar ax, 1
	add si, ax
	mov bx, word ptr [bp+0Eh]
	sar bx, 1
	sar bx, 1
	sar bx, 1
	add di, bx
	mov bh, al
	mov ax, word ptr [bp+0Ah]
	sar ax, 1
	sar ax, 1
	sar ax, 1
	sub al, bh
	inc al
	cmp bh, bl
	jge L12BC
	std
	add dx, ax
	add di, ax
	dec di
	add si, ax
	dec si
	jmp short L12BE
L12BC:
	sub dx, ax
L12BE:
	mov bx, word ptr _g_3DB0
	mov ds, bx
	mov es, bx
	mov bx, word ptr [bp+0Ch]
	sub bx, word ptr [bp+8]
	inc bx
	and dx, dx
	js L1322
L12D1:
	mov cx, ax
	push si
	push di
	rep movsb
	pop di
	pop si
	add di, 2000h
	jns L12E3
	add di, 8050h
L12E3:
	add si, 2000h
	jns L12ED
	add si, 8050h
L12ED:
	dec bx
	jne L12D1
L12F0:
	cld
	pop ds
	test byte ptr _g_4333, 0FFh
	jne L131A
	test byte ptr _g_4365, 0FFh
	je L130E
	test byte ptr _g_4331, 0FFh
	je L131A
	call far ptr _f_1B73_04BB
	jmp short L131A
L130E:
	test byte ptr _g_4366, 0FFh
	jne L131A
	call far ptr _f_1B73_00D9
L131A:
	dec byte ptr _g_3DD4
	pop di
	pop si
	pop bp
	retf
L1322:
	mov cx, ax
	push si
	push di
	rep movsb
	pop di
	pop si
	sub di, 2000h
	jns L1334
	sub di, 8050h
L1334:
	sub si, 2000h
	jns L133E
	sub si, 8050h
L133E:
	dec bx
	jne L1322
	jmp L12F0
_o01_3126_11F0	endp

_o01_3126_1343	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+0Eh]
	lds si, dword ptr [bp+0Ah]
	mov bx, word ptr [bp+12h]
	push bp
	lea bp, _g_3D20
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
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
	call far ptr _o01_3126_073C
	add sp, 0Ch
	pop di
	pop si
	pop bp
	retf
_o01_3126_1343	endp

_o01_3126_14B6	proc	far
	push bp
	mov bp, sp
	push si
	push di
	push ds
	les di, dword ptr [bp+0Ah]
	lds si, dword ptr [bp+6]
	mov bx, word ptr [bp+0Eh]
	push bp
	lea bp, _g_3D20
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	lodsw
	mov dx, word ptr es:[di]
	xor ax, dx
	and ax, word ptr es:[bx+di]
	xor ax, dx
	mov word ptr [bp], ax
	add bp, 2
	add di, 2
	pop bp
	pop ds
	pop di
	pop si
	pop bp
	retf
_o01_3126_14B6	endp

_o01_3126_1610	proc	far
	mov dx, 3BFh
	mov al, 1
	out dx, al
	mov al, 2
	lea si, _g_2184
	mov bx, 0
	mov cx, 4000h
	call near ptr _o01_3126_1658
	xor ax, ax
	mov es, ax
	mov byte ptr es:[449h], 6
	mov word ptr es:[44Ah], 5Ah
	retf
_o01_3126_1610	endp

_o01_3126_1637	proc	far
	mov al, 20h
	lea si, _g_2190
	mov bx, 720h
	mov cx, 7D0h
	call near ptr _o01_3126_1658
	xor ax, ax
	mov es, ax
	mov byte ptr es:[449h], 7
	mov word ptr es:[44Ah], 50h
	retf
_o01_3126_1637	endp

_o01_3126_1658	proc	far
	push ds
	push es
	push ax
	push bx
	push cx
	mov dx, 3B8h
	out dx, al
	mov dx, 3B4h
	mov cx, 0Ch
	xor ah, ah
L1669:
	mov al, ah
	out dx, al
	cld
	inc dx
	lodsb
	out dx, al
	inc ah
	dec dx
	loop L1669
	pop cx
	mov ax, 0B000h
	mov es, ax
	xor di, di
	pop ax
	rep stosw
	mov dx, 3B8h
	pop ax
	add al, 8
	out dx, al
	pop es
	pop ds
	retn
_o01_3126_1658	endp

S01A_TEXT	ends
	end
