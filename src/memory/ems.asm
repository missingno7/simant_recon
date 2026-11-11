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

	public	_ems_query_version
	public	_ems_query_status
	public	_ems_query_page_frame
	public	_ems_query_page_counts
	public	_ems_allocate_pages
	public	_ems_map_page
	public	_ems_free_handle
	public	_ems_get_page_map
	public	_ems_set_page_map
	public	_ems_exchange_page_map
	public	_ems_query_page_map_size
	public	_ems_save_handle_map
	public	_ems_restore_handle_map
	public	_ems_map_multiple_pages
	public	_ems_map_multiple_segments
	public	_ems_move_region
	public	_ems_resize_handle
	public	_ems_query_mappable_count
	public	_ems_get_mappable_pages
	public	_ems_set_handle_name
	public	_ems_find_named_handle
	public	_ems_set_alternate_map
	public	_ems_get_alternate_map
	public	_ems_query_alternate_map_size
	public	_ems_allocate_alternate_map
	public	_ems_free_alternate_map
	public	_ems_detect_manager
	public	_ems_initialize
	public	_ems_fatal_error

_ems_query_version	proc	far
	mov ah, 46h
	int 67h
	and ah, ah
	jne L0017
	mov _fd_55B3_360C, al
L0017:
	retf
_ems_query_version	endp

_ems_query_status	proc	far
	mov ah, 40h
	int 67h
	retf
_ems_query_status	endp

_ems_query_page_frame	proc	far
	mov ah, 41h
	int 67h
	and ah, ah
	je L002A
	call far ptr _ems_fatal_error
L002A:
	mov word ptr _fd_55B3_360E, 0
	mov word ptr _fd_55B3_360E+2, bx
	retf
_ems_query_page_frame	endp

_ems_query_page_counts	proc	far
	mov ah, 42h
	int 67h
	and ah, ah
	je L0042
	call far ptr _ems_fatal_error
L0042:
	mov _fd_55B3_3612, bx
	mov _fd_55B3_3614, dx
	retf
_ems_query_page_counts	endp

_ems_allocate_pages	proc	far
	push bp
	mov bp, sp
	mov ah, 43h
	mov bx, word ptr [bp+6]
	int 67h
	and ah, ah
	je L005E
	call far ptr _ems_fatal_error
L005E:
	mov ax, dx
	pop bp
	retf
_ems_allocate_pages	endp

_ems_map_page	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov ah, 44h
	mov al, byte ptr [bp+0Ah]
	mov bx, word ptr [bp+8]
	int 67h
	and ah, ah
	je L007B
	call far ptr _ems_fatal_error
L007B:
	pop bp
	retf
_ems_map_page	endp

_ems_free_handle	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov ah, 45h
	int 67h
	and ah, ah
	je L0090
	call far ptr _ems_fatal_error
L0090:
	pop bp
	retf
_ems_free_handle	endp

_ems_get_page_map	proc	far
	push bp
	mov bp, sp
	push di
	mov ax, 4E00h
	les di, dword ptr [bp+6]
	int 67h
	and ah, ah
	je L00A7
	call far ptr _ems_fatal_error
L00A7:
	xor al, al
	pop di
	pop bp
	retf
_ems_get_page_map	endp

_ems_set_page_map	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	mov ax, 4E01h
	lds si, dword ptr [bp+6]
	int 67h
	and ah, ah
	je L00C2
	call far ptr _ems_fatal_error
L00C2:
	xor al, al
	pop si
	pop ds
	pop bp
	retf
_ems_set_page_map	endp

_ems_exchange_page_map	proc	far
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
	call far ptr _ems_fatal_error
L00E2:
	xor al, al
	pop ds
	pop si
	pop di
	pop bp
	retf
_ems_exchange_page_map	endp

_ems_query_page_map_size	proc	far
	mov ax, 4E03h
	int 67h
	and ah, ah
	je L00F7
	call far ptr _ems_fatal_error
L00F7:
	retf
_ems_query_page_map_size	endp

_ems_save_handle_map	proc	far
	push bp
	mov bp, sp
	mov ah, 47h
	mov dx, word ptr [bp+6]
	int 67h
	and ah, ah
	je L010B
	call far ptr _ems_fatal_error
