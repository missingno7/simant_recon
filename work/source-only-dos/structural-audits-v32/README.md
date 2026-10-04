# v32 bounded compiler and structural investigations

These investigations admit no owner, layout binding or exact function. The
accepted v31 source-only boundary remains at `e4227d5`: 188 compiled TUs,
15 imports, 46 functional data bytes, 113 historical bytes and seven open layout
gates. The 29 strict behavioral implementations remain confirmed. Independent
game linking, execution and human acceptance are pending.

The single GPT-6.1 Sol investigation in `forensics-v32/REPORT.md` reviews retained
exhaustion evidence before reproducing three whole-TU near candidates. Root's
three fresh compiles reproduce the exact objects: `o15_384C_0239` has two
stack-home operand bytes, `FindIndex` three branch bytes, and `f_171C_0CF4` six
stack-home operand bytes. Their 7, 6 and 57 accepted peers, private data, fixup
binding and relocations pass. No credible new C hypothesis emerged; there was
no expansion, new-family search, semantic change or promotion. In particular,
the stack homes do not prove a wide flag or a missing pointer declaration.

The heap census in `heap-v38/` contains no application `__fheap` declaration or
live external fixup among 188 actual objects. The four diagnostic partial links
in `heap-v39/` move only `root:171C` first. Archive selection stays identical
under each linker. RTLink 4.00 still selects `fmalloc` plus `fdata` and reports
duplicate `__ffree`; 6.10 selects `fdata` without `fmalloc`. All four images have
15 unresolved symbols and were never executed. Root reparsed 454 selected member
instances and reopened all object and raw log/map pins. Both tested explanations
are rejected; the extraction cause and historical `79F0` owner remain open.

The database review in `database-v32/` separates the exact hazards from generic
early failures. At most three database calls precede callback initialization.
An early failure alone is therefore not either fifth-call access. Its `Punt`
nevertheless executes a zero far target, followed on ordinary continuation by
another zero target. That machine boundary has no accepted control/state
contract. If startup resumes with the guard latched, later recursive `Punt`
returns can expose the slot `-1` and `db_handles[4]` accesses. Both gates stay
unresolved; standalone CRT exit tests do not establish game fatal-path closure.

The separate `tail-bss-v32/` review corrects an overbroad documentation claim.
The final three section bytes map to DGROUP `8B9D..8B9F`. Accepted stock CRT
startup clears `[8B9E,94F0)` before initializers and `main`, overwriting only the
last two. Root reverified all 90 accepted runtime members with full fixup binding
and relocation checks. The first byte, physical source fields, historical
mastering mechanism and an independent placement proof remain open. The packet
admits no data disposition, adds no storage and runs no image. Its separate
index retains the pre-correction document without refreshing the worker pin.
The [separate documentation addendum](../../../docs/exe-format-tail-v32.md)
carries the correction. Editing the original pinned document caused 47 preflight
pin errors during validation; its exact frozen content was restored. The failed
run remains a diagnostic, and no accepted evidence pin was refreshed.

Final historical validation passes, including all 375 repository tests (two
skips) and 48 codegen rules. `boundary.json` and the separate boundary index pin
the successful log, the earlier failure and the focused restored-document test.
The newly generated progress observation is preserved in the archive; the
original progress inputs retain their frozen identities because only the date
would otherwise change. The source-only v31 acceptance packet is unchanged.

`root-review.json` records the independent review. `preservation-index.json`
preserves unchanged worker receipts, whole-module drafts/listings and raw text
artifacts; no OBJ, EXE or library payload is archived. The worker review flags
remain pending in their original receipts. Scripts retain original scratch-path
assumptions and are preserved as run mechanics, not cold-checkout replay tools.

Run `python work/source-only-dos/structural-audits-v32/recheck.py` for read-only
archive integrity. Later local observations are reported separately and do not
refresh frozen hashes or turn these results into current-build acceptance.
