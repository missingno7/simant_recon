# Menu-loader acceptance and list-helper follow-up (2026-10-01)

S17:384C is complete at `384C0:3867B` (443 bytes). The newly accepted
`o17_384C_0039` contributes 266 bytes, eleven bound fixups and four grouped
relocations. All four earlier functions, private CONST (16 bytes) and complete-TU
relocation order pass. `s17-accepted.c` is the canonical snapshot; promotion was
performed by `tools/promote.py` after exact search and verify-only acceptance.

The previous 266-byte near draft had the correct instruction stream but a 16-byte
frame rather than eighteen. A distinct final-phase pointer, the typed pointer-slot
read and a real later draw argument initialized before the fixup loops reproduce
the original homes without adding instructions. The draw argument is used by the
existing menu setup call. Its callee's accepted implementation returns int and
uses the argument to enable drawing; the prototype now agrees with that evidence.

LIFE-2 pins the complete source context and positive/negative compiler controls in
`evidence/codegen/LIFE-2-used-menu-draw-lifetime.json`. Moving the same draw
initialization immediately before its call, or calling with literal zero, leaves
the smaller frame and twelve byte differences. Int, unsigned and unsigned-char
draw locals all match. The accepted function is **layout-inferred**: the original
width, spelling and precise placement remain unknown. No artificial folded reads
or padding declarations occur in the accepted source. The rejected folded-index
near draft remains a separate control and must not be confused with acceptance.

## Retained experiments

`index.json` summarizes five S17 manual series: 124 controls including baselines,
all compiling and preserving earlier functions/private data. Six exact rows are
the three draw-width alternatives before and after source review, not six newly
recovered functions. The earlier declaration/prototype/name search tried another
166 variants, all yielding one code identity and no exact target. Its result,
tried inventory and log are retained separately.

| Series | Controls | Exact target rows | Accepted-peer preserving |
|---|---:|---:|---:|
| s17-used-word | 19 | 0 | 19 |
| s17-index-init | 25 | 0 | 25 |
| s17-folded-index | 46 | 0 | 46 |
| s17-home-ranking | 29 | 3 | 29 |
| s17-reviewed | 5 | 3 | 5 |
| list-value-flow | 25 | 0 | 7 |
| list-assignment-use | 19 | 0 | 13 |

Compact reports retain source hashes, compiler result, exact target verdict,
accepted-peer failures and private-data verdicts. S17 reports use the
pre-promotion claims snapshot (four accepted peers, no complete extent).
`sources.json` pins the frozen whole-module seeds with LF-normalized UTF-8 hashes
and the post-acceptance manifest hash. Generators run from the repository root
and write under ignored `build/workers/continue_next/`; their gates use the current
manifest. Replay S17 generators in the table's order: `s17_review.py` consumes the
home-ranking generator's selected source. It also regenerates the LIFE-2 spec.
Use the pinned spec for direct probe reproduction. Do not promote archived
negatives or assume current claim sets reproduce historical report shapes.

## Separate list-helper follow-up

`f_23E6_0000` remains unclaimed. `list-base.c` is a whole-module snapshot with its
156-byte baseline and fourteen accepted peers. The original 159-byte function
reloads its string pointer's segment into CX after advancing to the next string.
New for-header/value-flow, real length/next-pointer and assignment-result controls
do not reproduce that reload. All 44 compile and preserve private data; 24 regress
accepted peers and are rejected independently of the target.

The 159-byte folded assignment control uses MOV AX,1 followed by ADD to the index,
where the original uses MOV CX,[BP-0Ah] followed by INC. Four bytes still differ;
equal length is not acceptance. `list-assignment-near.log` retains that comparison.
Folded predicates would require STEERED evidence if exact, and none is exact.
These controls do not establish assembly or compiler exclusion. The value-flow
generator uses valid C89 blocks for scoped locals; only its corrected rerun is
archived. Neither list series changes canonical source.

## Acceptance and verification

`s17-final-search.log`, `s17-final-verify.log` and `s17-promote.log` record the
acceptance loop. `s17-accepted-slots.*` retains the resulting stack/register homes.
`s17-probe.log` passes all three LIFE-2 variants and nine checks. `validate.log`
passes the full test suite (two skips), all 47 compiler rules, all accepted module
claims, runtime and FAR_BSS checks. `hybrid.log` records a fresh rebuild with SHA-256
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`, identical to the
original. It ran alongside validation and read the preceding progress report for
its informational totals comparison; `hybrid-recheck.log` refreshes that comparison
after validation. Both use the accepted manifest and compiled contributions.
The hybrid includes explicit original debt and is not an independent historical link.

Validated totals: 1,243 exact C functions / 237,167 bytes; 96 complete TUs / 95 with
proven cross-function relocation order; 1,700 owned functions / 1,730 known.
Thirty functions and 15,709 code bytes remain open, plus 129 data bytes. Layout-
inferred C totals 20,867 bytes; STEERED and within-group-order debt are unchanged.
Continue from `docs/next-steps.md` using new source evidence; avoid repeating these
negative list controls or the preceding phase-next storage/header/profile searches.
