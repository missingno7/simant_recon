; Research-only DOS C1 intermediate capture hook for MSC 6.00AX.
; Used with CL /B2 E:\CAPTURE.EXE so C1 writes its intermediates and this
; program replaces C2. It never edits compiler binaries or production profiles.
;
; The old experiment hard-coded one compiler temporary stem. This version
; uses DOS findfirst/findnext and copies every matching six-character stem
; plus EX/IN/ST/SY suffix into E:\IR\, preserving each discovered filename.

.MODEL SMALL
.STACK 100h
.DATA
maskfile DB '????????',0
srcname  DB 'E:\',8 DUP (0),0
dstname  DB 'E:\IR\',8 DUP (0),0
inhandle DW ?
outhandle DW ?
found    DB 0
dta      DB 43 DUP (0)
buffer   DB 512 DUP (0)

.CODE
start:
    mov ax,@data
    mov ds,ax
    mov dx,OFFSET dta
    mov ah,1Ah
    int 21h

    mov dx,OFFSET maskfile
    xor cx,cx
    mov ah,4Eh
    int 21h
    jc finished

next_file:
    ; Compiler C1 files are eight-character names ending in EX, IN, ST, SY.
    mov si,OFFSET dta+1Eh
    cmp byte ptr [si+6],'E'
    jne check_in
    cmp byte ptr [si+7],'X'
    je save_file
check_in:
    cmp byte ptr [si+6],'I'
    jne check_st
    cmp byte ptr [si+7],'N'
    je save_file
check_st:
    cmp byte ptr [si+6],'S'
    jne next_search
    cmp byte ptr [si+7],'T'
    je save_file
    cmp byte ptr [si+7],'Y'
    jne next_search
save_file:
    mov di,OFFSET srcname+3
    mov bx,OFFSET dstname+6
    mov cx,8
copy_name:
    mov al,[si]
    mov [di],al
    mov [bx],al
    inc si
    inc di
    inc bx
    loop copy_name
    mov byte ptr [di],0
    mov byte ptr [bx],0
    call copy_file

next_search:
    mov dx,OFFSET maskfile
    mov ah,4Fh
    int 21h
    jnc next_file

finished:
    mov ax,4C00h
    int 21h

copy_file PROC NEAR
    mov dx,OFFSET srcname
    mov ax,3D00h
    int 21h
    jc copy_done
    mov inhandle,ax

    mov dx,OFFSET dstname
    xor cx,cx
    mov ah,3Ch
    int 21h
    jc close_input
    mov outhandle,ax

copy_loop:
    mov bx,inhandle
    mov cx,512
    mov dx,OFFSET buffer
    mov ah,3Fh
    int 21h
    jc close_both
    or ax,ax
    jz close_both
    mov cx,ax
    mov bx,outhandle
    mov dx,OFFSET buffer
    mov ah,40h
    int 21h
    jc close_both
    jmp copy_loop

close_both:
    mov bx,outhandle
    mov ah,3Eh
    int 21h
close_input:
    mov bx,inhandle
    mov ah,3Eh
    int 21h
copy_done:
    ret
copy_file ENDP
END start
