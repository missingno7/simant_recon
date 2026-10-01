# Cache lookup acceptance and bounded fleet controls

The 2026-10-01 checkpoint accepts `ch_LookUpId` (354 bytes) and completes
`root:1A96` at `1A96C:1B058` (1,772 bytes). All eleven functions, DATA (112 bytes),
BSS (2 bytes), and complete-TU grouped cross-function relocation order pass.
The source is natural C; no new STEERED or layout-inferred bytes were added.
There are now 1,244 exact C functions / 237,521 bytes and 29 unowned functions.

## What resolved the cache blocker

The preserved draft used `&base[i]` in both probing phases. Explicit `base + i`
initializers in both phases change MSC 6.00's register and frame allocation and
remove the five-byte excess. The hash assignment must also store `start` before
`i`: `i = start = hash`. Reversing those stores leaves two wrong BP operands.
These expressions have equivalent C values, but the compiler does not emit the
same code in this module context.

The rotated list worker found the candidate. Parent review identified that its
starting draft already reversed the chained assignment, then independently ran
all eight combinations of assignment order and the two pointer initializers.
Only `fleet_root/lookup-controls/007_chain1-first1-wrap1.c` matches. Every row
preserves all ten accepted peers and private data. Search and verify-only passed
before the parent promoted the whole module with its complete extent.

[PTR-1](../../../evidence/codegen/PTR-1-cache-probe-pointer-add.json) pins four
whole-module compiler controls: both additions, either addition alone, and
reversed stores. All fourteen expectations pass. The rule describes this
context; it does not claim that addition is universally preferable to indexing.
`lookup-accepted.c` is the accepted source snapshot. The search, slot diagnosis,
extent verification, promotion and probe transcripts are under `fleet_root/`.

## Tooling and source-order repairs

`diag.py` now reports the full candidate extent separately from the compared
bound payload. A longer candidate formerly displayed a target-sized prefix as
its length. Acceptance already rejected the full extent, so this repairs the
diagnosis without relaxing the gate. Bitmap drawing now correctly reports
675 versus 663 bytes, with an explicit incomplete-tail annotation. Four tests
cover longer, shorter, equal and existing terminal word-alignment cases.

The canonical bitmap module had two wrappers before their callee, contrary to
the original function order. The parent restored that order through
`promote.py`, preserving all three accepted peers and DATA (106 bytes).
`win_DrawBitMap` remains scaffolded and unclaimed; there is no new bitmap
coverage or complete extent. The repair transcripts and resulting snapshot
are retained here.

`tooling/triage-before-acceptance.json` is a fresh survey of the thirty open
canonical drafts before cache acceptance. It is not a survey of every preserved
best source: for example, the separate 490-byte memory-compaction draft remains
the appropriate residue seed. Do not replace a better archived seed with this
canonical survey's candidate merely because the survey is newer.

## Fleet results

Seven authorized Luna xhigh workers searched disjoint scratch directories with
at most two compiler jobs each. Two workers rotated after exhausting their
initial bounded hypotheses. The parent alone performed canonical promotion.
The retained index records 237 source-gate rows, including repeated baselines
and historical reproductions; 236 compiled, and one target matched. Four pinned
PTR-1 probe variants and diagnostic/search rechecks are counted separately.
Fourteen compiled rows regress accepted peers and nine regress private data;
those rows are rejected. The one uncompiled SpiderScan row is a source-generation
error, not evidence excluding compiler output.

| Target / work | Recorded rows | Result |
|---|---:|---|
| SpiderScan aggregate and real argument lifetimes | 34 | 33 compile; aggregate seed retains 24 BP-displacement differences |
| S15 draw/text argument lifetimes and split phases | 53 | No exact result; closest two-byte residue remains |
| FindIndex decision flow and upper boundary forms | 24 | No exact result; 9 private-CONST failures |
| root:23E6 list helper register, huge-pointer and assignment forms | 23 | Missing segment reload remains; 2 peer failures |
| Three root:171C memory-helper lifetime pairs | 6 | No exact result; all 57 accepted peers and private data preserved |
| S25:1035 field/value lifetimes | 6 | Two BX/SI operand differences remain |
| root:1C62 question dialog argument/result lifetimes | 13 | No exact result; 10 peer failures |
| LessonDone switch, return and time-lifetime forms | 27 | No exact result; case-9 split reproduces a historical failure |
| Bitmap real argument lifetimes and word views | 43 | No exact result; peers and data preserved |
| Parent cache lookup factorial controls | 8 | One exact 354-byte candidate, subsequently promoted |

Read individual worker reports and `index.json` before repeating a series.
The LessonDone listing includes all 56 embedded switch-table words; none was
masked or omitted from acceptance. A shorter candidate or smaller residue is
not a recovered function. These negative series do not establish assembly.
Invalid splices from the rotated cache worker's exploratory generator are not
retained as compiler evidence; the parent's eight complete controls supersede them.

The next useful work is a bounded set of expression/address-form controls grounded
in a remaining function's listing or Win16 semantics. Keep statement/store order
as an independent factor when expressions interact. Rotate when there is no new
source hypothesis; repeating the lifetime series here is unlikely to help.

## Validation and reproduction

`fleet_root/validate-final.log` records full validation PASS: every accepted module,
214 test cases (two skips), all 48 compiler probes, runtime and FAR_BSS checks.
`fleet_root/hybrid.log` records a fresh byte-identical hybrid rebuild; the later
`hybrid-recheck.log` reconciles every contribution against the newly generated
progress totals. Manifest SHA-256:
`c2850fb5d252bd490bb9d0d2994e1463b25a5e6a4f187ed4f4730dcf91e2f4fd`.
Hybrid SHA-256:
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`.
Explicit debt is copied from the original by that harness; this is not an
independent historical link or a historical freeze.

Generators retain their `build/workers/fleet_NAME/` destinations. To replay one,
copy its archived worker directory to that scratch path and run the documented
commands from the repository root. Use each series' frozen seed rather than
current canonical sources. The archived SpiderScan and cache generators were
adjusted to read their frozen seeds; their pin notes record that change. Never
apply these snapshots directly to `src/`; use the normal promotion workflow.
The current cache module already owns its claim and extent, so the seven negative
cache controls now fail those existing gates as expected.

`sources.json` pins every retained text artifact as UTF-8 with LF newlines and
one trailing newline. Worker reports retain hashes from the original scratch
files; optional `source_sha256_lf_before_archive` pins distinguish whitespace
normalization. Transcript lines have trailing whitespace removed. Archived
result JSON drops bulky compiler logs and warnings while
preserving gate verdicts and identities, so its hash differs from the original
report's hash. Use the archive pins for integrity checks. Compiler objects,
caches and regenerated diagnostic JSON are derived output and are not archived.
