; EMS (LIM 4.0) interface: INT 67h wrappers, EMM detection and page-frame setup.
; Root module, code frame 195A, linear 195AC-19862 (LINK fill 00 at 19863).
;
; Genuine assembly.  MSC 6.00(AX) cannot produce this object: most procedures are
; frameless far procs that pass INT 67h results in registers; framed ones end with
; pop bp/retf and no mov sp,bp and save DS (push ds; push si) around lds; the device
; name "EMMXXXX0" is stored in the code segment and opened through DS=CS; the error
; exit is an int 3 followed by a far jump to Punt with an unreachable retf behind it.

DGROUP		group	_DATA

_DATA		segment word public 'DATA'
ems_error	db	'EMS Error', 0
		public	_fd_55B3_360C
_fd_55B3_360C	db	0		; EMM version (INT 67h/46h)
ems_active	db	0		; set once the page frame is set up
		public	_fd_55B3_360E
_fd_55B3_360E	dd	0		; page frame (far pointer, offset 0)
		public	_fd_55B3_3612
_fd_55B3_3612	dw	0		; unallocated pages (INT 67h/42h)
		public	_fd_55B3_3614
_fd_55B3_3614	dw	0		; total pages
ems_mappable	dw	0		; mappable physical pages (INT 67h/58h)
ems_altmap	dw	0		; alternate map register save area size (INT 67h/5B02h)
ems_off_opt	db	'/E-', 0	; command-line switch that disables EMS
_DATA		ends

_DATA		segment
		extrn	__psp:word
_DATA		ends

		extrn	_Punt:far

EMS_TEXT	segment word public 'CODE'
		assume	cs:EMS_TEXT, ds:DGROUP

	public	_f_195A_000C
	public	_f_195A_0018
	public	_f_195A_001D
	public	_f_195A_0035
	public	_f_195A_004B
	public	_f_195A_0062
	public	_f_195A_007D
	public	_f_195A_0092
	public	_f_195A_00AC
	public	_f_195A_00C8
	public	_f_195A_00E9
	public	_f_195A_00F8
	public	_f_195A_010D
	public	_f_195A_0122
	public	_f_195A_0144
	public	_f_195A_0166
	public	_f_195A_0182
	public	_f_195A_019C
	public	_f_195A_01AF
	public	_f_195A_01CB
	public	_f_195A_01DF
	public	_f_195A_01F2
	public	_f_195A_0206
	public	_f_195A_0210
	public	_f_195A_021A
	public	_f_195A_0222
	public	_f_195A_023A
	public	_f_195A_0260
	public	_f_195A_02B7

_f_195A_000C	proc	far
	mov ah, 46h
	int 67h
	and ah, ah
	jne L0017
	mov _fd_55B3_360C, al
L0017:
	retf
_f_195A_000C	endp

_f_195A_0018	proc	far
	mov ah, 40h
	int 67h
	retf
_f_195A_0018	endp

_f_195A_001D	proc	far
	mov ah, 41h
	int 67h
	and ah, ah
	je L002A
	call far ptr _f_195A_02B7
L002A:
	mov word ptr _fd_55B3_360E, 0
	mov word ptr _fd_55B3_360E+2, bx
	retf
_f_195A_001D	endp

_f_195A_0035	proc	far
	mov ah, 42h
	int 67h
	and ah, ah
	je L0042
	call far ptr _f_195A_02B7
L0042:
	mov _fd_55B3_3612, bx
	mov _fd_55B3_3614, dx
	retf
_f_195A_0035	endp

_f_195A_004B	proc	far
	push bp
	mov bp, sp
	mov ah, 43h
	mov bx, word ptr [bp+6]
	int 67h
	and ah, ah
	je L005E
	call far ptr _f_195A_02B7
L005E:
	mov ax, dx
	pop bp
	retf
_f_195A_004B	endp

_f_195A_0062	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov ah, 44h
	mov al, byte ptr [bp+0Ah]
	mov bx, word ptr [bp+8]
	int 67h
	and ah, ah
	je L007B
	call far ptr _f_195A_02B7
L007B:
	pop bp
	retf
_f_195A_0062	endp

_f_195A_007D	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov ah, 45h
	int 67h
	and ah, ah
	je L0090
	call far ptr _f_195A_02B7
L0090:
	pop bp
	retf
_f_195A_007D	endp

_f_195A_0092	proc	far
	push bp
	mov bp, sp
	push di
	mov ax, 4E00h
	les di, dword ptr [bp+6]
	int 67h
	and ah, ah
	je L00A7
	call far ptr _f_195A_02B7
L00A7:
	xor al, al
	pop di
	pop bp
	retf
_f_195A_0092	endp

_f_195A_00AC	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	mov ax, 4E01h
	lds si, dword ptr [bp+6]
	int 67h
	and ah, ah
	je L00C2
	call far ptr _f_195A_02B7
L00C2:
	xor al, al
	pop si
	pop ds
	pop bp
	retf
_f_195A_00AC	endp

_f_195A_00C8	proc	far
	push bp
	mov bp, sp
	push di
	push si
	push ds
	mov ax, 4E02h
	les di, dword ptr [bp+6]
	lds si, dword ptr [bp+0Ah]
	int 67h
	and ah, ah
	je L00E2
	call far ptr _f_195A_02B7
L00E2:
	xor al, al
	pop ds
	pop si
	pop di
	pop bp
	retf
_f_195A_00C8	endp

_f_195A_00E9	proc	far
	mov ax, 4E03h
	int 67h
	and ah, ah
	je L00F7
	call far ptr _f_195A_02B7
L00F7:
	retf
_f_195A_00E9	endp

