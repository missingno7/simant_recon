# Hard-tail checkpoint (2026-10-01)

This checkpoint adds diagnostics and bounded compiler probes. It accepts **zero new
functions**. Main is `54cb824d19c2f897ab17c8b163a954121d4e4843`; the manifest remains
`c2850fb5d252bd490bb9d0d2994e1463b25a5e6a4f187ed4f4730dcf91e2f4fd`.
The DOS game is not ready to freeze as an independently reconstructed oracle.

The 29 open functions contain 15,039 bytes. Full validation still counts 15,355
unresolved game-code bytes and 129 unresolved game-data bytes. The additional
316 code-span bytes are inventoried in `non-function-debt.json`: 246 currently
labelled LINK_FILL, 22 root code debt, 32 overlay code debt, and 16 text-prefix
bytes. This inventory changes no ownership or accounting policy. RTLink's 17,001
bytes remain separate and were not investigated in this wave.

## Evidence and state

`all-open.json` contains target/candidate full extents, ordered CFGs, normalized
instructions with physical placements, frames, observed BP access maps, register
use-site obligations, missing/extra instructions, branch and width differences,
fixups, relocation differences, strict peer/data verdicts, source hashes, exhausted
controls, and next hypotheses for every open function. `next-hypotheses.json` pins
20 non-laboratory hypotheses to observed instruction islands and offsets; check
the exhaustion index before treating those dimensions as untested. `catalog.json` selects
whole-module seeds; `seeds/` preserves them. Each selected seed passed the current
accepted-peer and private-data gates; none passed target equality. This gate
statement is not a substitute for semantic review of a proposed claim.

The initial fresh-main diagnostic compiled every open function before archive
selection. LessonDone's reviewed Boolean/shared-return seed was then rechecked
and selected: 727 bytes versus target 723, 64 versus 65 CFG blocks. Its earlier
739-byte baseline remains the source of the declaration-phase experiment. A
715-byte split-case variant has a weaker skeleton and was not chosen by size.

| Function | Target / candidate bytes | CFG | Normalized similarity | Diagnostic class |
| --- | ---: | --- | ---: | --- |
| f_0250_1018 | 646 / 648 | MATCH | 0.8142 | STRUCTURAL_TAIL |
| f_0250_129E | 264 / 265 | MATCH | 1.0000 | ALLOCATOR_TAIL |
| DrawBalloons | 1060 / 1053 | MATCH | 0.9399 | EXPRESSION_TAIL |
| SpiderScan | 392 / 389 | MATCH | 0.9809 | EXPRESSION_TAIL |
| LessonDone | 723 / 727 | MISMATCH | 0.8268 | STRUCTURAL_TAIL |
| f_171C_09CC | 144 / 146 | MATCH | 0.8955 | STRUCTURAL_TAIL |
| f_171C_0ADC | 262 / 260 | MATCH | 0.8641 | STRUCTURAL_TAIL |
| f_171C_0FBC | 566 / 568 | MISMATCH | 0.8213 | STRUCTURAL_TAIL |
| f_171C_0CF4 | 490 / 490 | MATCH | 1.0000 | ALLOCATOR_TAIL |
| FindIndex | 267 / 267 | MISMATCH | 0.9898 | CONTROL_FLOW_TAIL |
| f_1C62_0415 | 649 / 653 | MATCH | 0.9855 | EXPRESSION_TAIL |
| f_1E57_038E | 997 / 985 | MISMATCH | 0.9322 | CONTROL_FLOW_TAIL |
| f_20E8_0903 | 286 / 280 | MATCH | 0.9717 | EXPRESSION_TAIL |
| win_UnlockWin | 386 / 390 | MATCH | 0.9281 | EXPRESSION_TAIL |
| f_23E6_0000 | 159 / 156 | MATCH | 0.9839 | EXPRESSION_TAIL |
| f_2505_0453 | 132 / 124 | MATCH | 0.8148 | STRUCTURAL_TAIL |
| win_DrawBitMap | 663 / 675 | MISMATCH | 0.8750 | STRUCTURAL_TAIL |
| f_2815_0165 | 232 / 246 | MATCH | 0.8673 | WIDTH_TYPE_TAIL |
| f_284A_0138 | 25 / 25 | MATCH | 0.5000 | EXPRESSION_TAIL |
| f_29D6_000A | 120 / 116 | MATCH | 0.9074 | EXPRESSION_TAIL |
| o10_35F5_0384 | 1759 / 1746 | MISMATCH | 0.8648 | STRUCTURAL_TAIL |
| DrawMapCursor | 205 / 210 | MATCH | 0.7167 | STRUCTURAL_TAIL |
| InvertPatch | 261 / 260 | MATCH | 0.7100 | STRUCTURAL_TAIL |
| o15_384C_0239 | 326 / 326 | MATCH | 1.0000 | ALLOCATOR_TAIL |
| win_PrintStyleTextInRect | 1039 / 1035 | MATCH | 0.9688 | EXPRESSION_TAIL |
| DisplayCard | 1457 / 1457 | MATCH | 0.9785 | EXPRESSION_TAIL |
| drawHistGraph | 732 / 714 | MISMATCH | 0.8877 | STRUCTURAL_TAIL |
| o25_3BA4_1035 | 281 / 281 | MATCH | 1.0000 | ALLOCATOR_TAIL |
| o25_3BA4_1686 | 516 / 520 | MISMATCH | 0.8840 | STRUCTURAL_TAIL |

