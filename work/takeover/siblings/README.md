# Sibling tools and blocker controls (2026-10-01)

No game function was accepted. Coverage remains 32 open functions / 17,144 code
bytes and 129 data bytes. Canonical sources, manifest, oracle lock and promotion
journal are unchanged. This checkpoint fixes diagnostic and search blockers.

## Sibling findings

| Project | Evidence inspected | Applicable method |
|---|---|---|
| Stunts | `tools/diagnostics.py` and its tests; `tools/pass_environment.py`; `evidence/compiler-notes.md` | Conservative 16-bit alignment, consistent/contradicted BP and register mappings, listing correlation, controlled DOS path experiments. MSC5.10 rules need fresh MSC6.00AX evidence. |
| Empires | `tools/probe_tu.py`, `tools/audit_relocation_topology.py`; `docs/matching-c-wave6.md`, `docs/matching-c-wave58.md` | Whole-TU probes, declaration and expression widths, object topology, compiler exclusion before declaring assembly. Turbo C/TASM rules do not transfer directly. |
| Icy Tower | `tools/diag.py`, `tools/pipeline.py`, `tools/metrics.py` | Classify source/control-flow before allocation/layout, measure emitted-code identities, trace compiler stages where available. GCC pass tracing and equivalence acceptance do not apply here. |
| Kegg | `docs/compiler-notes.md`, `tools/structure.py` | Probe types, nested scopes, expression trees and host environment with full contributions. Watcom shellsort slot allocation, modulo-25 identifiers and padding behavior are not MSC rules. |

The recurring blocker is missing original compiler context: declaration/prototype
history, expression widths, temporary lifetimes and compiler environment. Equal
length and similar operations do not prove the recovered declarations. None of
these controls establishes assembly or compiler exclusion. Siblings were read only.

## Installed tooling

`tools/mismatch.py` adapts Stunts' anchored alignment and conservative operand
families; source SHA-256 is in `stunts-diagnostic-origin.json`. Its 21 adapted
synthetic tests cover alignment, contradictory mappings, widths, segment/frame
registers, implicit effects and undecoded tails. SimAnt refuses unbound fixup
inputs: every bound byte remains visible and acceptance is independent.

`python tools/diag.py --triage --out build/workers/NAME/triage` compiles whole modules
once per group and reports strict target, peer and data verdicts separately from
patterns. `diag.py FUNCTION --source draft.c` inspects a chosen draft. Full instruction
artifacts stay in build output; `triage.json` preserves the 32-function survey.
Twenty-one candidates have original length. CalcScore and S15 have only stack-home
differences; S25:1035 only register differences. Linear decoding includes possible
tables/padding and is not a reachable-CFG proof. Existing `slots.py` connects the
observations to compiler-listing names. No additional compiler/debugger is needed
for this diagnostic tier.

Autosearch now fills its source-neutral allowance round robin across rules,
exposes `--neutral-beam N` in single and `--all` modes, and reports code identities.
A controlled test requires two interacting edits: a narrow search misses the
exact result, a wider search finds it, and peer regression still rejects it.

The starting-draft filter previously protected only peers/data already passing in
that draft. A broken draft could silently exclude an accepted peer from search
protection. It now protects every manifest claim and every checked data contribution,
rejects a broken starting draft, and saves the rejection report. Promotion already
required every claim to pass; accepted ownership was not weakened by the old filter.

## Negative controls and limits

Generators write only `build/workers/siblings/` and run from the repository root.
They merge old target bodies into current whole modules. Compare recorded source
hashes after future source changes. Every retained draft is an unclaimed hypothesis.

* `filenames.json`: 32 successful compiles with DOS source basenames of lengths
  1–8 for S15, memory compaction, CalcScore and S25:1035. Each target produced one
  code identity. Filename length does not explain these residues.
* `environment.json`: eight compiles with unchanged hash-pinned MSC6.00AX tools
  copied to DOS paths `D:\BIN`, `D:\B`, `D:\COMPILER`, `D:\NESTED\COMPILER`.
  Both targets produced unchanged code. These unregistered research environments
  cannot authorize promotion; production profiles are unchanged. TEMP, memory
  settings and other host effects remain untested here.
* `scopes.json`: 24 CalcScore nested history-loop scopes, declaration permutations
  and separate names. None is exact; best distance worsens from 12 to 23 and some
  variants lose PictureDialog. `score-scope-v2.c` retains a rejected hypothesis.
* `neutral-search.json` / `neutral-tried.json`: 208 S15 variants with
  `PROTO-NAMES,SYM-NAMES,DECL-SWAP`, neutral beam 24, depth 3, level cap 90 and
  budget 240. One target code identity; the two operand-byte residue persists.
  Strict search and promotion refusal transcripts are retained. Existing claims
  and both private-data contributions pass.
* `peer-repair.json`: nine natural pointer-result staging/type controls do not
  restore the disturbed memory peer. Initializers execute at the original return
  point, after validation and the lock decrement. None is accepted.

S15's unnamed BP-2 word corresponds to original BP-6 at two uses; its named result
is in SI. The residue is text-pointer segment/CSE storage, rather than a result-local
reorder. CalcScore's BP-4/BP-6 mapping is contradicted by later unchanged uses, so a
global permutation is insufficient. S25:1035's SI/BX substitution is local too.

The memory near draft swaps moved-flag/segment homes (BP-26/BP-22), with six operand
differences. **It also breaks accepted `f_171C_2086`: 88 bytes instead of 92, changed
bytes and relocation position.** `memory-peer-check.json` and
`rejected-memory-base.log` record this. Earlier notes claiming that this archived
near body preserved all current peers must not serve as fresh acceptance evidence.
Both environment controls retain the peer failure at every setting. Repair the
whole-module context before searching from `memory-near.c`.

## Verification and next work

`tests.log`: 203 tests pass (two skips). `validate.log`: all module/ownership,
45 compiler-rule and FAR_BSS checks pass (`validate.py --no-tests`, paired with
the fresh full test run). `hybrid.log`: byte-identical hybrid PASS, SHA-256
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`.
Manifest SHA-256 remains
`3235d9b8161d865ceb0954ef0ef90fc69731c13255a75a20091747d112dac1b9`.

Prioritize targeted TU/prototype/type and temporary-lifetime recovery, with every
accepted peer protected. Another generic disassembler or another compiler's
allocation rule is not supported by these findings. The missing matching RTLink
manager is a separate blocker to independent linking, not to module recovery.
