# Handoff: state and next steps (2026-10-01)

Read README.md, AGENTS.md, docs/codegen-rules.md and docs/tu-evidence.md before work.
`python tools/validate.py` is the source of truth for totals (docs/progress.md/json).
The latest phase-index checkpoint accepts CalcScore and completes S14:384C as a
4,653-byte TU. It also repairs the memory-compaction starting draft's accepted-peer
regression. Findings, compiler controls and verification transcripts are in
work/takeover/context-next/. The earlier sibling-tool comparison remains in
work/takeover/siblings/; its 203-test checkpoint preceded this acceptance.
The fresh full validation passes the unit tests (two skips), all 46 compiler
probes and module/FAR_BSS checks. The final-source recheck and byte-identical
hybrid transcripts are retained with this checkpoint.
Check Git for the current checkpoint and publication status.

## 1. Reconstruction state

| Measure | Validated value |
|---|---:|
| exact C functions / bytes | 1,242 / 236,901 |
| genuine symbolic assembly / code-segment data | 50,441 / 1,481 bytes |
| ASM used as a workaround for C | 0 |
| complete TUs / with proven cross-function relocation order | 95 / 94 |
| accepted MSC runtime | 90 members; 12,339 code + 2,021 data bytes |
| accepted game data / far data | 113,884 / 80,310 bytes |
| unresolved game code / data | 15,975 / 129 bytes |
| RTLink manager and associated metadata debt | 17,001 bytes |
| owned functions / known functions | 1,699 / 1,730 |

Proof quality is separate from coverage: 14,115 C bytes are STEERED, 20,601 are
layout-inferred, and 11,742 have within-group order pending. S00:31AD is the only
complete TU whose cross-function relocation order remains pending. FAR_BSS contains
19,408 zero bytes, but 14,928 bytes still have unverified declaration sizes. The opaque
data lint reports 6,397 bytes and includes false positives from typed numeric tables.
See the generated report for the full categories; these are not a historical freeze.

`python tools/link.py --reuse` produces a byte-identical **hybrid** SIMANT.EXE
(SHA-256 `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`).
It places compiled contributions and copies explicitly labelled debt from the original.
That proves placement and integration, not a fully independent reconstruction.

## 2. Accepted changes in the takeover checkpoint

* S14:384C is now a complete 4,653-byte TU, with grouped cross-function relocation
  order. CalcScore's distinct used history index resolves its 12-byte stack-home
  residue; an unnamed real later prototype parameter restores PictureDialog's
  compiler context. SCOPE-1 records the whole-module positive and negative controls.
  CalcScore is layout-inferred: alternative scope placements and parameter-name
  removals also match, so the original source spelling is not claimed.
* root:295C is now a complete, original-order TU with `/Zi`. The final 75-byte MIDI
  function matches through a folded unsigned-byte range expression; it is explicitly
  STEERED because its eliminated expression is unknown. CSE-1 records the controls.
* CODEALIGN-1 is installed and reproduced. The three RETF stubs at 19A95-19A97 now
  belong to root:1986; root:19A9 starts at the WORD-aligned 19A98. The old complete
  extent was released and replaced through promote.py, with journal entries.
* S04:35F5 is a complete TU: DrawMiniMapCursor's coordinate statement order now
  reproduces all 150 bytes and relocation evidence naturally.
* S09 owns the 2,464-byte saved-state descriptor table: typed size/count/symbolic-pointer
  records, 307 pointer relocations, no absolute-address capsules. Target-only extern
  declarations remain type hypotheses. Existing S09 code/data claims rechecked exactly.
* S05:3663 is now a complete TU with 744 exact code bytes and 112 data bytes.
  DoExpMenu reads the event low byte through an unsigned-char lvalue; BYTE-1 records
  the one-CMP-byte word-mask contrast. Its WORD-aligned start is 36634, immediately
  after the preceding proven contribution, rather than the paragraph frame base.
* The pinned MSC `syserr.c` member contributes 462 data bytes, grounded by two registered
  publics and all 38 pointer relocations. `promote.py --runtime-data syserr.c` is the
  single-writer acceptance route; verification and negative anchor tests are installed.
* root:0250 DrawCurBalloons now matches 1,680 code bytes, fixups and relocation sets.
  Moving its real drawing-callback declaration earlier supplies the declaration context;
  within-group relocation order remains explicit debt. The other four bodies stay scaffolded.
* S23 win_GetStyleTextHeight now matches 455 bytes and relocation order. Natural nested
  conditions and declaration placement reproduce the compiler result. Bringing the real
  DisplayCard loader/locker prototypes earlier preserves the other six accepted claims
  and all four data contributions; no dummy identifiers were accepted.