## Laboratory results and concrete compiler facts still missing

* **S15:384C:0239:** 137 instructions, 326/326 bytes, matching normalized skeleton
  and CFG. Only two displacement bytes differ: the text pointer's segment home
  is BP-2 in the candidate and BP-6 in the target. Both frames are 40 bytes.
  Top synthetic identifier counts 0..16 and unused automatic-array controls
  do not obtain the target home. The named `text` pre-C3 record and segment-store motif are unchanged in
  the tested same-line extern perturbation. `/Fc` puts named `text` at BP-4 and
  its live segment at BP-2. Split-pointer controls reproduce this base-plus-two
  relationship and encode their segment stores in pre-C3 PR. This is not proof
  of an unrelated anonymous spill. The target BP-6 could correspond to a whole
  pointer home at BP-8, or an equivalent coalesced home. The missing fact is the
  real declaration/context, ranking or coalescing change selecting that home.
  It is not evidence for another algorithm or for assembly.
* **S25:3BA4:1035:** 92 instructions, 281/281 bytes, matching skeleton and CFG.
  Only the LES/PUSH pair near the DigMyTile argument needs SI instead of BX.
  Other BX/SI uses already agree, so a global register rename would be wrong.
  The missing fact is the allocation/lifetime boundary of that pointer CSE.
  Identifier-count probes do not close it and several disturb accepted peers.
* **root:171C memory compaction:** the reviewed 490-byte wide-result seed remains
  intact. Six operand sites exchange BP-22 and BP-26; both frames are 38 bytes.
  Declaration-phase probes sometimes shrink the body to 488 bytes or disturb
  peers. The missing fact is the ranking/interference/coalescing of those two
  word values. Pointer-truncation drafts are excluded.
* **FindIndex:** target and seed are 267 bytes. The first discrepancy is a
  condition-tree/block-order choice: target JG to the upper update then JNE to
  the lower update; candidate JL to the lower update then JNE to the upper.
  Four explicit priority/continuation controls compile with peers/data intact
  but leave 17 differing bytes. The missing fact is the frontend condition-tree
  polarity and C2 scheduling rule that chooses the target block order.
* **root:23E6:0000:** 159/156 bytes, matching CFG, one missing instruction.
  The target reloads CX from BP-10 between `inc ax; add si,ax` and the counter
  increment. Both streams already use INC there. The earlier ADD-versus-INC
  description referred to a rejected control and is corrected in
  `probes/list-README.md`. Explicit segment reconstruction fails equality and
  sometimes peers. The missing fact is a real pointer-value/CSE lifetime that
  retains this reload; no compiler-exclusion proof exists.
* **root:284A:0138:** both bodies are 25 bytes, but the expression skeleton
  differs: the target zero-extends the first byte in AL then packs through CH/CL;
  the candidate uses AH. Volatile byte reads preserve the candidate lowering.
  An anonymous packed-member control regresses an accepted peer. Recover the
  byte-width/CSE graph before allocator work.
* **root:29D6:000A:** target 120 bytes, reviewed seed 116. Shift/multiply controls
  produce 118 bytes with relocation differences. The missing fact is the byte
  CSE/add graph that retains the target CX and ADD roles; an OR/XOR near variant
  depends on a channel-range assumption and is not accepted.

The allocator rule also applies diagnostically to root:0250:129E: its 101-instruction
skeleton matches despite a one-byte extent difference caused by register-specific
encoding. Its use-site substitutions are exported, with conflicting global maps
left explicit. No new causal declaration-context rule has been established.

## Compiler observation boundary

`../compiler-ir/` preserves C1 and post-C2 interception hooks and controls. They
use documented pass overrides, scratch hooks and read-only pinned compiler trees;
production compiler binaries and acceptance paths are untouched. Raw streams stay
under ignored build scratch. These are candidate-side streams; original compiler
intermediates are unavailable.

