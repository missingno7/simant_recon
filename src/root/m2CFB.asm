; Memory hook thunks (root, code frame 2CFB; linear 0x2CFB2-0x2CFE4).
;
; Ten far jumps into the memory manager (module 171C), placed after the
; runtime's EMULATOR_TEXT (2CFB:0000-0001).  The database modules 19A9/19DC
; call these entry points instead of the 171C functions.  Genuine assembly:
; a C function cannot consist of a bare "jmp far" (MSC always emits a
; prologue or at least retf after the body), and each entry is exactly the
; 5-byte EA instruction.

                extrn   _f_171C_13CA:far
                extrn   _f_171C_13E4:far
                extrn   _f_171C_152C:far
                extrn   _f_171C_14BE:far
                extrn   _f_171C_16EA:far
                extrn   _f_171C_1794:far
                extrn   _f_171C_1750:far
                extrn   _f_171C_18A6:far
                extrn   _f_171C_1686:far
                extrn   _f_171C_15A2:far

MEMHOOK_TEXT    segment word public 'CODE'
                assume  cs:MEMHOOK_TEXT

                public  _jt_171C_13CA
                public  _jt_171C_13E4
                public  _jt_171C_152C
                public  _jt_171C_14BE
                public  _jt_171C_16EA
                public  _jt_171C_1794
                public  _jt_171C_1750
                public  _jt_171C_18A6
                public  _jt_171C_1686
                public  _jt_171C_15A2

_jt_171C_13CA:  jmp     _f_171C_13CA
_jt_171C_13E4:  jmp     _f_171C_13E4
_jt_171C_152C:  jmp     _f_171C_152C
_jt_171C_14BE:  jmp     _f_171C_14BE
_jt_171C_16EA:  jmp     _f_171C_16EA
_jt_171C_1794:  jmp     _f_171C_1794
_jt_171C_1750:  jmp     _f_171C_1750
_jt_171C_18A6:  jmp     _f_171C_18A6
_jt_171C_1686:  jmp     _f_171C_1686
_jt_171C_15A2:  jmp     _f_171C_15A2

MEMHOOK_TEXT    ends
                end
