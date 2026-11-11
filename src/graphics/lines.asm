; Root module 16B5: line drawing (Bresenham) with per-mode near plot procedures.
; Root code frame 16B5, linear 16B58-171C2.
; Genuine assembly: 'add bp,6' argument frames, near plot/init procedures dispatched through DGROUP
; tables of near code offsets (call word ptr [bx+table]), a shared clip subroutine returning in the
; carry flag, pushf/cld/popf around the indirect call, push es; push ds; push si; push di saves
; (MSC saves DI first, rule ASM-2) and pop bp without mov sp,bp (rule ASM-1).  The dispatch
; tables at DGROUP 1E00/1F98 hold near offsets of this segment (defined below with the module's _DATA).

_DATA	segment word public 'DATA'
; 16B5 private data (DGROUP:1DE8-1F9D): line state (end points, deltas, error terms, the far
; destination at 1DF0/1DF2, step bytes), the per-mode init dispatch table (1E00: near offsets of
; this segment), a 200-word row-offset table filled at run time (1E06), the current plot
; procedure (1F96) and the per-mode plot dispatch table (1F98).
_g_1DE8	dw	0
_g_1DEA	dw	0
_g_1DEC	dw	0
_g_1DEE	dw	0
_g_1DF0	dw	0
_g_1DF2	dw	0
_g_1DF4	dw	0
_g_1DF6	dw	0
_g_1DF8	db	0
_g_1DF9	db	0
_g_1DFA	dw	0
_g_1DFC	dw	0
_g_1DFE	dw	0
_g_1E00	dw	_f_16B5_007F, _f_16B5_00AB, _f_16B5_00A5
_g_1E06	dw	200 dup (0)
_g_1F96	dw	0
_g_1F98	dw	_f_16B5_00B1, _f_16B5_03B5, _f_16B5_01D4
_DATA	ends
DGROUP	group	_DATA

LINE_TEXT	segment word public 'CODE'
	assume	cs:LINE_TEXT, ds:DGROUP

	public	_f_16B5_0008
	public	_f_16B5_0033
	public	_f_16B5_007F
	public	_f_16B5_00A5
	public	_f_16B5_00AB
	public	_f_16B5_00B1
	public	_f_16B5_01D4
	public	_f_16B5_03B5
	public	_f_16B5_04D8

_f_16B5_0008	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	mov di, word ptr [bp]
	mov si, word ptr [bp+2]
	mov bx, word ptr [bp+4]
	mov dx, word ptr [bp+6]
	mov ax, word ptr [bp+8]
	pushf
	cld
	call word ptr _g_1F96
	popf
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_16B5_0008	endp

_f_16B5_0033	proc	far
	push bp
	mov bp, sp
	add bp, 6
	push es
	push ds
	push si
	push di
	mov ax, DGROUP
	mov ds, ax
	les bx, dword ptr [bp]
	mov ax, word ptr es:[bx]
	mov word ptr _g_1DE8, ax
	dec ax
	mov word ptr _g_1DEC, ax
	add bx, 2
	mov ax, word ptr es:[bx]
	mov word ptr _g_1DEA, ax
	dec ax
	mov word ptr _g_1DEE, ax
	add bx, 2
	mov word ptr _g_1DF2, bx
	mov word ptr _g_1DF0, es
	mov bx, word ptr [bp+4]
	shl bx, 1
	push bx
	call word ptr [bx+_g_1E00]
	pop bx
	mov ax, word ptr [bx+_g_1F98]
	mov word ptr _g_1F96, ax
	pop di
	pop si
	pop ds
	pop es
	pop bp
	retf
_f_16B5_0033	endp

_f_16B5_007F	proc	near
	mov bx, word ptr _g_1DE8
	shr bx, 1
	shr bx, 1
L0087:
	shr bx, 1
	mov di, offset DGROUP:_g_1E06
	mov ax, ds
	mov es, ax
	mov ax, word ptr _g_1DF2
	mov cx, word ptr _g_1DEA
L0097:
	stosw
	add ax, bx
	loop L0097
	shr bx, 1
	shr bx, 1
	mov word ptr _g_1DFE, bx
	retn
_f_16B5_007F	endp

_f_16B5_00A5	proc	near
	mov bx, word ptr _g_1DE8
	jmp L0087
_f_16B5_00A5	endp

_f_16B5_00AB	proc	near
	mov bx, word ptr _g_1DE8
	jmp L0087
_f_16B5_00AB	endp

_f_16B5_00B1	proc	near
	call near ptr _f_16B5_04D8
	jae L00B7
	retn
L00B7:
	mov es, word ptr _g_1DF0
	mov word ptr _g_1DFC, ax
	xor ax, ax
	mov cx, dx
	sub cx, si
	jns L00C9
	inc ax
	neg cx
L00C9:
	mov word ptr _g_1DF6, cx
	mov byte ptr _g_1DF9, al
	xor ax, ax
	mov cx, bx
	sub cx, di
	jns L00DB
	inc ax
	neg cx
L00DB:
	mov word ptr _g_1DF4, cx
	mov byte ptr _g_1DF8, al
	xor ax, ax
	cmp cx, word ptr _g_1DF6
	je L00EE
	jbe L0165
	jmp short L00F3
L00EE:
	inc word ptr _g_1DF4
	dec ax
L00F3:
	mov bp, 1
	cmp byte ptr _g_1DF9, 0
	je L00FF
	neg bp
L00FF:
	cmp byte ptr _g_1DF8, 0
	je L010C
	xchg di, bx
	xchg si, dx
	neg bp
L010C:
	xor ax, ax
	mov dx, word ptr _g_1DF6
	mov cx, word ptr _g_1DF4
	div cx
	mov dx, ax
	mov cx, word ptr _g_1DF4
	or cx, cx
	je L0164
	mov ax, word ptr _g_1DFC
	and ax, 1
	mov bx, 0FFFFh
L012B:
	push di
	push bx
	push cx
	mov bx, si
	shl bx, 1
	mov bx, word ptr [bx+_g_1E06]
	mov cx, di
	shr di, 1
	shr di, 1
	shr di, 1
	and cx, 7
	xor cx, 7
	add bx, di
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	pop cx
	pop bx
	pop di
	inc di
	add bx, dx
	jb L0160
	loop L012B
	retn
L0160:
	add si, bp
	loop L012B
L0164:
	retn
L0165:
	mov bp, 1
	cmp byte ptr _g_1DF8, 0
	je L0171
	neg bp
L0171:
	cmp byte ptr _g_1DF9, 0
	je L017E
	xchg di, bx
	xchg si, dx
	neg bp
L017E:
	xor ax, ax
	mov dx, word ptr _g_1DF4
	mov cx, word ptr _g_1DF6
	div cx
	mov dx, ax
	mov cx, word ptr _g_1DF6
	inc cx
	mov ax, word ptr _g_1DFC
	and ax, 1
	mov bx, 0FFFFh
L019A:
	push di
	push bx
	push cx
	mov bx, si
	shl bx, 1
	mov bx, word ptr [bx+_g_1E06]
	mov cx, di
	shr di, 1
	shr di, 1
	shr di, 1
	and cx, 7
	xor cx, 7
	add bx, di
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	pop cx
	pop bx
	pop di
	inc si
	add bx, dx
	jb L01CF
	loop L019A
	retn
L01CF:
	add di, bp
	loop L019A
	retn
_f_16B5_00B1	endp

_f_16B5_01D4	proc	near
	call near ptr _f_16B5_04D8
	jae L01DA
	retn
L01DA:
	mov es, word ptr _g_1DF0
	mov word ptr _g_1DFC, ax
	xor ax, ax
	mov cx, dx
	sub cx, si
	jns L01EC
	inc ax
	neg cx
L01EC:
	mov word ptr _g_1DF6, cx
	mov byte ptr _g_1DF9, al
	xor ax, ax
	mov cx, bx
	sub cx, di
	jns L01FE
	inc ax
	neg cx
L01FE:
	mov word ptr _g_1DF4, cx
	mov byte ptr _g_1DF8, al
	xor ax, ax
	cmp cx, word ptr _g_1DF6
	je L0212
	ja L0217
	jmp near ptr L02E8
L0212:
	inc word ptr _g_1DF4
	dec ax
L0217:
	mov bp, 1
	cmp byte ptr _g_1DF9, 0
	je L0223
	neg bp
L0223:
	cmp byte ptr _g_1DF8, 0
	je L0230
	xchg di, bx
	xchg si, dx
	neg bp
L0230:
	xor ax, ax
	mov dx, word ptr _g_1DF6
	mov cx, word ptr _g_1DF4
	div cx
	mov dx, ax
	mov cx, word ptr _g_1DF4
	mov ax, word ptr _g_1DFC
	mov bx, 0FFFFh
	or cx, cx
	jne L024D
	retn
L024D:
	push di
	push bx
	push cx
	mov cx, di
	and ax, 0Fh
	shr di, 1
	shr di, 1
	shr di, 1
	and cx, 7
	xor cx, 7
	mov bx, si
	shl bx, 1
	mov bx, word ptr [bx+_g_1E06]
	add bx, di
	mov ah, al
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	and al, 1
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	add bx, word ptr _g_1DFE
	mov al, ah
	shr al, 1
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	and al, 1
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	add bx, word ptr _g_1DFE
	mov al, ah
	shr al, 1
	shr al, 1
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	and al, 1
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	add bx, word ptr _g_1DFE
	mov al, ah
	shr al, 1
	shr al, 1
	shr al, 1
	and al, 1
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	mov al, ah
	pop cx
	pop bx
	pop di
	inc di
	add bx, dx
	jb L02DF
	dec cx
	je L02E7
	jmp L024D
L02DF:
	add si, bp
	dec cx
	je L02E7
	jmp L024D
L02E7:
	retn
L02E8:
	mov bp, 1
	cmp byte ptr _g_1DF8, 0
	je L02F4
	neg bp
L02F4:
	cmp byte ptr _g_1DF9, 0
	je L0301
	xchg di, bx
	xchg si, dx
	neg bp
L0301:
	xor ax, ax
	mov dx, word ptr _g_1DF4
	mov cx, word ptr _g_1DF6
	div cx
	mov dx, ax
	mov cx, word ptr _g_1DF6
	inc cx
	mov ax, word ptr _g_1DFC
	mov bx, 0FFFFh
L031A:
	push di
	push bx
	push cx
	mov cx, di
	and ax, 0Fh
	shr di, 1
	shr di, 1
	shr di, 1
	and cx, 7
	xor cx, 7
	mov bx, si
	shl bx, 1
	mov bx, word ptr [bx+_g_1E06]
	add bx, di
	mov ah, al
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	and al, 1
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	add bx, word ptr _g_1DFE
	mov al, ah
	shr al, 1
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	and al, 1
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	add bx, word ptr _g_1DFE
	mov al, ah
	shr al, 1
	shr al, 1
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	and al, 1
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	add bx, word ptr _g_1DFE
	mov al, ah
	shr al, 1
	shr al, 1
	shr al, 1
	and al, 1
	mov ch, byte ptr es:[bx]
	ror ch, cl
	and ch, 0FEh
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	mov al, ah
	pop cx
	pop bx
	pop di
	inc si
	add bx, dx
	jb L03AD
	dec cx
	je L03AC
	jmp L031A
L03AC:
	retn
L03AD:
	add di, bp
	dec cx
	je L03AC
	jmp L031A
_f_16B5_01D4	endp

_f_16B5_03B5	proc	near
	call near ptr _f_16B5_04D8
	jae L03BB
	retn
L03BB:
	mov es, word ptr _g_1DF0
	mov word ptr _g_1DFC, ax
	xor ax, ax
	mov cx, dx
	sub cx, si
	jns L03CD
	inc ax
	neg cx
L03CD:
	mov word ptr _g_1DF6, cx
	mov byte ptr _g_1DF9, al
	xor ax, ax
	mov cx, bx
	sub cx, di
	jns L03DF
	inc ax
	neg cx
L03DF:
	mov word ptr _g_1DF4, cx
	mov byte ptr _g_1DF8, al
	xor ax, ax
	cmp cx, word ptr _g_1DF6
	je L03F2
	jbe L0469
	jmp short L03F7
L03F2:
	inc word ptr _g_1DF4
	dec ax
L03F7:
	mov bp, 1
	cmp byte ptr _g_1DF9, 0
	je L0403
	neg bp
L0403:
	cmp byte ptr _g_1DF8, 0
	je L0410
	xchg di, bx
	xchg si, dx
	neg bp
L0410:
	xor ax, ax
	mov dx, word ptr _g_1DF6
	mov cx, word ptr _g_1DF4
	div cx
	mov dx, ax
	mov cx, word ptr _g_1DF4
	or cx, cx
	je L0468
	mov ax, word ptr _g_1DFC
	mov bx, 0FFFFh
	and ax, 0Fh
L042F:
	push di
	push bx
	push cx
	mov bx, si
	shl bx, 1
	mov bx, word ptr [bx+_g_1E06]
	mov cx, di
	shr di, 1
	and cx, 1
	xor cx, 1
	add bx, di
	mov ch, byte ptr es:[bx]
	shl cl, 1
	shl cl, 1
	ror ch, cl
	and ch, 0F0h
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	pop cx
	pop bx
	pop di
	inc di
	add bx, dx
	jb L0464
	loop L042F
	retn
L0464:
	add si, bp
	loop L042F
L0468:
	retn
L0469:
	mov bp, 1
	cmp byte ptr _g_1DF8, 0
	je L0475
	neg bp
L0475:
	cmp byte ptr _g_1DF9, 0
	je L0482
	xchg di, bx
	xchg si, dx
	neg bp
L0482:
	xor ax, ax
	mov dx, word ptr _g_1DF4
	mov cx, word ptr _g_1DF6
	div cx
	mov dx, ax
	mov cx, word ptr _g_1DF6
	inc cx
	mov ax, word ptr _g_1DFC
	and ax, 0Fh
	mov bx, 0FFFFh
L049E:
	push di
	push bx
	push cx
	mov bx, si
	shl bx, 1
	mov bx, word ptr [bx+_g_1E06]
	mov cx, di
	shr di, 1
	and cx, 1
	xor cx, 1
	add bx, di
	mov ch, byte ptr es:[bx]
	shl cl, 1
	shl cl, 1
	ror ch, cl
	and ch, 0F0h
	or ch, al
	rol ch, cl
	mov byte ptr es:[bx], ch
	pop cx
	pop bx
	pop di
	inc si
	add bx, dx
	jb L04D3
	loop L049E
	retn
L04D3:
	add di, bp
	loop L049E
	retn
_f_16B5_03B5	endp

; clip the segment (SI,DI)-(x2,y2) against the bitmap (Cohen-Sutherland outcodes); CF = rejected
_f_16B5_04D8	proc	near
	push ax
	mov word ptr _g_1DFA, 0
L04DF:
	xor al, al
	cmp si, 0
	jl L04F9
	cmp si, word ptr _g_1DEE
	jg L0508
	cmp di, 0
	jl L0517
	cmp di, word ptr _g_1DEC
	jg L051B
	jmp short L051D
L04F9:
	or al, 8
	cmp di, 0
	jl L0517
	cmp di, word ptr _g_1DEC
	jg L051B
	jmp short L051D
L0508:
	or al, 4
	cmp di, 0
	jl L0517
	cmp di, word ptr _g_1DEC
	jg L051B
	jmp short L051D
L0517:
	or al, 1
	jmp short L051D
L051B:
	or al, 2
L051D:
	mov ah, al
	xchg si, dx
	xchg di, bx
	xor al, al
	cmp si, 0
	jl L053D
	cmp si, word ptr _g_1DEE
	jg L054C
	cmp di, 0
	jl L055B
	cmp di, word ptr _g_1DEC
	jg L055F
	jmp short L0561
L053D:
	or al, 8
	cmp di, 0
	jl L055B
	cmp di, word ptr _g_1DEC
	jg L055F
	jmp short L0561
L054C:
	or al, 4
	cmp di, 0
	jl L055B
	cmp di, word ptr _g_1DEC
	jg L055F
	jmp short L0561
L055B:
	or al, 1
	jmp short L0561
L055F:
	or al, 2
L0561:
	xchg si, dx
	xchg di, bx
	test ah, al
	jne L05B1
	or ax, ax
	je L05A3
	cmp di, bx
	jl L057C
	xchg si, dx
	xchg di, bx
	xchg ah, al
	xor word ptr _g_1DFA, 1
L057C:
	test ah, 1
	jne L05B4
	test al, 2
	jne L05E3
	cmp si, dx
	jl L0594
	xchg si, dx
	xchg di, bx
	xchg ah, al
	xor word ptr _g_1DFA, 1
L0594:
	test ah, 8
	jne L0613
	test al, 4
	je L05A0
	jmp near ptr L0642
L05A0:
	jmp L04DF
L05A3:
	cmp word ptr _g_1DFA, 0
	je L05AE
	xchg si, dx
	xchg di, bx
L05AE:
	clc
	pop ax
	retn
L05B1:
	stc
	pop ax
	retn
L05B4:
	push dx
	push bx
	push di
	push si
L05B8:
	mov ax, si
	mov cx, di
	add ax, dx
	add cx, bx
	sar ax, 1
	sar cx, 1
	cmp cx, 0
	je L05D8
	jg L05D2
	mov si, ax
	mov di, cx
	inc di
	jmp L05B8
L05D2:
	mov bx, cx
	mov dx, ax
	jmp L05B8
L05D8:
	pop si
	pop di
	pop bx
	pop dx
	mov si, ax
	mov di, cx
	jmp L04DF
L05E3:
	push dx
	push bx
	push di
	push si
L05E7:
	mov ax, si
	mov cx, di
	add ax, dx
	add cx, bx
	sar ax, 1
	sar cx, 1
	cmp cx, word ptr _g_1DEC
	je L0608
	jg L0602
	mov si, ax
	mov di, cx
	inc di
	jmp L05E7
L0602:
	mov bx, cx
	mov dx, ax
	jmp L05E7
L0608:
	pop si
	pop di
	pop bx
	pop dx
	mov dx, ax
	mov bx, cx
	jmp L04DF
L0613:
	push dx
	push bx
	push di
	push si
L0617:
	mov ax, si
	mov cx, di
	add ax, dx
	add cx, bx
	sar ax, 1
	sar cx, 1
	cmp ax, 0
	je L0637
	jg L0631
	mov si, ax
	inc si
	mov di, cx
	jmp L0617
L0631:
	mov bx, cx
	mov dx, ax
	jmp L0617
L0637:
	pop si
	pop di
	pop bx
	pop dx
	mov si, ax
	mov di, cx
	jmp L04DF
L0642:
	push dx
	push bx
	push di
	push si
L0646:
	mov ax, si
	mov cx, di
	add ax, dx
	add cx, bx
	sar ax, 1
	sar cx, 1
	cmp ax, word ptr _g_1DEE
	je L0667
	jg L0661
	mov si, ax
	inc si
	mov di, cx
	jmp L0646
L0661:
	mov bx, cx
	mov dx, ax
	jmp L0646
L0667:
	pop si
	pop di
	pop bx
	pop dx
	mov dx, ax
	mov bx, cx
	jmp L04DF
_f_16B5_04D8	endp

LINE_TEXT	ends
	end
