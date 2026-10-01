# Search context and focused residue controls (2026-10-01)

The previous checkpoint c2205ff is pushed to origin/main. This follow-up fixes a
search default and retains 11 negative whole-module series: 176 controls including
their baselines, 175 successful compiles, no exact target. Nothing was promoted.
All compiled controls preserve private data; 17 regress accepted peers. Those
variants remain rejected. `index.json` records the counts separately.

## Search now uses the module's options

Bare `search.py FUNCTION draft.c` formerly compiled with generic profile flags
and no manifest placements. That produced a different candidate from the module
verifier: the memory baseline appeared much worse than its actual six-byte
residue. `tools/search.py` now inherits the target object's profile, flags and
private-data placements. Explicit CLI options override them. A later object of
the same frame uses its own record; an unrecorded object uses profile defaults.
A C experiment in an assembly-owned object still uses a C compiler.

Search history records the module key and effective placements alongside flags
and the source hash. Search still checks one target; it does not replace the
whole-module gate. `tests/test_search.py` covers inherited context, overrides,
later objects, source-language changes and profile fallback. Live controls match
accepted f_171C_2086, retain f_171C_0CF4's strict six-byte failure and reject a
wrong placement of the peer's referenced private DATA. No binder or acceptance
rule changed. The three `*-search.log` files use the fixed default. The three
`*-promote-refused.log` files retain refusal with every accepted peer/data exact.

## S15: text-pointer segment storage

The baseline has 326 bytes / 137 instructions. Its two differences remain the
text segment spill and later push: candidate BP-2, original BP-6. Rectangle and
event storage have no demonstrated connection to that missing home.

| Series | Controls | Result |
|---|---:|---|
| s15-rect-phases | 10 | Separate border/print rectangles and block scopes do not match; extra live rectangles grow the frame. |
| s15-rect-views | 8 | Shared union rectangle, first-member and void-pointer views retain the two-byte residue. |
| s15-aggregate-storage | 12 | Word/byte/long rectangle storage and word/byte event storage retain the residue. |
| s15-type-context | 14 | Real Event/Rect typedefs and a used text-pointer alias retain the residue. |
| s15-runtime-headers | 7 | Pinned stdio.h/stdlib.h for the actual puts/exit calls, at the top or runtime declarations, retain the residue. |

Every S15 source control preserves all seven accepted peers and DATA/CONST. The
union and array forms are representation hypotheses, not recovered declarations.
The generators retain the corrected word-boundary rectangle substitution and
exclude unsigned-char pointers from the TextPtr rewrite; early generator mistakes
are not included as compiler-exclusion evidence.

## Memory compaction: flag and segment homes

`memory-base.c` is the repaired context-next draft, retaining the used nb alias.
It preserves all 57 accepted peers, including the 92-byte unlock function, and
DATA/CONST/BSS. The target remains 490 bytes / 182 instructions with six operand
differences: candidate moved at BP-26 versus original BP-22, and candidate segment
at BP-22 versus original BP-26. Its wide flag and low-word return remain hypotheses.

`memory-wide-segment.json` records 19 controls: narrow/wide flag storage paired
with real used long/unsigned-long segments, cast or low-word lvalue reads, and
volatile-word contrasts. `memory-pointer-phases.json` records seven controls
reusing nb, or a real adjacent pointer, in neighbor/scan/found phases. No target
matches. All accepted peers and private data remain exact in these source series.

## S25: one far-field register choice

`s25-base.c` merges the earlier near target body into the current canonical
module, preserving the now-accepted DoAntMoveY context. The target remains 281
bytes / 92 instructions. Only the LES and push at 110B/110E select BX instead of
the original SI; earlier uses of that same field pointer already match.

`s25-field-lifetimes.json` has 29 controls: real field pointers initialized before
or after the saved-state call, scoped/value snapshots for DigMyTile, register
requests and capturing x at its existing x=y assignment. None matches; all peers
and data pass. `s25-field-views.json` has 13 controls for short, one-word arrays,
anonymous single-member structs and unsigned storage read as signed words. The
target retains the same two bytes in every form. The three member forms regress
accepted peers, including DoAntMoveY in two cases, and are rejected.

`s25-folded-reads.json` records 32 USE-1/USE-2-style unsigned field reads around
the plane condition and folded call arguments. They add code or otherwise fail
to reproduce the register choice. Original eliminated expressions are unknown;
these diagnostic controls would require STEERED marking if one matched. All
accepted peers and data pass, but none is accepted.

## Compiler/profile contrasts

`optimizer-controls.json` retains 25 whole-module controls across all three
targets: the selected flags, plus /Oa, /Ol, /Oz, /Or, /OaOl and their combination.
Memory and S25 also test MSC 6.00/6.00A; prior S15 version controls already exist
in context-next. All targets remain inexact. Fourteen successful controls regress
accepted peers; all 24 successful compiles preserve private data. S15 and S25
produce one bound target code identity each; memory produces seven.

MSC 6.00 fails internally on this whole memory source (C1001, newcode.c:1.87,
line 535); the retained error is a source/profile-specific compile failure, not
evidence that the DOS target was assembly. The 6.00A memory control retains the
six-byte residue and all accepted peers/data.

## Verification and continuation

`sources.json` pins the three whole-module seeds with LF-normalized UTF-8 hashes
and the manifest identity. Reports retain per-variant source hashes, target
verdicts, peer losses and all data checks. Generators read these frozen seeds,
write only build/workers/phase_next and run from the repository root. Their
claims come from the current manifest: after future acceptance, a replay's peer
gate may differ from the recorded checkpoint. No diagnostic result authorizes
promotion.

`search-tests.log`: seven focused tests pass. `tests.log`: the fresh full suite
passes 210 tests with two skips.
`validate.log`: all 46 compiler-rule probes and fresh module, ownership, runtime
and FAR_BSS validation PASS
(`--no-tests`, paired with that full suite). `hybrid.log`: byte-identical hybrid
PASS, SHA-256 aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11.
The manifest identity and coverage are unchanged: 31 open functions, 15,975 game
code bytes and 129 data bytes remain. The hybrid copies explicit debt from the
oracle and is not an independent historical link.

Avoid repeating these storage/header/profile series. Continue only from a new
listing-grounded lifetime or CSE hypothesis, or rotate to another open body with
fresh semantic evidence. The search-default mismatch is resolved; the three
source residues remain unresolved. These experiments do not admit assembly.
