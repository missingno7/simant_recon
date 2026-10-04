_DATA segment word public 'DATA'
extrn _g_8ED8:byte
extrn _g_8EC0:byte
_DATA ends
DGROUP group _DATA
CHECK_TEXT segment word public 'CODE'
assume cs:CHECK_TEXT, ds:DGROUP
public _FrameProbe
_FrameProbe proc far
push bx
push ds
mov ax, seg DGROUP
mov dx, ss
cmp ax, dx
jne BadStack
mov dx, ds
cmp ax, dx
jne BadStack
mov bx, 100h
add bx, OFFSET DGROUP:_g_8EC0
mov al, byte ptr ss:[bx]
jmp HaveResult
BadStack:
mov al, 0EEh
HaveResult:
mov byte ptr cs:Observed, al
push ds
push cs
pop ds
mov dx, offset Observed
mov cx, 1
mov bx, 1
mov ah, 40h
int 21h
pop ds
pop ds
pop bx
retf
_FrameProbe endp
Observed db 0
CHECK_TEXT ends
end
