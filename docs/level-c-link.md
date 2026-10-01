# Independent historical link: current evidence and remaining proof

The goal is to build SIMANT.EXE from recovered sources, pinned historical libraries and
a recorded link script, with no original executable bytes used as build ingredients.
The exact circa-1991 RTLink/Plus toolchain is still missing. Exact function/module
verification remains available and is independent of that missing toolchain.

## Proof levels

* Module proof: compiled C or symbolic assembly reproduces original bytes, bound fixups,
  relocation sets and the required within-group/cross-function ordering. validate.py
  reports partial modules and complete TUs separately.
* Hybrid integration: tools/link.py places those contributions and copies explicitly
  labelled debt. The resulting hash equals the original. This proves integration and
  coverage accounting, not an independent rebuild.
* Independent whole build: all game objects/data and third-party runtime ingredients
  are available, and a historical linker derives the complete layout, relocations,
  vectors, section tables and executable headers. This has not been achieved.

Current validated coverage and proof-quality categories are in docs/progress.md.
The 17,001-byte RTLink debt total includes manager code/data and associated metadata;
it should not be confused with only the 15,131-byte manager code/data region.

## Installed tools and reproducible trial

C:\tools contains RTLink/Plus 4.00 (1990 DiscMaster distribution), 6.10 (1993 BBS
distribution) and RTLink for Clipper 3.11/3.13 (Clipper 5.0/5.01 disk archives).
Each has provenance and pinned identities;
none produces the original manager exactly. They are experimental instruments.
No tool binaries are committed. Search results: work/takeover/rtlink-search.md.
The 4.00 installer now completes with all checksums OK. Its stock RELOAD manager
uses 16-byte section records; SimAnt uses 18-byte records. Extraction, inventory
and paired trial reports are in work/takeover/rtlink400/. The exact original version
and matching manager distribution are still missing.

```
python tools/rtlink.py build/workers/NAME/rtlink --profile rtlink610 --jobs 6
python tools/rtlink.py build/workers/NAME/rtlink --profile rtlink610 --jobs 6 --reuse
python tools/rtlink.py build/workers/NAME/rtlink400 --profile rtlink400 --jobs 6
```

Trials use real complete-TU/data objects and clearly labelled synthetic stub objects
for missing code. They never promote anything. Their large stub byte count includes
partial modules whose complete object extent is unavailable, so it is not the validator's
unresolved-game-code count. Link inputs inferred from the original (ALWAYS/NEVER,
AREA/SECTION, PRELOAD/RELOAD) are labelled in work/rtlink/linkscripts/SIMANT_derived.lnk.
Stale collections are refreshed, and reuse requires source, gate-object and cached-object
hashes to agree. A gate failure is not written as a reusable object.

The latest paired 4.00/6.10 trials link with 99 real objects, 67 stubs (106,081 code bytes)
and one unresolved symbol, __acrtused. Of fourteen overlay images without trial code
stubs, thirteen relocation sets agree; only S21's order agrees and all raw images differ.
Raw byte differences include rebased fixup fields. This report is a diagnostic, not
an acceptance comparison or a claim that those complete images match independently.
The parser reads the linked manager's $$OVLPBLOCK pointers and record size, supporting
16/18-byte tables. It counts length differences and reports final unwritten paragraph
padding explicitly. RTLINK.CFG selects documented freeformat input for both profiles.

## Findings established by real-linker experiments

* Relocations are grouped by frame and target symbol. Group ordering uses a 101-bucket
  hash of the target's internal symbol-record handle, with most recent insertion first.
  The handle follows symbol creation while objects are read: PUBDEF creates immediately,
  an external at first FIXUPP reference, and an unreferenced external at object end.
  The chain position comes from the first relocating fixup. Names do not determine it.
  This supersedes the earlier name-hash hypothesis (kept in Git history).
* Clipper 3.11/3.13 share an ordering rule; 6.10 differs. None matches SimAnt's global
  ordering. The original linker and complete object set in historical input order are
  still required to reproduce it naturally. Original symbol spellings are not a blocker
  merely because an earlier hypothesis said the ordering depended on names.
* ALWAYS creates initial vectors in listed order; later vectors follow first reference.
  NEVER is needed for the original's direct references into S00-S03. The format matches.
  VEC-1 records the experiment and the inferred original lists separately.
* SimAnt uses the RELOAD manager ($$RTLOVLINITR, reload stack 0x1800, RELOAD FAR 400)
  and cache modules. Installed managers differ. Section record flags are the high byte
  of the three-byte file-position field: 0x05 PRELOAD+CACHE, 0x04 CACHE, 0x01 PRELOAD.
* CODEALIGN-1 is now installed: root:19A9 starts at 19A98; RETF stubs at 19A95-19A97
  belong to root:1986. Late MEMHOOK object root:2CFB is read in the library list after
  LLIBCR/LIBH. Its final address still depends on which runtime imports missing objects pull.

Detailed reproducible evidence: work/rtlink/findings.json and experiments.json,
work/vec/, work/align/FINDINGS.txt, evidence/codegen/CODEALIGN-1.json,
docs/codegen-rules.md VEC-1/DATAPTR-1, and tools/rtlink.py. Archived proposal patches
are historical and must not overwrite current tooling.

## What remains for the final binary proof

1. Recover the remaining game code and typed data through the strict module gate.
2. Obtain and pin a matching RTLink distribution/manager library; verify exact output,
   not version labels or similarity. Continue archival searches before assuming absence.
3. Close object/library input order, complete runtime pull-in, global relocation order,
   vectors, resident/far/BSS data placement, section tables and MZ headers.
4. Declare the 256-byte mastering tail as an external artifact with an independently
   identified source/append step; it is not ordinary linker output.
5. Resolve and disclose proof-quality debt (steered constructs, inferred declarations,
   pending order, FAR_BSS dimensions and runtime oracle-derived words) before freeze.

SDL3 does not require the DOS overlay linker. Port work needs recovered game behavior,
replacement of DOS video/input/audio/timing/storage interfaces, and behavioral comparisons
against the frozen original. The project's current working rule still keeps modern code
out of this tree until the historical freeze. A missing linker can be an explicit freeze
policy decision later, but no such exception has been authorized in this checkpoint.
