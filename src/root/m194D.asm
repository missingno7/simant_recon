; Root module 194D: paragraph-stepping block copy, Tandy video memory probe, 386 dword checksum.
; Root code frame 194D, linear 194D6-19591.
; Genuine assembly: 'and ax,ax'/'and dx,dx' tests (MSC emits or r,r), rep movsw with manual
; segment stepping, rep stosw/repe scasw video probe, 386 instructions (xor edx,edx; lodsd;
; shr edx,16) and push ds; push di; push si saves (MSC saves DI first, rule ASM-2).

_DATA	segment word public 'DATA'
	extrn	_g_91A0:byte
	extrn	_g_91A2:byte
_DATA	ends
DGROUP	group	_DATA

	extrn	_o21_39C7_0000:far
	extrn	_o21_39C7_016D:far

HUGE_TEXT	segment word public 'CODE'
	assume	cs:HUGE_TEXT, ds:DGROUP

	public	_f_194D_0006
	public	_f_194D_003F
	public	_f_194D_008F

_f_194D_0006	proc	far
	push bp
	mov bp, sp
	push ds
	push di
	push si
	les di, dword ptr [bp+6]
	lds si, dword ptr [bp+0Ah]
	mov dx, word ptr [bp+0Eh]
L0015:
	mov cx, 1000h
	cmp dx, cx
	jg L001E
	mov cx, dx
L001E:
	mov ax, cx
	shl cx, 1
	shl cx, 1
	shl cx, 1
	sub dx, ax
	rep movsw
	mov bx, es
	add bx, ax
	mov es, bx
	mov bx, ds
	add bx, ax
	mov ds, bx
	and dx, dx
	jne L0015
	pop si
	pop di
	pop ds
	pop bp
	retf
_f_194D_0006	endp

_f_194D_003F	proc	far
	push bp
	mov bp, sp
	sub sp, 2
	push di
	call far ptr _o21_39C7_0000
	cmp al, 2
	jne L0088
	call far ptr _o21_39C7_016D
	and ax, ax
	je L0088
	mov ax, word ptr _g_91A2
	add ax, word ptr _g_91A0
	sub ax, 400h
	mov word ptr [bp-2], ax
	mov es, ax
	xor di, di
	mov ax, 0AA55h
	mov cx, 800h
	rep stosw
	mov ax, 9
	int 10h
	mov es, word ptr [bp-2]
	xor di, di
	mov ax, 0AA55h
	mov cx, 800h
	repe scasw
	mov ax, 1
	jne L008A
L0088:
	xor ax, ax
L008A:
	pop di
	mov sp, bp
	pop bp
	retf
_f_194D_003F	endp

; 386 code inside the 16-bit segment (the segment was opened before .386, so it stays USE16)
	.386
_f_194D_008F	proc	far
	push bp
	mov bp, sp
	push si
	push ds
	lds si, dword ptr [bp+6]
	mov ax, ds
	sub ax, 3
	mov ds, ax
	mov cx, word ptr [si+2]
	add ax, 3
	mov ds, ax
	shr cx, 2
	xor edx, edx
	xor ah, ah
L00AE:
	lodsd
	add edx, eax
	loop L00AE
	mov ax, dx
	shr edx, 10h
	add ax, dx
	pop ds
	pop si
	pop bp
	retf
_f_194D_008F	endp

HUGE_TEXT	ends
	end
