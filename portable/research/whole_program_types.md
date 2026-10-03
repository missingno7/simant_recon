# Whole-program type and shared-record audit

This static audit scans every manifest-owned C translation unit under `src/root/` and `src/S*`. Its purpose is to establish safe mechanical-conversion boundaries, not to infer a universal C object model from repeated names. No historical source, generator, or production file was changed.

## Scope and result

The frozen manifest contains 127 modules; this audit selected 93 C translation units and excluded 29 ASM modules. It found 133 tagged struct/union definitions across 40 unique tagged names. Among repeated tag names, 2 have identical textual field lists and 9 have conflicting field lists. Of 40 typedef declarations, 4 alias names repeat; 3 repeat with conflicting aggregate/type definitions.

The complete normalized declaration groups and all source SHA-256 pins are in [whole_program_types.json](whole_program_types.json). “Identical” means the source member declarations match after whitespace normalization; it does not prove host `sizeof`, alignment, runtime aliasing, serialized layout, or semantic equivalence.

## Highest-value collisions

| Name | Source evidence | Finding | Conversion boundary |
|---|---|---|---|
| `Rect` | 38 definitions across root and overlays | All 38 have fields `int left, top, right, bottom` in that order. | Strong common type candidate once fields use explicit DOS-width scalars and target assertions; preserve source edges and coordinate conventions. |
| `Event` | 24 definitions | Seven field-list variants: common 8-word layout; split modifier bytes; `Point where`; compact S11 record; S19 `x6` variant. | Distinct named event views over fixed-width data, with source-specific accessors. Do not use one generic `Event` alias. |
| `Pt` / `Point` | 23 `Pt` tags; seven `Point` typedefs | `Pt` usually `x,y`, but two definitions use `h,v`; `Point` typedef variants include `v,h`. | Keep XY and HV named views; identical storage word count does not establish field semantics or interchangeability. |
| `Win` / `Obj` | Root m23AE/m2505 and S26 m39C7; API calls cross these source modules | Window declarations share offsets for flags `0x1c` and object pointer table `0x2c`; S26 adds min/grid/zoom fields. Object views place `type` at `0x21` but otherwise expose different fields. | Common offset-checked byte-backed record with named typed views/accessors; model handles outside the host record. |
| `OpenDBRec` / `IndexEntry` | m1A28, m1986, m19A9 share `fd_50F6_3958` | Three incompatible runtime table views; index row is a far pointer view in m1986, a 32-bit file offset view in m19A9. | Separate file wire DTOs from runtime state. Review each field offset against reads/writes before defining shared accessors. |
| `Sample` / `Instr` / `Song` | root audio TUs m0000, m2815, m284A, m290D, m295C | Same tags recur with different fields. m290D passes Sample to the m0000 loader, establishing a shared 14-byte DOS prefix; the m290D `data` field is not read in the scanned bodies. `Instr` views of `fd_50F6_0000` share a six-byte pointer-bearing record selected by resource mode. | Preserve owner-specific records and only share the Sample prefix proven by field order, packed declaration, callsite and callee accesses. Use the evidenced tagged pointer-bearing table owner for `fd_50F6_0000`. |

The first audit pass treated the `fd_50F6_0000` collision as unresolved. Follow-up against the data source and symbol registry establishes a stronger chain: it is one 56-entry DOS table with six-byte records; the nine source tables at `0x0C42 + k*0x150` are pointer-bearing instrument rows, and `f_277E_010A` copies each row into the same global table. `Voice.b` is a 32-bit view of the far-pointer tail in those source modes, not generally numeric. A native owner should use a tagged kind plus a real host reference and translate that copy path.

## Serialized bytes versus runtime pointers

Do not let a host pointer become an accidental wire field. The DOS source declares far pointers as four-byte values and `Handle` as a far pointer to a far pointer; native pointer sizes and indirection differ. The audio Sample prefix shares four bytes at `data`, but one view calls it a `Handle` and another a direct far data pointer. Model the handle token/reference relationship explicitly.

The database code supplies direct fixed-length I/O evidence: `m1A28` reads/writes 14 bytes of `DBHeader`; `m1986` reads a 20-byte index header and `count * 8` bytes into index rows; `m19A9` reads ten bytes into `DBRecordHeader` at row offset +14. Because the index row is viewed as `char far *data` in one TU and `long offset` in another, the portable file format should use fixed-width byte/word fields—not a native pointer—even while the exact pointer/offset encoding still needs asset-backed confirmation. `OpenDBRec` is a runtime table, not a wire DTO.

