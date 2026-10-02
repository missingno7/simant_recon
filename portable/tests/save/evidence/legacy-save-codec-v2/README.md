# Legacy save codec and Next9 bindings, V2

This packet adds a portable 307-row SaveRec binding over the diagnostic Next9 state extension. It preserves the V1 packet and its original source snapshots unchanged. The V2 codec uses explicit storage policy per binding: numeric native 16/32-bit components serialize as DOS little-endian values, while byte streams remain byte-for-byte. In particular, row 99 is the raw 20-byte interior slice `[20,40)` of `fd_3D57_087A[72]`; the four DrawSwarm arrays remain all 50 bytes each. Row 29 follows the Next9 backing type `int16_t[16][12]`, not the original byte-array alias declaration, because the native consumers store and read numeric cells.

`validation.json` records source/EXE initializer checks, negative initializer control, strict inherited Next9 rebuild, and a controlled original DOS `SaveGame` write. The runner observed 307 actual DOS `write` calls totaling 48,386 bytes; a native decode/encode pass reproduced that exact captured stream in normal and forced-big-endian representations. The DOS payload is retained only under ignored `build/workers/savegame_original_write/`; no payload bytes or original executable capsule are copied into this packet.

Reproduce from the repository root:

```powershell
python portable/tools/recover_source_next9.py --out build/workers/recovered_source_next9/generated
python portable/tests/save/finalize_next9_evidence.py
```

The generated state, module objects, DOS payload, and native test binaries are local build products and are not committed. Their identities and all committed source inputs are pinned in `input-pins.json`, `source-binding-proof.json`, and `validation.json`. The source audit is based on `src/S09/m35F5.c`, `src/S13/m384C.c`, `src/data/d3D57.c`, `src/data/d3E1D.c`, and the locked `assets/SIMANT.EXE`. V2 is diagnostic evidence only; no production profile selection or live file service is included.
