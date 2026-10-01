# LessonDone (root:0E2E) targeted recovery report

No exact natural-C source was found. The working whole-module draft keeps the three previously accepted functions and the module's CONST contribution intact. `promote.py --verify-only` refused the only best-byte candidate because LessonDone still fails its complete byte, fixup, and relocation checks.

## Bound target evidence

`context.txt` identifies LessonDone at `root:0E2E:065E` (linear `0E93E`), size 723 bytes. `listing.txt` records the full bound instruction listing and all 56 words in the embedded switch table. The function begins with a 30-byte dispatch sequence; its table occupies offsets `+0x1e` through `+0x8d` (112 bytes), and code resumes at `+0x8e`. Target function-byte SHA-256: `d53fcd3b79c21247c81f0f15d388fb51680c03cefd76c70396b3a77c4a15566f`.

The table-aware breakdown was used only to locate differences. Every candidate remained subject to the strict whole-function and whole-module comparison; no table bytes were excluded from acceptance.

## Focused hypotheses

`base.c` is the original-order four-function module draft copied from the current LessonDone residue source. It is the positive control for the accepted peers and private data: `Feedback`, `RunTutor`, `GiveLesson`, and CONST all remain exact in every valid round.

The strongest diagnostic candidate, `case9_split_only.c`, spells LessonDone case 9 as sequential short-circuit tests. It compiles to 715 bytes, 8 bytes short, with 535 differing bytes in the shared 715-byte span and a relocation-set count of 8 versus 9. The first difference is at `+0x26`, the first byte of case 5's table entry. The 56-word table differs at 31 entries (42 table bytes); the post-table region has 493 differing bytes over the shared span. This control reproduces the archived `full-search/LessonDone/best.c` case-9 split candidate exactly (bound function SHA-256 `63422cb70806bff52c177ced511603019b45bdc7fafa62da0d2986be966ab6d2`), so it is a repeated historical failure rather than new recovery evidence.

A nested short-circuit rewrite of cases 7/26 plus split case 9 reaches the same 715-byte candidate. Testing the case-7 nesting alone emits the exact same 739 function bytes as the baseline; case-9 splitting alone produces the shorter candidate. The isolated result is retained to avoid attributing the improvement to the wrong edit.

Other new controls also failed strictly:

- Explicit default labels at the beginning or end of the outer switch produce 706-byte candidates, first differing at `+0x11`, with 8 versus 9 relocations. An explicit `default: break` leaves the baseline candidate unchanged.
- Nested `switch (MePlane)` forms for case 54 produce 722- and 723-byte candidates but retain only 5 of the 9 expected relocations. Merging the return after the two plane-specific assignments produces a 739-byte candidate with 8 versus 9 relocations.
- A case-54 result local produces 742 bytes and 8 versus 9 relocations. A lazy `long now` lifetime over the case-7/9 time comparison starts differing at `+0x3`, against the target's zero-local frame.
- Reordering separate case bodies to the observed target-block order produces the exact same 739 function bytes as the baseline. Grouping cases in that order produces 712 bytes and 8 versus 9 relocations.
- Rewriting dispatch as `switch (lesson - 1)` with cases 0 through 55 emits exactly the same 739 bound function bytes as the baseline (`088ff42b88a53a3a30bf6241a136473cea3f3a59c2f40bc7aee6a4213beccc5d`). The byte stream cannot distinguish these spellings.

The machine-readable whole-module verdicts are in `round2-results/results.json` through `round6-results/results.json`; each records all module claims, the CONST placement, and the object hash. `variant-summary.tsv` indexes the results. Complete source and generator hashes are in `source-hashes.txt`.

## Reproduction

From the repository root:

```powershell
python tools/context.py LessonDone > build/workers/fleet_lesson/context.txt
python build/workers/fleet_lesson/listing.py > build/workers/fleet_lesson/listing.txt
python build/workers/fleet_lesson/generate_round2.py
python tools/variants.py build/workers/fleet_lesson/round2-sources --module root:0E2E --jobs 2 --show LessonDone --out build/workers/fleet_lesson/round2-results
python build/workers/fleet_lesson/generate_round3.py
python tools/variants.py build/workers/fleet_lesson/round3-sources --module root:0E2E --jobs 2 --show LessonDone --out build/workers/fleet_lesson/round3-results
python build/workers/fleet_lesson/generate_round4.py
python tools/variants.py build/workers/fleet_lesson/round4-sources --module root:0E2E --jobs 2 --show LessonDone --out build/workers/fleet_lesson/round4-results
python build/workers/fleet_lesson/generate_round5.py
python tools/variants.py build/workers/fleet_lesson/round5-sources --module root:0E2E --jobs 2 --show LessonDone --out build/workers/fleet_lesson/round5-results
python build/workers/fleet_lesson/generate_round6.py
python tools/variants.py build/workers/fleet_lesson/round6-sources --module root:0E2E --jobs 2 --show LessonDone --out build/workers/fleet_lesson/round6-results
python tools/search.py LessonDone build/workers/fleet_lesson/case9_split_only.c --quiet
python tools/promote.py build/workers/fleet_lesson/case9_split_only.c --module root:0E2E --claim LessonDone --verify-only
python build/workers/fleet_lesson/compare_archived.py
python build/workers/fleet_lesson/write_hashes.py
```

The final strict search reports 715 versus 723 bytes, 535 differing bytes, and 8 versus 9 relocations. The verify-only report confirms the three accepted peers and CONST remain exact, then refuses LessonDone. No canonical source, manifest, journal, or evidence file was changed; no extent was claimed.