* root:0250 DrawSpider now matches 1,433 bytes, 132 fixups and grouped relocation order.
  Moving two real variable declarations before 1018, assigning rectangle left before top,
  and using conditional image-mode calls reproduce the stack homes and AX selector.
  The module's other 49 claims and all private data remain exact; no assembly or dummy
  identifiers were introduced. Three other bodies remain scaffolded. Controls are in
  `work/takeover/spider/`; the latest acceptance validation passes all 38 probes.

* S08 RandWorld now owns 1,355 exact code bytes, bound fixups and relocation sets.
  Literal boundary-column indexes remove the old dead y store; the first-loop zero
  expression is explicitly STEERED because its eliminated original source is unknown.
  ZERO-1 records the positive and four-byte-longer literal-zero negative control.
  All prior 17 claims and both data contributions remain exact. Within-group relocation
  order is pending; complete-TU trials under Zi and Zd were refused, so S08 remains
  partial. Controls and refusal transcripts are retained in `work/takeover/randworld/`.

* root:2815 owns the 36-byte instrument setter. Splitting the earlier scaffolded
  volume and instrument-pointer reads establishes the required private segment-word
  order (CONST-1). The earlier volume function remains unclaimed. Positive and
  negative whole-module controls are in `work/takeover/adlib-setter/`.
* root:290D is a complete TU after recovering the 138-byte sample-delta decoder in
  natural C. Native right shift, counter initialization order and removal of the
  draft's unused padding variable reproduce the code without inline assembly.
  The extent starts at 290DE after the preceding contribution ends at 290DD and
  a one-byte WORD-alignment fill. Controls are in `work/takeover/delta/`.

* S25 DoAntMoveY now owns 1,990 exact bytes. USE-1 records the folded unsigned
  attribute read that reproduces address-taken local stack-slot ranking; it is
  STEERED because the original eliminated expression is unknown. All 12 earlier
  claims and private data remain exact. The changed object record boundaries leave
  2,458 additional earlier S25 bytes with within-group order pending; that proof
  debt is counted separately from byte coverage. Controls: work/takeover/antmove/.
* root:293A is a complete TU at 293A6:295CA after the 171-byte MPU polling body.
  LIFE-1 records its STEERED folded success-flag read. Two inferred continuation
  labels reproduce the CodeView object record breaks; all nine functions, private
  data and complete-module relocation order pass. Controls: work/takeover/mpu/.

* S09:35F5 is now a complete TU at 35F50:36EEA after recovering FileSelect's
  2,405 bytes, 159 fixups and 94 grouped relocations. USE-2 records combined
  STEERED folded path, save-mode and index reads; the eliminated original source
  expressions remain unknown. All six functions, four data contributions and
  complete-module relocation order pass. Whole-module controls and latest
  validation/hybrid evidence are in work/takeover/fileselect/.

* root:171C owns the 362-byte free-block function f_171C_0160. A word segment
  plus an unsigned-long paragraph count reproduces DX in its second address sum;
  the default long-segment control uses CX and differs at two operand bytes.
  WIDTH-1 records both equivalent-value expressions and their whole-module controls.
  All 57 claims and the DATA/CONST/BSS contributions pass. Four memory functions
  remain scaffolded; the module is partial. The full 45-probe/test acceptance and
  hybrid transcript are retained in `work/takeover/freeblock/`.

* S13:384C owns DrawColonyBars's 490 bytes after natural rectangle-field staging
  and a used coordinate intermediate. All 23 claims, CONST (114 bytes) and DATA
  (206 bytes) pass, including grouped relocation order. InvertPatch is the only
  remaining scaffold in this module. The full test/45-probe validation and fresh
  hybrid pass are retained in `work/takeover/colony-bars/`.

Tooling fixes are also installed: promote --note/--drop-extent, alignment diagnostics,
ASM probe variants, complete autosearch enumeration (including aliases and in-place
drafts), and continuation from preserved best files. Search verdict caches now include
module metadata, registries, manifest, toolchain and acceptance-gate fingerprints.
RTLink trials refresh stale collections and verify source/object hashes before reuse;
gate-failing objects are not cached. Historical work/align scripts have corrected paths.
Do not apply their archived whole-file patches to the current tools.

Sibling-inspired diagnostics (`tools/diag.py`, `tools/mismatch.py`) now group fully
bound BP/register/branch differences without affecting acceptance. Autosearch exposes
`--neutral-beam` and protects every existing manifest claim, rejecting broken starting
drafts. The older memory near draft breaks accepted f_171C_2086 (88 vs 92 bytes).
The new work/takeover/context-next/memory-near-repaired.c restores a real used nb
alias and preserves every accepted peer/data contribution; its compaction target
still has six stack-home differences and is unclaimed. Prefer that baseline.
See work/takeover/siblings/README.md for the four-project comparison and
work/takeover/context-next/README.md for the declaration-history bisection and repair.