C1 EX preserves real expression changes and symbol identities. Tiny controls
identify several identity operands, but the S15 extern comparison still has 60
undecoded differences near branch/loop/switch/goto records. Full normalized IR
equality is therefore **unknown**, not asserted from partial token scanning.

Post-C2 PR contains named-local records. With `saved`'s name and far-pointer type
held constant, a real address-taken int moves its final home BP-4 -> BP-6 and a
name-relative PR byte changes FC -> FA. Rename/type controls and a long-local
allocation contrast bound the interpretation. This supports a tentative home byte
before C3; the adjacent byte changes too, and the record grammar and unnamed
split-pointer/CSE references remain undecoded. See
`../compiler-ir/c2/FINDINGS.md` and `home-delta-probe.json`. This is partial compiler
visibility, not a codegen rule or a proof that original and candidate IR agree.

A subsequent four-control split-pointer probe provides a narrower mapping:
the offset stays in SI across a call; the segment occupies BP-2/BP-4/BP-6, and
pre-C3 PR store/reload motifs carry FE/FC/FA. Whitespace preserves both PR and GS.
S15 has the corresponding FE store motif beside its named `text` record; the
tested extern context preserves it. See `../compiler-ir/c2/split-far-stream-analysis.json`.
These are probe-confirmed motifs, not a complete PR parser, and do not prove
anonymous ownership. The next useful step is tracing the source/context-to-home
allocation/coalescing decision selecting BP-8 for the whole pointer or BP-6 for
its high word. More broad source permutations without that decision would add
little information. Structural
functions still require their own condition/shared-tail/loop reconstruction; the
allocator observation does not establish a universal blocker for all 29 functions.

## Reproduction and acceptance boundary

Run from the repository root with the existing pinned toolchain:

```powershell
python tools/hardtail.py --triage --catalog work/takeover/hardtail/catalog.json `
  --out build/workers/NAME/report
python tools/hardtail.py S15:384C:0239 `
  --source work/takeover/hardtail/seeds/S15_384C_01b51eecedcd.c `
  --out build/workers/NAME/s15
python tools/compilerstate.py --spec work/takeover/hardtail/probes/s15-local-spec.json `
  --out build/workers/NAME/s15-local --ledger build/workers/NAME/ledger.jsonl `
  --prior-ledger work/takeover/hardtail/experiments.jsonl
python work/takeover/hardtail/probes/make_controls.py
python work/takeover/hardtail/probes/index_gate_recheck.py
python work/takeover/hardtail/inventory.py
```

A hardtail exit status of 1 means at least one strict target remains inexact. The
classifier cannot promote. GP/BP/branch/relocation normalization is diagnostic;
widths, addressing forms, byte lanes, instruction placement/counts, calls, table
extents and CFG edges remain available. The CFG is ordered and conservative, not
a source-independent graph-isomorphism proof. Dense word tables are recognized
only by the guarded MSC dispatch pattern and validated destinations; table bytes
remain in strict extent/fixup checks. Undecoded or unknown indirect structure yields
UNKNOWN, never an assumed match. Declaration-context classification requires a
causal probe; POSSIBLE_ASM requires positive compiler-exclusion evidence.

`experiments.jsonl` retains 102 current harness rows and all 101 unique whole-module
inputs in `experiment-sources/`. It records source/context hashes, dimension and
parameters, compile status, size delta, strict differences, peer/data regressions
and available diagnostic metrics. Fifty-one early rows have explicit diagnostic
errors from an earlier tool bug; their strict gates remain recorded, and allocator
metrics are not invented retroactively. The current all-open analysis has those
metrics. List-worker controls use a separate schema in
`probes/list-compilerstate-experiments.json`; these and historical archive rechecks
are not counted as new exact results. Synthetic declarations and frame reservations
are diagnostic only and cannot be promoted.

`exhaustion-index.json`, `archive-audit.md` and `archive_audit.py` associate archived
reports by exact function IDs and inspect generator parameters. The audit corrects
misassigned balloons, map-draw and ant-helper series and adds omitted compaction and
other controls. It describes retained tested values, not exhaustive dimensions or
unarchived objects. Before a new compile, check this index and the JSONL ledger;
`--prior-ledger` deduplicates identical source plus pinned module context.

Continue to use context -> whole-module drafts -> search -> promote --verify-only
-> promote. No diagnostic synthetic context may enter a proposed claim. Bytes,
extents, symbolic bindings, relocation sets/order, peers, private data and semantic
review remain mandatory. No acceptance code or canonical source changed here.
Validation and hybrid logs are preserved in this directory. The hybrid verification
uses retained accepted objects (`link.py --reuse`); it remains byte-identical at
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11` and still copies
explicit debt. It is not a historical whole-link proof or a freeze.
