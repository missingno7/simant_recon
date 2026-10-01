# Phase-index recovery and memory-context repair (2026-10-01)

CalcScore is accepted: 1,169 bytes, 61 fixups and 18 relocations, with grouped
relocation order. S14:384C is now a complete 4,653-byte TU (384C0:396ED), with all
11 functions, 158 private-data bytes and grouped cross-function relocation order
exact. `score-search.log`, `score-promote-verify.log` and `score-promote.log` retain
the acceptance loop. `score-accepted.c` is the promoted snapshot; `sources.json`
pins the retained sources. Canonical ownership was written only by promote.py.
The subsequent tidy-only promotion is retained separately; it preserves every
claim and the complete extent. `validate.log` records the fresh full test run
with two skips and 46 reproduced compiler probes. `validate-final.log` checks
the final source with those tests already passed. `hybrid-final.log` is the
fresh final-manifest image check. No tools or test implementations changed.

## CalcScore: separate used indices, then repair later context

The prior draft used one `j` across the history computation and both matrix
scans. Its listing placed `j` with `score` at BP-6 and `sum2` at BP-4; the
operand correspondence was inconsistent across phases. A distinct block-local
history index reproduces the original allocation: historyIndex and later j at
BP-4, sum2/score at BP-6. Both variables perform real work and are initialized
before use. The history index still supplies the same second-score denominator;
the later j is initialized by each matrix loop. No artificial read or padding
local is added. Existing unused t is retained from the earlier canonical draft.

The scoped form alone matches CalcScore but changes PictureDialog and grows
the complete module by one byte. Removing one real prototype parameter name
after CalcScore repairs that compiler context. The selected source declares
`f_00F8_02F7(int)`; its type and call behavior are unchanged. Numerous other
single-parameter prototypes also work. A matrix-local j block is another exact
target alternative. Both a shadowed j and the clearer historyIndex name match.
These alternatives do not prove original spelling or exact block placement;
the accepted claim is explicitly layout-inferred, not STEERED.

`score-phase-homes.json` records 11 whole-module controls (two target matches,
both with peer regression). `score-peer-repair.json` records 45 controls; the
mixed named/unnamed parameter variants that MSC rejects are compilation
failures, not compiler exclusion. `score-reviewed.json` records both tidy
spellings with all peers/data exact. SCOPE-1 preserves three full-module
compiler probes: shared index negative, scoped target positive with peer loss,
and the complete accepted context. Its segment lengths distinguish the peer
regression (4,654 bytes) from the accepted 4,653-byte TU.
Twenty-six of the peer controls compile and 25 pass the entire pre-promotion
module gate. The single compiled failure is the scoped baseline with all
prototype parameter names retained.

## Memory compaction: the broken starting draft is repaired

Prefer **memory-near-repaired.c** for subsequent f_171C_0CF4 searches. It preserves
every accepted memory-module peer, including f_171C_2086 at its original 92 bytes,
and all three private-data contributions. The compaction target is still
inexact: 490 bytes with six moved-flag/segment stack-home operand differences.
It is an unclaimed source hypothesis; its wide moved flag and low-word return
view are not established original types. `memory-search-strict.log` and
`memory-promote-refused.log` retain the strict target failure and whole-module
refusal. It must not be promoted until the residue is exact.

The 32-subset bisection plus old near control in `memory-bisect.json` isolates
the accepted-peer regression to declaration history. Adding real used segment
and type caches but removing the canonical used nb alias changes the symbol
count by one and reproduces the 88-byte peer. Net changes of zero or two keep
that peer exact in this series. Address width and moved-flag width alone do
not cause the peer regression. This is evidence for the known context effect,
not a new universal modulo rule.

Eight real used alias alternatives restore the peer. The selected draft
restores `nb = b` before assigning the found block's size, then uses nb for
the copied block's fields, copy destination and handle update. It is the same
block pointer; no dummy declaration is added. The six target differences are
unchanged. `memory-alias.json` records the broken baseline and eight repairs.
Eighteen flag-storage/read alternatives also fail (`memory-flag-storage.json`).

The guarded search runs from the repaired draft: DECL-SWAP, STMT-SWAP, EMBED,
PROTO-NAMES; neutral beam 16, depth 3, budget 240, level cap 90, six jobs.
It checks 197 variants / 22 target code identities without breaking an accepted
peer or data contribution, and finds no exact target. `memory-search.json`
and `memory-tried.json` retain its results. No acceptance gate was changed.

## S15 negative controls

MSC 6.00 and real-mode 6.00A reproduce the same two operand-byte residue as
MSC 6.00AX. All seven accepted peers and both data contributions pass.
`s15-600.json` and `s15-600a.json` retain the full verdicts.

Further full-module controls all fail: 28 font-width/pointer/phase-scope
compiles, 17 parameter-result/key-local compiles, and 13 rectangle-address
compiles including their baselines. Explicit near/far rectangle pointers add
code rather than reproduce the text segment's BP-6 home. The current residue
still maps the text segment from candidate BP-2 to original BP-6 at two uses.
These failures do not establish assembly or exclude compiler output.

## Reproduction and next work

Generators write scratch beneath build/workers/context_next and run from the
repository root. The CalcScore generator reads the preserved shared-index
seed because canonical S14 has since changed. Re-running negative controls
against the current manifest also checks its new complete-TU extent and its
now-accepted CalcScore claim; retained reports describe the pre-promotion
claim set. The pinned SCOPE-1 probes remain directly reproducible with
`python tools/probe.py evidence/codegen/SCOPE-1-score-phase-index.json`.

Continue with focused S15 pointer-segment lifetime/context and repaired memory
flag/segment-home recovery. CalcScore is finished. Keep RTLink as separate
independent-link debt. Validation and fresh byte-identical hybrid transcripts
are retained here at the checkpoint; the generated progress report has totals.
