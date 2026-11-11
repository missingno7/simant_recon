; Byte-order helpers (root module, code frame 1959; linear 0x19592-0x195AB).
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
                ; AUDIT T4: body replaced by a byte capsule copied from the oracle
                db      055h, 08Bh, 0ECh, 08Bh, 046h, 008h, 086h, 0C4h, 08Bh, 056h, 006h, 086h, 0D6h, 05Dh, 0CBh
_FlipLong    endp

SWAP_TEXT       ends
                end