## 3. Remaining game code

User priority: finish and verify the remaining game code first. Close the 129 data bytes
alongside relevant modules when convenient. Linker debt is a separate side task and must
not interrupt reconstruction. The authorized Luna xhigh archival search completed,
including the 2,804-archive PC-SIG 1991 ZIP-catalog inventory. Retained findings are
under `work/linker_hunt/`; the RTLink 4.00 candidate is now extracted and tested
(see section 4). It does not match the original stock manager format.

There are 31 known unowned functions, all represented by whole-module drafts,
including hard register, stack-slot, CSE, declaration and control-flow residues.
Preserved earlier surveys: work/resI/survey.txt, work/resJ/residue.txt,
work/autosearch/results.md/json. Current takeover scratch and search state:
`work/takeover/full-search/results.json` and preserved whole-module snapshots in that
directory. Ignored incremental logs remain under `build/workers/takeover/`.
`work/takeover/residue-controls/` retains later negative searches and the exact
free-block and colony-bar results, including warnings about semantically unsound old temporaries.
Read the timestamp and base path before continuing;
reports of a newly accepted function are historical and must not be promoted again.

The later residue-control index now retains 181 series / 7,203 recorded variants,
including four already accepted free-block alternatives and two exact colony-bar
alternatives. Other later candidates remain unclaimed. Memory compaction's reviewed flow and typed next-block sum
have a 490-byte draft with six stack-home bytes still wrong; its wide-result
low-word view is a hypothesis, not acceptance. The question-dialog draft has
scalar coordinates and separate loop counters, but remains 653 vs 649 bytes.
The corrected text-rendering cache updates on every space-loop iteration and
remains 1,035 vs 1,039 bytes. See the retained README for sources and failed controls.
Avoid the older generic text-cache draft: it never updates the cached character
inside its loop. Avoid padding a segment union with an unused member to explain
the compaction frame; the near result does not justify that layout.

The blocker follow-up retains another 13 series / 909 whole-module variants in
`work/takeover/blockers/`. All fail acceptance. They cover full S15 declaration
contexts (including previously missed SYM-NAMES moves), S15 storage/initializer/live
key locals, FindIndex decision trees, window-allocation intermediates, Tandy channel
CSE/addition/subtraction/argument forms, fresh memory-compaction views and split list
pointer updates. The 120-byte Tandy OR/XOR control still differs at the ADD opcode;
its value equivalence requires a channel-range assumption. Read the README's semantic
cautions before reusing its near draft. These failures do not establish assembly.
A final 133-variant S15 control of the existing USE-1/USE-2 folded-use idea also
fails; standalone and combined conditional reads of initialized locals do not
reproduce the missing stack-home placement.

FindIndex's retained negated lower-bound predicate (`findindex-conditional-forms-v16.c`)
is 267 bytes and differs only at the first conditional jump and its destination
(three bytes). It is still unclaimed: related Boolean forms, explicit predicates,
bound updates, optimizer controls, real record tags and prototype parameter removals
do not reproduce the original first `JG` while retaining its later `JNE`/`JL` branches.
S10 key-variable reuse, further graph declarations, staged MIDI word assembly, separate
clip-pass result pointers, memory-helper pointer lifetimes and EnterNest argument
pointers also failed. These controls do not establish assembly or compiler exclusion.
Later corrected prototype controls include every earlier real prototype, rather than
only the target's callees. Wider map indices, combined card base/title lifetimes and
handle types, compaction segment types, resize return flags, graph scale definitions
and K&R function definitions also remain inexact. The original-style K&R controls
compile to the same candidate bytes. InvertPatch's experimental int-return definitions
conflict with its earlier void prototype; those failed rows are not compiler exclusion.

| Module | Principal open work |
|---|---|
| root:0250 | 1018, 129E, DrawBalloons; natural identifier and statement evidence; DrawCurBalloons order debt |
| S25:3BA4 | 1035, 1686; register/slot residues; continuation must retain the original ownership gate |
| S10:35F5 | 0384; expression and parameter-copy structure still open |
| S23:39C7 | PrintStyleTextInRect, DisplayCard; register/storage and declaration evidence |
| root:171C | 09CC, 0ADC, 0CF4, 0FBC |
| others | S12 cursor, S13 InvertPatch and small root/S15/S17/S24 residues |

Run rule-driven searches from whole-module best drafts, then inspect aligned disassembly
for the remaining differences. Win16 is semantic evidence only; use verified naming
decisions. Its old build/lift/open paths no longer exist; maintained probe/source paths
must be located again. Do not accept a smaller distance as an exact result.

