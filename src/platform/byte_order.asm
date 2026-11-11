; Swaps the byte order of a word or a double word. Both routines use small assembly entry
; points.
; File name and folder are ours, inferred from the DOS routines or storage defined here.
; DOS: resident code; segment 1959; complete original translation unit.
; Windows: _TEXT, from recorded function pairs in the Windows symbol inventory. This is outside
; the six named application groups.
; Build profile: masm510; /Mx.
;
; Genuine assembly: MSC 6.00 never emits this shape.  C spellings of the swap
; compile to "mov al,[bp+7] / mov ah,[bp+6]", and an inline-asm body always gets
; an "mov sp,bp" epilogue (experiments in docs/codegen-rules.md, rule ASM-1).
; The original encodes "xchg al,ah" (86 C4), which is how MASM assembles that
; operand order.

SWAP_TEXT       segment word public 'CODE'
                assume  cs:SWAP_TEXT

                public  _FlipWord
                public  _FlipLong

; unsigned far FlipWord(unsigned value): swap the bytes of a word
_FlipWord    proc    far
                push    bp
                mov     bp, sp
                mov     ax, [bp+6]
                xchg    al, ah
                pop     bp
                ret
_FlipWord    endp

; unsigned long far FlipLong(unsigned long value): swap the byte order of a dword
_FlipLong    proc    far
                push    bp
                mov     bp, sp
                mov     ax, [bp+8]
                xchg    al, ah
                mov     dx, [bp+6]
                xchg    dl, dh
                pop     bp
                ret
_FlipLong    endp

SWAP_TEXT       ends
                end