_f_195A_00F8	proc	far
	push bp
	mov bp, sp
	mov ah, 47h
	mov dx, word ptr [bp+6]
	int 67h
	and ah, ah
	je L010B
	call far ptr _f_195A_02B7
L010B:
	pop bp
	retf
_f_195A_00F8	endp

_f_195A_010D	proc	far
	push bp
	mov bp, sp
	mov ah, 48h
	mov dx, word ptr [bp+6]
	int 67h
	and ah, ah
	je L0120
	call far ptr _f_195A_02B7
L0120:
	pop bp
	retf
_f_195A_010D	endp

_f_195A_0122	proc	far
	push bp
	mov bp, sp
	push si
	push ds
	mov dx, word ptr [bp+6]
	mov cx, word ptr [bp+8]
	mov ax, 5000h
	lds si, dword ptr [bp+0Ah]
	int 67h
	and ah, ah
	je L013E
	call far ptr _f_195A_02B7
L013E:
	xor al, al
	pop ds
	pop si
	pop bp
	retf
_f_195A_0122	endp

_f_195A_0144	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	mov dx, word ptr [bp+6]
	mov cx, word ptr [bp+8]
	lds si, dword ptr [bp+0Ah]
	mov ax, 5001h
	int 67h
	and ah, ah
	je L0160
	call far ptr _f_195A_02B7
L0160:
	xor al, al
	pop si
	pop ds
	pop bp
	retf
_f_195A_0144	endp

_f_195A_0166	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	lds si, dword ptr [bp+6]
	mov ax, 5700h
	int 67h
	and ah, ah
	je L017C
	call far ptr _f_195A_02B7
L017C:
	xor al, al
	pop si
	pop ds
	pop bp
	retf
_f_195A_0166	endp

_f_195A_0182	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov bx, word ptr [bp+8]
	mov ah, 51h
	int 67h
	and ah, ah
	je L0198
	call far ptr _f_195A_02B7
L0198:
	xor al, al
	pop bp
	retf
_f_195A_0182	endp

_f_195A_019C	proc	far
	mov ax, 5801h
	int 67h
	and ah, ah
	je L01AA
	call far ptr _f_195A_02B7
L01AA:
	mov ems_mappable, cx
	retf
_f_195A_019C	endp

_f_195A_01AF	proc	far
	push bp
	mov bp, sp
	push di
	les di, dword ptr [bp+6]
	mov ax, 5800h
	int 67h
	and ah, ah
	je L01C4
	call far ptr _f_195A_02B7
L01C4:
	mov ems_mappable, cx
	pop di
	pop bp
	retf
_f_195A_01AF	endp

_f_195A_01CB	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	mov dx, word ptr [bp+6]
	lds si, dword ptr [bp+8]
	mov ax, 5301h
	int 67h
	pop si
	pop ds
	pop bp
	retf
_f_195A_01CB	endp

_f_195A_01DF	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	lds si, dword ptr [bp+6]
	mov ax, 5401h
	int 67h
	mov al, dl
	pop si
	pop ds
	pop bp
	retf
_f_195A_01DF	endp

_f_195A_01F2	proc	far
	push bp
	mov bp, sp
	push di
	mov ax, 5B01h
	mov bl, byte ptr [bp+6]
	les di, dword ptr [bp+8]
	int 67h
	xor al, al
	pop di
	pop bp
	retf
_f_195A_01F2	endp

_f_195A_0206	proc	far
	push di
	mov ax, 5B00h
	int 67h
	mov al, bl
	pop di
	retf
_f_195A_0206	endp

_f_195A_0210	proc	far
	mov ax, 5B02h
	int 67h
	mov ems_altmap, dx
	retf
_f_195A_0210	endp

_f_195A_021A	proc	far
	mov ax, 5B03h
	int 67h
	mov al, bl
	retf
_f_195A_021A	endp

_f_195A_0222	proc	far
	push bp
	mov bp, sp
	mov bl, byte ptr [bp+6]
	mov ax, 5B04h
	int 67h
	xor al, al
	pop bp
	retf
_f_195A_0222	endp

emm_name	db	'EMMXXXX0', 0

_f_195A_023A	proc	far
	push ds
	push cs
	pop ds
	assume	ds:EMS_TEXT
	lea dx, emm_name
	assume	ds:DGROUP
	mov ax, 3D00h
	int 21h
	pop ds
	jb L025D
	mov bx, ax
	mov ah, 3Eh
	int 21h
	call far ptr _f_195A_0018
	test ah, 0FFh
	jne L025D
	mov ax, 1
	retf
L025D:
	xor ax, ax
	retf
_f_195A_023A	endp

_f_195A_0260	proc	far
	push si
	test ems_active, 0FFh
	jne L02B5
	mov es, __psp
	mov si, 80h
	xor ax, ax
	mov dl, byte ptr es:[si]
	inc si
	mov cx, 80h
	xor ax, ax
L027A:
	xor bx, bx
L027C:
	mov dl, byte ptr es:[si]
	inc si
	cmp dl, byte ptr ems_off_opt[bx]
	je L028A
	loop L027A
	jmp short L0294
L028A:
	inc bx
	cmp byte ptr ems_off_opt[bx], 0
	je L02B5
	loop L027C
L0294:
	call far ptr _f_195A_023A
	test ax, 0FFh
	je L02B5
	call far ptr _f_195A_000C
	and ah, ah
	jne L02B5
	cmp al, 32h
	jl L02B5
	call far ptr _f_195A_001D
	mov ems_active, 1
L02B5:
	pop si
	retf
_f_195A_0260	endp

_f_195A_02B7	proc	far
	int	3
	push ds
	mov ax, offset DGROUP:ems_error
	push ax
	jmp far ptr _Punt
	retf				; unreachable
_f_195A_02B7	endp

EMS_TEXT	ends
	end
