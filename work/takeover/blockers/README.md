# Handover blocker follow-up (2026-10-01)

No game functions were accepted in this checkpoint. The thirteen series in index.json
record 909 whole-module variants for six remaining functions. Each uses the current
module's flags, placements, earlier claims and private-data gate through
autosearch.Evaluator. The compact verdict files retain failures, scores and source
hashes; the generators, first drafts and best-scoring whole-module drafts are kept.
Run generators from the repository root; they write only build/workers/blockers/.
Every retained draft is an unclaimed hypothesis. Merge into the current module and
run search.py and promote.py --verify-only before considering acceptance.

* S15 declaration controls include all real earlier prototypes and SYM-NAMES moves,
  including unnamed parameters that an older site filter missed. Pointer views,
  initializers and used keyboard/button/font intermediates still leave the same two
  stack-home operand bytes wrong in the 326-byte function.
  A final 133-variant control applies the existing USE-1/USE-2 folded-read idea to
  initialized handle, text, parameter, rectangle and result values. Standalone reads
  and combined conditional reads also leave the stack-home mismatch. These are
  STEERED diagnostic hypotheses, not new rules or original-source evidence.
* FindIndex's explicit three-way decision trees do not fix the existing branch residue.
* Window allocation's real return/count/index intermediates and typed window pointers
  do not reproduce its 132-byte original's stack and register choices.
* Tandy channel-expression controls test addition, casts, subtraction, assignment and
  CSE forms. The 120-byte OR/XOR variants still have one opcode byte wrong: the
  original uses ADD. Their value equivalence also requires a channel-range assumption;
  a lower score is neither semantic proof nor acceptance. tandy-cse-v14.c is retained
  only to explain the failed control, not as a replacement implementation.
* Memory compaction's fresh whole-module merge preserves all current accepted claims.
  The 490-byte near body still swaps six stack-home operand bytes. Its wide-result
  low-word view remains a hypothesis; no padded layout has been accepted.
* List/string pointer-update and increment controls still omit the original's dead CX
  reload. The near 156-byte body remains shorter than the 159-byte original.

validate.log records full validation PASS (all tests, 45 compiler rules and FAR_BSS
declaration probes); hybrid.log records the byte-identical hybrid PASS.
tests.log records a fresh 177-test run after the final tooling cleanup (two skips).
The manifest hash remains 3235d9b8161d865ceb0954ef0ef90fc69731c13255a75a20091747d112dac1b9.
Coverage is unchanged: 32 functions / 17,144 game-code bytes and 129 data bytes remain
unresolved. Historical-link evidence is in ../rtlink400/README.md.
