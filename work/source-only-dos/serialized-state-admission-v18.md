# Functional serialized-state storage review

Root accepts four independent 50-byte far objects for the DrawSwarm displacement
buffers: `fd_50F6_0F46`, `0F84`, `0FC6` and `1008`. Their generated provider uses
`unsigned char far [50]`. This is a functional storage and view decision, with
no historical COMDEF translation unit, placement, ordering or padding claim.

The complete source graph has only three modules using these names: canonical
DrawSwarm, its identical effective-module copy and the S09 SaveRec table. Both
DrawSwarm loops cap the index before access at 16. Its signed-byte reads and
writes are preserved by the canonical declarations. SaveRec separately exposes
all 50 bytes of each object as unsigned raw state, and LoadGame/SaveGame transfer
the entire registered span. The 34 tail bytes are observable loaded and saved
state even though the active animation loops do not index them. They cannot be
discarded or replaced with a 16-byte allocation.

The complete source/registry census finds no additional escaped pointer,
computed/numeric view or registered interior name. This evidence establishes
the complete source-visible allocation independently of neighboring addresses.
It does not assert that the signed and unsigned declarations are interchangeable
in every C implementation; the selected MSC target's actual byte views are
checked directly.

The fresh MSC provider emits four far COMDEFs, each 50 byte-sized elements,
without live code, initialized data, publics or fixups. Both RTLink profiles
independently link and execute startup-zero, signed active-view and full SaveRec
round-trip controls. Equal-total-size word elements, a shortened 16-byte owner
and a shifted SaveRec base are detected. All twelve links have clean diagnostics
and maps resolving all four consumer imports; emitted EXEs alone do not count.

The raw research receipt and executed tool identities remain unchanged. The
production source/type and whole-object guards verify the current generated
provider independently. No original executable or fragments enter compilation
or linking, no game implementation is stubbed, and no canonical source or
historical manifest is edited. Full-game execution, broader storage/layout
gates and human acceptance remain pending.

Root also accepts two independent signed `int far [6]` population work vectors,
`fd_50F6_0AEC` and `fd_50F6_0AFA`, twelve bytes each. Complete declarations,
CountAnts writes to all six indices, bounded direct consumers and the two
SaveRec `{2,6}` rows establish their extents. The control module's scalar
`fd_50F6_0AEC` read is the same object's element-zero view. The 156-source
census accounts for all 64 references and twelve complete reference-bearing
views; no additional ASM/numeric/interior view is found. Its older inventory
snapshot is observational provenance, not current mutable-report authority.

Both linkers pass the actual startup/typed/byte/SaveRec aliases and detect four
contrasts: equal-byte byte elements, a five-word subobject whose sixth access
overwrites its adjacent guard, a one-word shifted SaveRec base and count five.
Clean logs and resolved maps are required even for negative runtime cases.
The fresh runtime provider is the data-only two-array source; the separate
whole-module exact-search result is research provenance and is not promoted.
Unchecked raw saved population values remain the existing algorithm's domain,
and historical TU/order/placement is not claimed.