L010B:
	pop bp
	retf
_ems_save_handle_map	endp

_ems_restore_handle_map	proc	far
	push bp
	mov bp, sp
	mov ah, 48h
	mov dx, word ptr [bp+6]
	int 67h
	and ah, ah
	je L0120
	call far ptr _ems_fatal_error
L0120:
	pop bp
	retf
_ems_restore_handle_map	endp

_ems_map_multiple_pages	proc	far
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
	call far ptr _ems_fatal_error
L013E:
	xor al, al
	pop ds
	pop si
	pop bp
	retf
_ems_map_multiple_pages	endp

_ems_map_multiple_segments	proc	far
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
	call far ptr _ems_fatal_error
L0160:
	xor al, al
	pop si
	pop ds
	pop bp
	retf
_ems_map_multiple_segments	endp

_ems_move_region	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	lds si, dword ptr [bp+6]
	mov ax, 5700h
	int 67h
	and ah, ah
	je L017C
	call far ptr _ems_fatal_error
L017C:
	xor al, al
	pop si
	pop ds
	pop bp
	retf
_ems_move_region	endp

_ems_resize_handle	proc	far
	push bp
	mov bp, sp
	mov dx, word ptr [bp+6]
	mov bx, word ptr [bp+8]
	mov ah, 51h
	int 67h
	and ah, ah
	je L0198
	call far ptr _ems_fatal_error
L0198:
	xor al, al
	pop bp
	retf
_ems_resize_handle	endp

_ems_query_mappable_count	proc	far
	mov ax, 5801h
	int 67h
	and ah, ah
	je L01AA
	call far ptr _ems_fatal_error
L01AA:
	mov ems_mappable, cx
	retf
_ems_query_mappable_count	endp

_ems_get_mappable_pages	proc	far
	push bp
	mov bp, sp
	push di
	les di, dword ptr [bp+6]
	mov ax, 5800h
	int 67h
	and ah, ah
	je L01C4
	call far ptr _ems_fatal_error
L01C4:
	mov ems_mappable, cx
	pop di
	pop bp
	retf
_ems_get_mappable_pages	endp

_ems_set_handle_name	proc	far
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
_ems_set_handle_name	endp

_ems_find_named_handle	proc	far
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
_ems_find_named_handle	endp

_ems_set_alternate_map	proc	far
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
_ems_set_alternate_map	endp

_ems_get_alternate_map	proc	far
	push di
	mov ax, 5B00h
	int 67h
	mov al, bl
	pop di
	retf
_ems_get_alternate_map	endp

_ems_query_alternate_map_size	proc	far
	mov ax, 5B02h
	int 67h
	mov ems_altmap, dx
	retf
_ems_query_alternate_map_size	endp

_ems_allocate_alternate_map	proc	far
	mov ax, 5B03h
	int 67h
	mov al, bl
	retf
_ems_allocate_alternate_map	endp

_ems_free_alternate_map	proc	far
	push bp
	mov bp, sp
	mov bl, byte ptr [bp+6]
	mov ax, 5B04h
	int 67h
	xor al, al
	pop bp
	retf
_ems_free_alternate_map	endp

emm_name	db	'EMMXXXX0', 0

_ems_detect_manager	proc	far
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
	call far ptr _ems_query_status
	test ah, 0FFh
	jne L025D
	mov ax, 1
	retf
L025D:
	xor ax, ax
	retf
_ems_detect_manager	endp

_ems_initialize	proc	far
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
	call far ptr _ems_detect_manager
	test ax, 0FFh
	je L02B5
	call far ptr _ems_query_version
	and ah, ah
	jne L02B5
	cmp al, 32h
	jl L02B5
	call far ptr _ems_query_page_frame
	mov ems_active, 1
L02B5:
	pop si
	retf
_ems_initialize	endp

_ems_fatal_error	proc	far
	int	3
	push ds
	mov ax, offset DGROUP:ems_error
	push ax
	jmp far ptr _Punt
	retf				; unreachable
_ems_fatal_error	endp

EMS_TEXT	ends
	end
