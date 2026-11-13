; Reads BIOS ticks and keyboard state and installs a Ctrl-Break hook. The same module contains a
; byte swapping copy helper.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: resident code; segment 1F58; complete original translation unit.
; Windows: none (DOS only), based on the platform-specific code or DOS release data.
; Build profile: masm510; /Mx.
;
; Root code frame 1F58, linear 1F586-1F668.
; Genuine assembly: BIOS data area and interrupt-vector access through ES=0, int 16h,
; cli/sti around the vector swap, xchg with memory, frameless procs (rules ASM-1, ASM-2).

_DATA	segment word public 'DATA'
	extrn	_g_53BD:byte
_kbd_pending_key		dw	0		; pending key (scan code in AH, 80h = pushed back)
_kbd_second_pending_key		dw	0		; second pending key
_dos_saved_int23_offset		dw	0		; saved INT 23h vector (offset, segment)
_dos_saved_int23_segment		dw	0
_DATA	ends
DGROUP	group	_DATA

	extrn	_atexit:far

KBD_TEXT	segment word public 'CODE'
	assume	cs:KBD_TEXT, ds:DGROUP

	public	_timer_bios_tick_count
	public	_input_return_zero
	public	_mem_exchange_byte_ranges
	public	_kbd_poll_bios_key
	public	_kbd_read_bios_char
	public	_kbd_unread_char
	public	_kbd_read_key_code
	public	_kbd_restore_ctrl_break_vector
	public	_kbd_install_ctrl_break_vector

_timer_bios_tick_count	proc	far
	xor ax, ax
	mov es, ax
	mov ax, word ptr es:[46Ch]
	mov dx, word ptr es:[46Eh]
	retf
_timer_bios_tick_count	endp

_input_return_zero	proc	far
	xor ax, ax
	retf
_input_return_zero	endp

_mem_exchange_byte_ranges	proc	far
	push bp
	mov bp, sp
	push ds
	push si
	push di
	mov cx, word ptr [bp+0Eh]
	and cx, cx
	je L0033
	les di, dword ptr [bp+6]
	lds si, dword ptr [bp+0Ah]
L002A:
	mov al, byte ptr es:[di]
	xchg byte ptr [si], al
	stosb
	inc si
	loop L002A
L0033:
	pop di
	pop si
	pop ds
	pop bp
	retf
_mem_exchange_byte_ranges	endp

_kbd_poll_bios_key	proc	far
	mov ax, word ptr _kbd_pending_key
	and ax, ax
	jne L0047
	inc ah
	int 16h
	jne L0047
	xor ax, ax
L0047:
	cmp byte ptr _g_53BD, 0
	je L0059
	xor bx, bx
	mov es, bx
	and word ptr es:[417h], not NumLockState
L0059:
	retf
_kbd_poll_bios_key	endp

_kbd_read_bios_char	proc	far
	mov ax, word ptr _kbd_pending_key
	and ax, ax
	jne L0072
	xor ah, ah
	int 16h
	and al, al
	jne L0070
	mov al, ah
	mov word ptr _kbd_pending_key, ax
	xor al, al
L0070:
	cbw
	retf
L0072:
	xor ah, ah
	xor cx, cx
	xchg word ptr _kbd_second_pending_key, cx
	mov word ptr _kbd_pending_key, cx
	retf
_kbd_read_bios_char	endp

_kbd_unread_char	proc	far
	push bp
	mov bp, sp
	mov ax, word ptr [bp+6]
	mov ah, 80h
	xchg word ptr _kbd_pending_key, ax
	mov word ptr _kbd_second_pending_key, ax
	pop bp
	retf
_kbd_unread_char	endp

_kbd_read_key_code	proc	far
	call far ptr _kbd_read_bios_char
	and ax, ax
	jne L00A0
	call far ptr _kbd_read_bios_char
	mov ah, 8
L00A0:
	retf
_kbd_read_key_code	endp

_kbd_restore_ctrl_break_vector	proc	far
	cli
	xor ax, ax
	mov es, ax
	mov ax, word ptr _dos_saved_int23_offset
	mov dx, word ptr _dos_saved_int23_segment
	mov word ptr es:[8Ch], ax
	mov word ptr es:[8Eh], dx
	sti
	retf
_kbd_restore_ctrl_break_vector	endp

_kbd_install_ctrl_break_vector	proc	far
	push bp
	mov bp, sp
	cli
	les bx, dword ptr [bp+6]
	mov dx, es
	xor ax, ax
	mov es, ax
	xchg word ptr es:[8Ch], bx
	xchg word ptr es:[8Eh], dx
	mov word ptr _dos_saved_int23_offset, bx
	mov word ptr _dos_saved_int23_segment, dx
	push cs
	assume	ds:KBD_TEXT
	lea bx, _kbd_restore_ctrl_break_vector
	assume	ds:DGROUP
	push bx
	call far ptr _atexit
	add sp, 4
	sti
	pop bp
	retf
_kbd_install_ctrl_break_vector	endp

KBD_TEXT	ends

NumLockState	equ	20h		; BIOS keyboard flag byte 0040:0017, bit 5

	end
