# DOS remembered filename owner review (v34)

Scope is only the DOS far object referenced as `fd_50F6_3862` by S09. This is a pinned evidence review, not a source candidate. No canonical source, layout, promotion, or Git state was changed.

**Disposition:** the object is still unresolved. I found no independently grounded declaration or maximum complete-string length, so this review does not add storage or import a size.

The current S09 source identifies the remembered-name read/write chain. `LoadGame` passes its uninitialized local `name[100]` to `FileSelect`, then copies the result to the far object with `_fstrcpy`. `SaveGame`'s new-file route likewise passes its uninitialized local `name[100]`; its reuse-last route first copies the remembered global into that local. `FileSelect` accepts no capacity argument. After its `chdir`/current-drive setup, its first access to the name is a read of `*name`, before any later clearing. It forms paths with `sprintf`, copies them back without a bound, and returns the selected path for the caller's `_fstrcpy`.

The original DOS disassembly independently confirms the critical caller condition: at `LoadGame` entry, only the `ok` local is initialized before the call to `FileSelect` at S09:35F5:0052. Its pointer is the other local at BP-0x6c. After `FileSelect`'s preliminary `chdir`/current-drive setup, its first name access tests the pointed-to byte at S09:35F5:0402, before any later clearing of that buffer. `SaveGame` calls `FileSelect` with its local at S09:35F5:0237 on the new-file route without first initializing that local; only its reuse-last route copies the remembered name there. Thus the first value is not bounded by a producer contract; an uninitialized stack string is read before the dialog produces a selection. The subsequent full path is assembled/copied through unbounded string operations. The declaration `name[100]` does not cap what `FileSelect` reads or writes.

The only narrow bound found is on the typed basename: the editor is called with `maxLen == 9`, and its implementation decrements that limit, allowing at most eight typed characters. Directory display formats `ff.name` in a 12-character field; this does not constrain complete paths. The local `path[67]`, `buf[80]`, DOS 8.3 conventions, and the next mapped address are not used as evidence for the global's capacity.

The current-intake packet is still `INCOMPLETE` (188 compiled TUs, 15 unresolved symbols, 46 unresolved data-disposition bytes). The active production `window-ralloc-handles-contract-v1.json` is `admitted: true`, but admits only `_fd_50F6_385A` and `_fd_50F6_385E`, four bytes each. Its v27 root acceptance explicitly says “Filename3862 excluded”; the pinned policy says `do_not_infer_3862_extent: true`. This active contract is distinct from the older v27 worker candidate, which also records the unsized filename as open.

The read-only Win16 source search for `lastfilename` found only `ClearLastFileName.c`; that routine clears `editBufInvalidFlag[1834]` and does not declare a filename object. Win16 disassembly cards label `_LoadGame`, `_SaveGame`, and `_FileSelect`, but that naming evidence provides no declaration or storage extent. No generic cross-version match was used.

To reproduce the disassembly observations from the repository root, run:

```powershell
python tools/context.py LoadGame
python tools/context.py o09_35F5_0188
python tools/context.py o09_35F5_03C6
```

To repeat the source and Win16-name searches:

```powershell
rg -n -i --glob '*.c' 'FileSelect|o09_35F5_03C6' src
rg -n -i 'lastfilename' D:/Prog/simantw_recon/src
```

Run `python build/workers/dos_filename_owner_v34/verify_v34.py` to validate the pinned inputs and structured claims. The verifier is read-only.
