# Saved scalar word v19 source review

Status: `ROOT_REVIEW_PENDING_UNADMITTED`. This is a natural source-functional storage candidate, not a historical COMDEF identity or placement claim.

The one classified row is `_fd_50F6_0354`, a two-byte signed `int far` scalar. The full pinned graph has 127 canonical TUs plus all 29 strict effective sources (156 unique files); all 13 exact identifier hits match the source inventory. The current build report is used only to confirm that this name remains missing.

`o09_35F5_0D7A` sets the latch before `RandYard` while preparing to load a saved game. `NewGame` and `XferPatch` also set it. `CountAnts` reads it in both caste-completion guards and clears it after recomputing the population counts. The S09 SaveRec table has one `{2,1,&fd_50F6_0354}` row; generic `LoadGame`/`SaveGame` I/O uses `p->count * p->size`, so this view carries two bytes.

The only address escape is the SaveRec row. All source declarations are signed `int far`; the registry has only the candidate's exact base spelling and no registered interior. No numeric, assembly, pointer-array, aggregate, or mixed-width storage view was found. The separate `int far` definition is in [saved-scalar-words-v19.c](providers/saved-scalar-words-v19.c).

The source-supported storage type/extent does not establish a legal value domain or a universal scheduling/lifetime rule: raw save payloads can replace the word. Original COMDEF-producing TU/order, FAR_BSS ordering, padding, and absolute placement remain unknown.

Machine-readable source receipts and all 156 source pins are in [source-review-v19.json](source-review-v19.json). The latest runtime result is recorded there after the probe completes.
