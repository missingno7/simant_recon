# Display-mode selector storage candidate review

Status: `CANDIDATE_PENDING_PARENT_REVIEW`; `root_reviewed: false`. This is a generated-only, source-functional `char near g_5A97` candidate. It makes no claim about original storage ownership, module order, original initialization, or original byte identity.

## Source closure

The accepted producer is `src/S20/m39F1.c` (SHA-256 `6fd0a02991a29325f214049a8a8961aaee4bc65fbf760b296e63a6ac8f6fbe7b`), module `S20:39F1`, with `ReadWord`, `SkipWords`, and `ReadConfig` recorded `EXACT_NATURAL`. The probe pins each entire extracted function definition: `ReadWord` line 185 `db84e9a8a3aac977928fe2ca781569a02b98c4a0ad720d9c43ef68bf8feb7743`, `SkipWords` line 197 `9952f9c1a7184cd84db564b163b7ccd2acd647bc1a7836da86585b1383284dfd`, and `ReadConfig` line 209 `b8242702ec6b1809ccfb9dbfc04a772115b04fb1f76091bbed0ee49b87585833`. These exact bodies were used in a research harness; this is not a complete original translation unit.

First-write dominance is pinned to the earlier review and the six accepted canonical startup/mode sources. The fresh closure scanner verifies every source hash in the current layout manifest and only the 29 effective sources from `static-completeness/index-v1.json`; superseded experiments are excluded. It records all `g_5A97` references, fixed numeric address literals, pointer/index escape patterns, and signal/hard-error handler spellings. Closure details and complete pins are in `build/workers/dos_g5a97_config_producer/candidate/packets/display-mode-selector-review-v1.json` (SHA-256 `f5b0d390c1125d8c99dc71887495c10f77ac936f674d0cfa2af6e42ec26847ed`). Key path anchors are `src/root/m15F8.c:74-95`, `src/root/m00F8.c:328-346`, `src/root/m1A96.c:280-285`, `src/S15/m384C.c:66-82`, `src/S20/m39F1.c:68-69,82-114,125-154,216-258`, and `src/root/m205F.c:132-165`.

## Candidate extent and view limit

Provider `work/source-only-dos/providers/display-mode-selector.c` contains only `char near g_5A97;`. It compiles under MSC 6.00AX to `_g_5A97`, near communal length one. Separate plain-`char`, `signed char`, and `unsigned char` provider controls all have the same near one-byte OMF extent. That extent evidence cannot distinguish signedness. The canonical source contains plain-char declarations, unsigned-char consumers, and the byte compare `src/root/m1FBD.asm:13,38`; the candidate follows the plain-char source declaration while the byte views stay one byte.

## Runtime producer cases

The fixture executes the exact producer bodies against test-generated configuration files, test-owned path/message data, and the pinned real MSC runtime under RTLink/Plus 4.00 and 6.10. The output records plain-char / explicit-signed-char / unsigned-raw views, respectively. Both `0x00` and `0xFF` entry values were tested for every recognized mode:

| Config mode | Plain char | Signed char | Raw unsigned byte |
|---|---:|---:|---:|
| `?` | `-1` | `-1` | `255` |
| `E` | `0` | `0` | `0` |
| `H` | `3` | `3` | `3` |
| `M` | `5` | `5` | `5` |
| `T` | `2` | `2` | `2` |
| `V` | `8` | `8` | `8` |
| `e` | `4` | `4` | `4` |
| `m` | `7` | `7` | `7` |

In particular mode `?` assigns source value `-1`; the fixture observed `-1 / -1 / 255` from either initial byte under both linkers. Invalid mode and missing file each exited with status 1 and the expected message from both seeds. A no-seed control observed CRT zero only for this test-owned tentative definition. All 42 of 42 cases passed. The detailed run receipt is `build/workers/dos_g5a97_config_producer/candidate/producer-fixture.json` (SHA-256 `369c08e6f162fed8603f4f5bf05dd24dc24ff0278a7c7263bbb55dde0c15c404`).

## Limits

The fixture excludes `IBMInitStuff`, game functions, and first consumers. Its `BEFORE` display is harness instrumentation; it is not a game-code read. The dynamic evidence covers only the config producer, while first-write dominance along source-visible startup remains the static closure review. The unseeded CRT result is fixture-only. No original executable or original data bytes were read. No source byte or initialized value was copied from an original image. The contract and bindings remain root-review-pending and are not added to mandatory source-binding packets.
