# Root-pending v32: startup clearing at the common-tail boundary

Status: `STATIC_RUNTIME_CLEAR_PROVEN_FOR_LAST_TWO_TAIL_BYTES; FIRST_TAIL_BYTE_AND_HISTORICAL_BOUNDARY_OPEN`. This packet is not reviewed or admitted, and it makes no automatic debt disposition.

The accepted runtime manifest binds `llibcr.lib(dos\\crt0.asm)` as a 255-byte `_TEXT` contribution at 29F4:001C, with member SHA-256 `2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d`. The checker decodes the complete OMF member and confirms its non-fixup bytes against the loaded historical member. The MZ header enters RTLink at 2CFF:06F8; the manager's setup ends with a far jump to 29F4:001C.

The installed CRT source and loaded disassembly agree on normal EXE startup: after DOS-version and stack checks, the code sets SS to DGROUP, copies SS to ES, clears DF, loads DI from `_edata` and CX from `_end`, subtracts DI, zeros AX, and executes `REP STOSB`. Exact OMF external fixups and their historically bound operands resolve `_edata` to DGROUP:8B9E and `_end` to DGROUP:94F0. A second `_end-2` stack-bound reference resolves to 94EE, independently agreeing on `_end=94F0`. Thus the loop writes the half-open interval `[DGROUP:8B9E, DGROUP:94F0)`, including 8B9E and 8B9F, and excluding 8B9D.

The section-27 file image ends at DGROUP offset 8BA0. Its final three file bytes map to 8B9D–8B9F. The accepted runtime `PAD` contribution ends at 8B9C and `EPAD` ends at 8B9D; `_edata` is one byte later. The first confirmed source-owned `_BSS` contribution is root:0093's word-aligned two-byte seed at 8BA2. A start at 8BA0 is consistent with the file-backed limit and the seed placement, but this probe does not establish a BSS owner at 8BA0 or assign source fields to the two cleared tail bytes. The common-tail values and broader mastering seam remain unresolved.

On the normal DOS 2+ path with enough stack, the clear precedes the optional `__qczrinit`, `_setenvp`, `_setargv`, `_cinit`, and `main` calls. Two pre-clear exits are visible in the CFG: the DOS 1 path returns to PSP:0000, and the stack-overflow path calls the CRT message routines then terminates through DOS. Neither reaches game code or C initialization. The stack-error messages inspect their own CRT message/debugger data; that exceptional path is not evidence that the overlapping tail bytes are harmless.

No poison-before-startup fixture was attempted: the static pass did not establish a verified RTLink entry-override hook, and the exact accepted CRT control flow answers the normal-entry write question without replacing or patching it. No compiler or linker ran, no executable was produced or executed, and the original executable was only read through the analysis parser. Historical address and boundary observations remain oracle-derived rather than an independent placement proof.

Reproduce from the repository root:

```powershell
python build/workers/dos_tail_bss_boundary_v32/probe_tail_bss_boundary_v32.py
```

The root-false machine-readable receipt includes source/tool/input pins, complete decoded CRT OMF payloads and fixups, exact original-entry disassembly, and the computed file/load offsets: [tail-bss-boundary-v32.json](build/workers/dos_tail_bss_boundary_v32/tail-bss-boundary-v32.json). The checker is [probe_tail_bss_boundary_v32.py](build/workers/dos_tail_bss_boundary_v32/probe_tail_bss_boundary_v32.py).
