# DGROUP 56FE ownership investigation v32

Status: **OPEN / no admission**. This bounded review found no typed owner for
`55B3:56FE..5701` and does not claim runtime or human acceptance. It changes no
canonical source, manifest, provenance, or promotion record. Mechanical input and
artifact hashes are in `pins.json`; regenerate them with `python
build/workers/dos_dgroup_56fe_owner_v32/make_pins.py`.

## Findings

The current SOURCE_ONLY_DOS report retains `dgroup_56fe` as four bytes of
`UNKNOWN_FIELD_SEMANTICS`. The historical map records four zero bytes, no relocation,
and the heuristic owner `root:195A`. The original-function reference scan has no direct
data operand into this span. Its sole immediate-address candidate is `f_195A_0166` at
`195A:016E`, `mov ax, 0x5700`. The pinned context shows that function first loads its
far argument into `DS:SI`, then sets `AX=5700h` and invokes `int 67h`. Thus `5700h` is
the EMS service selector in this instruction sequence; it is not an address or a read
or write of DGROUP 5700h. This candidate does not ground the map's `root:195A` hint.

Current object and placement evidence puts the accepted `root:195A` `_DATA`
contribution at `55B3:3602`, size 28. Its generated OMF `_DATA` segment is 28 bytes.
`root:1CE2` contributes 74 bytes ending at 56FE; `root:1E57` begins at 5702 with an
806-byte `_DATA` contribution. Its generated OMF exports `g_5702` at `_DATA` offset
zero. Both neighboring starts and ends are word aligned, so this four-byte interval is
not explained by the recorded word alignment. These present source objects pin the
known neighboring contributions; they do not identify the original contributor for
the interval.

In current C, `g_5702` is a 32-word array with the initial sentinel `0x8000` at its
first element. The window-stack routines read and update that array, and the original
disassembly of `f_1E57_0052`, `f_1E57_00B1`, and `f_1E57_038E` agrees with accesses
starting at absolute offset 5702 and forward. A repository text census found no
`56FE` address token or negative `g_5702` index. No source field, initializer,
producer, lifetime, or interior alias is established for the preceding four bytes.
The scan does not exclude computed aliases or arbitrary pointer flow.

The current DOS↔Win16 correspondence table has no pair for the inspected
`f_195A_0166` or `f_1E57` routines and contains no data-symbol correspondence. It adds
no cross-version anchor for this span.

## Open evidence

1. Identify the original object or linker contribution for DGROUP `56FE..5701` from
   original object/SEGDEF/LEDATA or RTLink ordering records. The checked-in executable
   map and current rebuilt objects do not name that contributor.
2. Establish whether any original computed or indirect pointer reaches this range;
   the function scan explicitly excludes general dynamic pointer flow.
3. If reachable or source-owned, locate the field-level type, initialization producer,
   reads/writes, lifetime, and aliases. No evidence currently supports a four-byte
   type or a semantic value.
4. A Win16 data-level identity would need an independently anchored variable or
   initialization/use chain; the current correspondence index supplies none.

Until one of these routes produces positive evidence, retain all four bytes as
explicit unknown debt. The source owner remains unresolved.
