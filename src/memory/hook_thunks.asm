; Memory hook thunks (root, code frame 2CFB; linear 0x2CFB2-0x2CFE4).
;
; Ten far jumps into the memory manager (module 171C), placed after the
; runtime's EMULATOR_TEXT (2CFB:0000-0001).  The database modules 19A9/19DC
; call these entry points instead of the 171C functions.  Genuine assembly:
; a C function cannot consist of a bare "jmp far" (MSC always emits a
; prologue or at least retf after the body), and each entry is exactly the
; 5-byte EA instruction.

                extrn   _Ralloc:far
                extrn   _RallocFree:far
                extrn   _RallocFreshen:far
                extrn   _mem_handle_age_delta:far
                extrn   _RallocSize:far
                extrn   _RallocFreed:far
                extrn   _RallocMemoryFree:far
                extrn   _RallocRealloc:far
                extrn   _RallocType:far
                extrn   _RallocSetType:far

MEMHOOK_TEXT    segment word public 'CODE'
                assume  cs:MEMHOOK_TEXT

                public  _mem_hook_ralloc
                public  _mem_hook_rallocfree
                public  _mem_hook_rallocfreshen
                public  _mem_hook_age_delta
                public  _mem_hook_rallocsize
                public  _mem_hook_rallocfreed
                public  _mem_hook_rallocmemoryfree
                public  _mem_hook_rallocrealloc
                public  _mem_hook_ralloctype
                public  _mem_hook_rallocsettype

_mem_hook_ralloc:  jmp     _Ralloc
_mem_hook_rallocfree:  jmp     _RallocFree
_mem_hook_rallocfreshen:  jmp     _RallocFreshen
_mem_hook_age_delta:  jmp     _mem_handle_age_delta
_mem_hook_rallocsize:  jmp     _RallocSize
_mem_hook_rallocfreed:  jmp     _RallocFreed
_mem_hook_rallocmemoryfree:  jmp     _RallocMemoryFree
_mem_hook_rallocrealloc:  jmp     _RallocRealloc
_mem_hook_ralloctype:  jmp     _RallocType
_mem_hook_rallocsettype:  jmp     _RallocSetType

MEMHOOK_TEXT    ends
                end
