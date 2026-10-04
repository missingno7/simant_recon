# v37a correction: RTLink data-only library selection

## Correction to v37 evidence

The v37 `LIB.EXE` stdin driver was incomplete. It supplied `Y` to the “Create?” prompt, then reached end-of-input at the later library prompts. All three logs end with `LIB : fatal error U1158: terminator missing`. Although LIB had already written parseable library bytes, those runs cannot be described as clean librarian runs.

This append-only v37a run uses Microsoft LIB 3.17’s documented response-file form (`LIB @response-file`), as described in the [Microsoft C Compiler User’s Guide, Managing Libraries](https://archive.computerhistory.org/resources/access/text/2024/05/102734492-05-0002-acc.pdf). For example, the `DATAONLY` response contains the library name, `yes`, `+DONLY.OBJ`, `NUL`, and the output library name, one response per line. The three resulting librarian logs contain no fatal or other error, and `LIB <name>.LIB;` consistency-check runs produce no diagnostic output. The test harness then parses each actual library directory and embedded OMF module, checks the expected module name and public symbols, and records library and member hashes.

The C sources were recompiled into fresh objects. Their `DONLY`, `CDMEM`, and `COMMON` object hashes match v37 exactly. The new clean-run library hashes and module lists also match the bytes and members that v37 had written before its fatal prompt error. The earlier v37 report remains untouched; the side-by-side comparison is recorded in `selection-cause-controls-v37a.json`.

## Confirmed selection result

The corrected libraries confirm the same control result under pinned RTLink 4.00 and 6.10:

- With `DATAONLY.LIB(DONLY.C)` and `CODEDATA.LIB(CDMEM.C)` explicitly on the `LIBRARY` command but unreferenced, neither linker selects either custom member.
- With a live fixup to the initialized data public, both select `DONLY.C`.
- With a live call to the function in the code-plus-data module, both select `CDMEM.C`.
- A live fixup to a symbol that exists only as a COMDEF in `COMMON.C` does not extract it; both links leave that symbol undefined. This is a limited COMDEF contrast, not a positive data-only control.
- Clean natural-main CRT links under both profiles select the stock `fdata.asm` member through the pinned `stdalloc.asm` → `malloc.asm` → `fmalloc.asm` → `fdata.asm` fixup chain.

The libraries passed through the pinned Microsoft LIB 3.17 binary (SHA-256 `418aec4161ef09084aaf2bed66e4de9e007eb6f2bedd1990b73707f624336ff3`). The actual post-LIB `DONLY.C` member defines `_probe_data_only` at `_DATA` offset 0; `CDMEM.C` defines `_probe_cd_data` and `_probe_cd_fn`. The JSON receipt records each source object hash, archive hash, embedded-member hash, public definition, link log, map, and log/map hash. No generated executable was run.

## Corrected OMF comment reading

The comment comparison must use the post-LIB members supplied to RTLink. Those members contain class A3 and class A2 comments: for example, `DONLY.C` has A3 payload `05444f4e4c59` (length-prefixed `DONLY`) and A2 payload `01`; pinned `fdata.asm` has A3 payload `056664617461` (length-prefixed `fdata`) and A2 payload `01`. The TIS OMF specification identifies A2 as the link-pass separator and A3 as LIBMOD, a library-module-name record that the librarian inserts and the linker ignores ([TIS OMF Specification, pp. 4–5 and 19](https://openwatcom.org/ftp/devel/docs/omf.pdf)). Therefore, the earlier v37 comparison against pre-LIB C objects created a metadata difference that does not exist in the linker inputs. These ordinary module-name records give no reason to infer automatic extraction or an fdata-specific directive.

## Remaining limit

The corrected controls rule out generic extraction of every unreferenced data-only member, but do not identify why the current 186-object RTLink 6.10 partial link selects `fdata.asm` alone. That run’s selected-member log and map show fdata but no fmalloc; local RTLink documentation does not explain its app-specific cause. This leaves linker-trigger attribution open and establishes no historical `DGROUP:79F0` placement, original byte identity, or application reachability. The v37a result does not change v36’s admission decision.

See [selection-cause-controls-v37a.json](selection-cause-controls-v37a.json) for the structured receipts and [probe_fdata_selection_cause_v37a.py](probe_fdata_selection_cause_v37a.py) for the clean-response-file controls. All v37 files remain unchanged.