## 4. Independent historical link

The exact circa-1991 RTLink/Plus distribution is still missing. C:\tools contains
RTLink/Plus 6.10 and Clipper editions 3.11/3.13, all with provenance and pinned identities.
The independent Luna search also found a six-part RTLink/Plus 4.00 distribution:
`C:\tools\RTLink-Plus-4.00-DiscMaster\RTLINK40.ZIP` (SHA-256
`065cc748274addd3ac6f4aca314e67305e5f9a05758dee9b9cf76a19de5c69d5`).
Its DAT payloads were extracted by the checksum-verifying vendor installer under
headless DOSBox-X, with only scratch mounted. The clean DOS/source/docs/examples
installation contains 181 files. The pinned rtlink400 profile is installed under
`C:/tools/RTLink-Plus-4.00-DiscMaster/installed/dest`. Its library contains the RELOAD
manager and its source, but the stock manager uses 16-byte section records rather
than SimAnt's 18-byte records; its intercept offset also differs. No standalone
4.01 or 5.0 copy was found. Extraction, inventories, hashes and trial reports are
retained in `work/takeover/rtlink400/`.
Archive coverage and retained download identities are in `work/linker_hunt/inventory-search.md`.
The manager bytes and global relocation group ordering differ from the original.
Search evidence and contemporary version references: work/takeover/rtlink-search.md.
The 4.x/5.0 family is a search hypothesis, not a confirmed exact version number.

Latest trials (`build/workers/blockers/rtlink400-trial` and `rtlink610-control`) both
link successfully: 99 real objects, 67 explicitly labelled stubs (106,081 code bytes),
and unresolved `__acrtused`. Fourteen overlay images have no trial code stubs;
thirteen relocation sets match, only S21's order matches, and all raw images differ.
The trial parser now follows $$OVLPBLOCK's pointers and 16/18-byte record size, with
explicit image lengths and final partial-paragraph reporting. RTLINK.CFG sets the
documented freeformat syntax for both profiles. This is diagnostic output, never
acceptance. MEMHOOK is read in the library list; its address can still shift because
incomplete objects pull a different runtime set.

The linker does not block exact module recovery. It blocks the final independent
whole-EXE proof. SDL3 has no technical dependency on RTLink; remaining game semantics,
DOS hardware replacement and behavior verification matter to the port. The project
still requires a historical freeze before modern/port code enters this tree.
See docs/level-c-link.md for the proof requirements and the current linker findings.

## 5. Remaining data and declarations

Only 129 data bytes remain unresolved. Small palettes, bitmasks and state words have
ambiguous ownership or incomplete typed declarations (DGROUP 2100, 2328, 56FE, 5A28,
5A96, 60B0, 68AC, 79F0); a 12-byte far paragraph gap and tail bytes are also explicit debt.
Do not turn a plausible owner or apparent fill into acceptance without positive and
negative evidence. The large save table and syserr.c range are already accepted.
FAR_BSS sizes: 180 bytes pinned, 4,300 consistent, 14,928 unverified (tools/farbss.py).

## 6. Repository layout

`work/` keeps cited reproducers, earlier best drafts and research notes (work/README.md).
Archived proposals there may already be installed or superseded. `build/` is ignored
scratch and generated output; new workers use build/workers/NAME/. Preserve useful
unclaimed best drafts deliberately before deleting scratch, with flags and gate results.

## 7. Operating rules

* Canonical sources/manifest have one writer: promote.py. Registries use rename.py,
  symbols.py/functions.py. Draft whole modules in scratch, in original function order;
  same-module unrecovered callees stay scaffolded. Complete TU requires --extent and no scaffold.
* Loop: context.py -> whole-module draft -> search.py -> promote --verify-only -> promote.
  Validate at acceptance/tooling boundaries, not per hypothesis. Never patch objects,
  copy original code capsules, trim extents, mask fixups or hand-edit manifest/journal/oracle.lock.
* Names: Win16 CONFIRMED/HIGH or reviewed two-anchor decisions; DOS-1 applies only to
  identifier-shaped diagnostics from the DOS function itself. Assembly needs ASM-1 evidence.
* Git Bash: MSYS_NO_PATHCONV=1 for /AL-style flags. Never kill unowned processes; DOSBox
  and other Python work may belong to another project. Git requires the per-command
  safe.directory=D:/Prog/simant_recon setting under this sandbox account.
* User decisions (2026-09-30): genuine exact assembly counts as finished; C workarounds
  stay separate; acquire historical tools with provenance in C:\tools; pushing is allowed.
  Commit only on validation PASS and recheck the hybrid at the checkpoint.
