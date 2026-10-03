# Whole-program initialized shared-state provider proof

This packet is diagnostic only and is not selected by any production build.

`portable/tools/asm_state_provider.py` emits one C provider for three PUBLIC
EMS scalars from `src/root/m195A.asm`: the EMM version byte and unallocated and
total page words. It counts the source `_DATA` declarations, adds the accepted
`root:195A` `_DATA` placement, and requires the resulting addresses to match
both `layout/symbols.json` and current `GLOBAL_STATE` views in the captured
whole-program migration. The generated C declarations retain the DOS widths
(`int8_t` and `int16_t`) and the literal source zero initializers.

`portable/tools/source_state_aliases.py` describes source-level view
canonicalization without defining extra storage. Four unresolved PUBLIC views
map to initialized globals in `src/root/m0250.c`; two unresolved views map to
entries 3 and 4 of its sibling source-owned five-string pointer table in
`src/root/m15F8.c`. An existing scalar pointer view of that table is resolved
to element 0. The transform rewrites only extern declarations and identifier
uses, retaining a single canonical storage owner per object.

Run `python portable/tests/recovered/whole_program_asm_state/run_proof.py` to
recreate the immutable receipt at
`portable/tests/recovered/evidence/whole-program-asm-state-v1/report.json`.
The runner refuses to overwrite that report; pass a new `--report` path for a
fresh verification packet. It has positive source/address controls, negative
wrong-width and wrong-address controls, and native compile-only checks for the
provider plus three converted consumer TUs. These checks establish source and
declaration consistency, not runtime, link, EMS hardware, or pixel equivalence.

The far page-frame pointer `fd_55B3_360E` remains explicit debt: its source is a
`dd` far pointer and this packet has no approved native pointer provider. The
private `ems_active` byte is not a shared PUBLIC contract. Graphics driver,
font canvas/stride, audio scheduler/resource voice, and input-owned state are
outside this provider.