Explicit `#pragma pack(1)` appears around the full `m0000.c::Sample` definition. This packed source view is evidence for DOS layout only; a host overlay should use fixed-width fields and `_Static_assert` checks, and should not store native pointers in its pointer slot.

## Single-owner native global boundary

The current whole-program scratch catalog is diagnostic-only and is hash-labelled separately in the JSON. At the observed snapshot it contains 2,150 declaration views and 750 unprovided contracts (495 global-state and 255 callable/external-ABI), with 478 distinct unprovided global storage starts and 17 starts carrying multiple symbol names. The scratch output changed during this audit; those values belong only to the recorded SHA and do not claim production or admission status.

For scalar map data, keep the established `SimGameWorld` byte arrays (`MapA`, `LifeA`, etc.) as the single owner; source-session bridge copies should be boundary transfer, not a second long-lived writable truth. Names with omitted array bounds are views. Do not infer extent from the next symbol. For aliases at one address, point each name at the same owner slice. For byte/word scalar views, use explicit-width accessors that preserve sign and endian rather than native union type-punning.

Pointer-bearing data needs a different owner rule. Source `d55B3_00B8.c` initializes nine tables of six-byte `{kind, far pointer}` entries; `f_277E_010A` copies them into `fd_50F6_0000`, a 56-entry table. Root modules consume these as different tagged pointer roles. Keep one native table and use the kind to select the typed host reference. Translate `Voice.b`’s raw far-pointer copy explicitly. Native pointers are correct for real host resource references; they are wrong inside a fixed-width DOS wire record or when blindly treated as unchanged DOS pointer bits. The `Sample.data` field also needs care: m0000 stores a `Handle`, while m290D’s different declaration is unused in the scanned bodies.

The database object is a runtime owner rather than a wire record: one `fd_50F6_3958` table is viewed as three `OpenDBRec` definitions. Give the owner native handle/reference fields and expose source-specific accessors. Keep file headers and eight-byte index rows as fixed-width wire DTOs; a native pointer must not replace the file offset that the DOS reader consumes.

## Recommended shared type headers

The report contains detailed bases and guardrails. Suggested split:

- `portable/game/types/dos_scalars.h`: fixed-width 8/16/32-bit scalar vocabulary; per-member conversion decisions and arithmetic checks remain explicit.
- `portable/game/types/dos_geometry.h`: shared `Rect` candidate plus separate XY/HV point types.
- `portable/game/types/dos_event_views.h`: fixed-width raw event DTO and named source-specific event views. The existing `portable/tests/input/process_edit_event_dto.h` is a bounded example of `int16_t` event/rectangle declarations.
- `portable/game/types/dos_window_views.h`: offset-asserted root/zoom window and object views backed by bytes/accessors, not host pointers.
- `portable/game/types/dos_database_records.h`: fixed-width wire records separate from runtime database state.
- `portable/game/types/dos_audio_views.h`: owner-specific audio records and a narrowly scoped Sample prefix.

The existing Empires TU rule’s “one source module per portable C file” is a useful shape, but its “all structs from one common header” rule cannot be applied by identifier alone here. Generate common declarations only after the alias groups, offsets, pointer semantics and wire/runtime boundary are reviewed; keep source-facing aliases scoped by historical module where layouts conflict. Likewise, the Stunts semantic audit’s type/layout assertions are a good verification pattern: assert scalar widths, each selected `sizeof` and `offsetof`, but attach them to source-grounded contracts and keep unresolved views marked as debt.

## Mechanical rules for the next port batch

1. Build the translation inventory from manifest ownership; retain one native C file per frozen TU and preserve body/member order.
2. Replace legacy scalar spellings with fixed-width aliases by reviewed declaration; separately audit promotion, signedness, shifts and narrowing.
3. Namespace every conflicting `struct` tag and typedef before adding a shared header. Deduplicate only exact declaration groups and only when their source-level semantic role matches.
4. Represent resource-file records as explicit wire DTOs with fixed-width members and verified byte lengths. Keep runtime pointers, handles, callback addresses and owner links in separate state or opaque handles.
5. For cross-TU shared objects, record declaration, shared symbol/API chain, observed field accesses, and expected offsets. Add compile-time layout checks and paired source-vs-native tests before routing multiple historical views through one native object.
6. Treat disassembly-derived pads/offsets as recorded byte views, not permission to use `#pragma pack` indiscriminately. The packed Sample is explicit source evidence; other structures need their own evidence.

The source pins cover the 93 selected historical C TUs plus `layout/manifest.json`; this receipt records static source pins; any changed source invalidates the snapshot and requires a new audit receipt.
