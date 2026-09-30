# Whole-build harness — design (worker `link`, prototype)

Status: installed as `tools/link.py` (run `python tools/link.py`; outputs in `build/link/`:
`provenance.json`, `report.txt`, the hybrid EXE). Result: **PASS** — the hybrid EXE's SHA-256
equals the original (`aa0596c6…4f11`), with every byte's provenance recorded.

`validate.py` passes with the harness hooks installed; the numbers below are from the original design run and are superseded by `python tools/link.py`.
The gate hooks it uses (`collect=` in tools/modules.py and tools/runtime.py) only record
bound bytes and relocation sites; they never change a verdict.

## 1. Three proof levels, kept apart

| Level | Claim | Bytes that may come from the original | Counted as reconstruction |
|---|---|---|---|
| (a) exact contributions | Every own byte is the bound output of a freshly compiled or assembled accepted object, or of an accepted MSC runtime member, placed at its accepted address. | none (the original is only compared) | yes (C, ASM, data, runtime counted separately) |
| (b) oracle-assisted hybrid | Own bytes + rule-generated fill + categorised debt = the original, byte for byte (SHA-256). | only bytes in a `debt:*` category, plus the file geometry (§7) | **never** |
| (c) independent historical link | A linker model builds the whole file from objects, libraries and a link script. | none | yes (future; see docs/level-c-link.md) |

Level (b) proves that our contributions **link**. Every own byte and every own relocation
entry is at the right file offset, and our accounting has no gaps or overlaps. Because debt
is copied verbatim, a hybrid mismatch can only come from an own byte, an own relocation
entry or our placement arithmetic. The run then prints the file range and the owner (see
(design run).

## 2. Data model

`ProvMap` keeps one *class* per file byte (506,509 entries) and one *owner* per byte.
`provenance.json` stores them run-length encoded (`ranges`: `{file:[a,b), class, owner}`).

| Class | Meaning | Where the bytes come from |
|---|---|---|
| `C`, `ASM`, `DATA_IN_CODE` | accepted claims (by claim `kind`) | `match.Binder` candidate bytes via `modules.verify_module(collect=)` |
| `PAD` | the MSC word-alignment `90` inside a complete TU's segment | the object segment's last byte (none today) |
| `DATA` | accepted game data placements (`_DATA`, `CONST`, far data, data-only TUs) | `modules.verify_data_segment` bound body |
| `RUNTIME` | accepted MSC 6.00 runtime members' code segments | `runtime.verify_all(collect=)` bound segments |
| `RUNTIME_DATA` | accepted runtime DGROUP data segments (a common PAD/EPAD area is placed once) | `runtime.verify_data(collect=)` |
| `RELOC_OWN` | relocation entry whose value comes from our fixup; the frame's order is fully explained by the objects (EXACT, complete frame) | computed from our site and frame |
| `RELOC_OWN_ORDER_ORACLE` | same value provenance, but the slot (order) is taken from the original | computed value, original slot |
| `LINK_FILL` | linker zero fill: 1 byte before a word-aligned next object, < 16 bytes before a paragraph-aligned object, section end or region boundary. Both neighbours must be own. | generated `00` (rule), never copied |
| `FAR_BSS` | frame 50F6 far communals, only when `farbss.account` accounts the region | generated zeros |
| `FORMAT_FILL` | MZ header padding and RTLink record padding | generated zeros |
| `debt:<category>` | not reconstructed; copied from the original in the hybrid only | the original |

Debt categories (region model, `geometry_from_exe`):
`mz_header`, `reloc_entry.<site category>`, `game_code` (root 0–29F4C), `text_prefix16`
(29F4C–29F5C), `runtime_code` (29F5C–2CFB0), `frame_2CFB` (2CFB0–2CFF0, empty today),
`rtlink_manager`, `rtlink_section_table`, `rtlink_vectors` (2CFF0–31259), `overlay_code`
(S00–S26), `far_data` (S27 < 55B30), `dgroup_data`, `common_tail`. A byte in no region, or
in a category the model does not know, is a **GAP** and fails the run. A second write to a
byte is an **OVERLAP** and fails the run.

Side attributes, reported separately and never hidden in a class:
* `runtime_fields_with_placement_derived_from_original`: `runtime.py` binds runtime data
  targets whose placement is not registered (e.g. a member's own `_DATA`) by deriving the
  placement from the original operand. It checks that the value agrees across references,
  then writes that value. That is **249 fixup fields / 498 bytes** inside `RUNTIME` and
  `RUNTIME_DATA`. They are counted as own bytes, as `validate.py` does, and listed so that
  the single-anchor ones can be reviewed.
* `fixup_closure`: for each code/data fixup of an own contribution, is the target defined
  by an own object, or known only from `layout/symbols.json`? Is the call routed through
  the original's RTLink vector table? This measures readiness for level (c).
* `frame_from_layout`: relocation entries whose segment field is the frame of a combined
  DGROUP segment (§4).

## 3. Placing each compiled object (no second binder)

`collect()` compiles every manifest module **once**, in parallel (`--jobs 8`; 123 modules
≈ 40 s). It calls `modules.verify_module(text, module, claims, collect=col)` and then the
runtime binder once. The hook (`collect_hook.patch`, about 30 added lines) records what the
gate already computes:
* per claim: `Binder.candidate` (bound bytes), linear address, relocation sites with
  RTLink group key and FIXUPP index, fixup records (`via_vector`, `direct_overlay`);
* per data placement: the bound body, start, placement frame and relocation sites;
* for a complete TU, the unbound object segment (for the trailing `90` pad);
* the object bytes (used by the level-(c) experiments);
* for runtime members and runtime data: bound segments, frames, relocation sites and the
  derived-placement fields.

Only verdicts decide inclusion. Only modules whose `verify_module` result is `exact` are
used; inside them, only exact claims and exact data segments. Runtime members are used only
when they match their manifest row (the same rule as `validate.py`). Addresses are the
accepted ones:

| Contribution | Address source | File offset |
|---|---|---|
| code claim / DATA_IN_CODE | claim `seg:off` (UNIT:SEG@OFF origin enforced by the gate) | root: `header + linear`; Snn: `section data offset + linear − load` |
| PAD | extent end − 1 | same |
| data placement | manifest placement (S27) | S27 data offset + linear − 3D570 |
| `_BSS` placement | memory only (listed, no file bytes) | — |
| runtime code | `runtime-location.json` via the runtime binder (frame 29F4, EMULATOR_TEXT at 2CFB0) | root |
| runtime data | derived / DOSSEG / class-sequence placements (`runtime.py`) | S27 |
| FAR_BSS | 50F6:0000 … DGROUP, when `farbss.account` passes | S27 |

The harness reconciles its totals with `validate.py` (`docs/progress.json`). C, ASM,
code-segment data, runtime, data, runtime data, far link fill and FAR_BSS **all agree**.
Three residuals differ, and each difference is a real `validate.py` accounting issue (§9).

## 4. Relocation tables

**Sites.** Each own fixup that produces a relocation (base16, pointer32) gives a site. Each
original entry of the MZ table and of the 28 section tables is looked up by `(unit, site)`.
An own site missing from the original, or an entry whose frame differs from ours, fails the
run.

**Entry value** = `(site − F·16, F)`:
* code: F = the claim's code frame, checked against the original: 5,335 entries with an own
  frame, 0 mismatches;
* far data: F = the placement frame (3D57, 4E4B, …);
* DGROUP data (game and runtime `_DATA`, `CONST`): F is the frame of the *combined* segment
  (`_DATA` → 55B7, `CONST` → 5D90). That is a linker layout fact, taken from the original
  and counted as `frame_from_layout` (1,906 entries). The harness checks that one segment
  name always has one frame. MS LINK and RTLink write the frame of the containing
  *segment*, not of DGROUP (55B3).

**Order model (new evidence, `exp_frame_groups.py`).** Each table lists frames in ascending
order, contiguously. **Within a frame, RTLink groups the relocations by target symbol across
all objects of that frame, not per object.** In the runtime `_TEXT` frame 29F4, the members'
entries interleave. The same holds in DGROUP `_DATA` (55B7) and `CONST` (5D90). Inside a
group, the order is (object link order, FIXUPP order). With object-qualified keys for
segment targets, 3,179 of the 3,252 own entries in complete frames lie in frames where
every group follows this model. The other 73 are all entries of two frames: the known
S00:31AD cross-function case (ZI-1) and module 295C, which has no extent. In 5 multi-object
frames (2,040 entries) the objects' entries interleave, as the model predicts
(design run). The docs' current wording "Within a module RTLink groups…" is right for game
modules only because each game module has its own frame.

Order status per frame unit (`order_status`):
`EXACT` (the table order is the object order), `GROUPED` (the order inside every group is
proven by the objects; the group order is the program-wide RTLink symbol order, taken from
the original), `DIFF` (some group's inside order differs), and `_partial_frame` when the
frame still has debt entries. Only `EXACT` in a complete frame is `RELOC_OWN`.

Current totals: **7,241 of 9,075** entries reproduced (sites and values).
* Order proven outright (EXACT, complete frame): 40 (+24 EXACT in partial frames).
* Order inside every group proven: 3,200 in complete frames plus 3,827 in partial frames.
* Group order taken from the original: all 7,027 of those GROUPED entries.
* Order inside a group differs (pending): 150.
* Slot: always the original's in (b). Where an own entry sits among debt entries also
  depends on the original.

## 5. RTLink section table, vector region, manager

Corrected region model (from the run, see §9):

| Linear | Content | Provenance |
|---|---|---|
| 2CFB0–2CFB2 | crt0dat `EMULATOR_TEXT` | RUNTIME |
| 2CFB2–2CFE4 | game ASM jump table `root:2CFB` | ASM (accepted) |
| 2CFE4–2CFF0 | paragraph fill before the manager | LINK_FILL |
| 2CFF0–31259 | RTLink manager frames 2CFF, 2FB3 (17,001 bytes) | debt |
|  of which 2CFF:0B6B–0D69 | section count word + 28×18-byte section table (510 bytes) | `debt:rtlink_section_table` |
|  of which 2CFF:25F6–2B46 | 136 vectors × 10 (1,360 bytes) | `debt:rtlink_vectors` |
|  rest | manager code/data (15,131 bytes) | `debt:rtlink_manager` |

The section, vector and manager relocation entries (204 of the root table) are debt.
Diagnostics:
* 127 of 136 vector targets are the start of an own C/ASM claim.
* Every vector's `E8 rel16` calls the same manager routine, 2CFF:0529.
* Section-table `w1` = 0x2576 is constant (manager-internal).
* `section_id` = index + 2.
* The count word is 28.
* Vector order is not sorted by (section, address). It is not first-reference order (in
  table or address order). It is not the relocation-group order either: 301 consistent vs
  297 inconsistent pairs (design run).

The manager is third-party code (Pocket Soft), like the MSC runtime. It can become
reconstruction only by binding a pinned RTLink/Plus manager object (docs/level-c-link.md).

## 6. MZ header

The fixed 30 bytes (`MZ`, sizes, relocation count, header paragraphs, min/max alloc,
SS:SP, checksum, CS:IP = manager entry 2CFF:06F8, relocation offset 30, overlay 0, and
0x1C–0x1D = 0) are `debt:mz_header`. The relocation table starts at 30 and its entries are
§4. The padding up to 14,848 (header paragraphs) is FORMAT_FILL.

Most fields follow from a level-(c) layout: image size, relocation count, header size,
min alloc from BSS + stack, SS:SP from the STACK segment. CS:IP needs the manager. The
harness does not derive them today.

## 7. Exactly what the hybrid takes from the original

1. **Debt bytes: 88,492.**
   * code: game 19,180, overlays 20,888, runtime 0
   * data: far 9,051, DGROUP 14,734
   * RTLink manager 15,131, section table 510, vectors 1,360
   * relocation entries not produced by us: 7,336 bytes = 1,834 entries
   * MZ header 30
   * `text_prefix16`: 16
   * common tail 256
2. **Geometry**:
   * header length and relocation offset;
   * section record file offsets and relocation counts;
   * the end of S27's data (its last 3 declared bytes lie inside the common tail and are
     classed as tail).
3. **Relocation slots** of all own entries, i.e. the program-wide RTLink group order and
   the position among debt entries.
4. **Layout frames** of DGROUP relocation entries (55B7, 5D90).

The following are *layout inputs* of level (a) itself, from accepted records that were
grounded in the original by analysis, not copied bytes:
* claim, extent and placement addresses (manifest);
* target addresses (`symbols.json`): 191 code and 5,215 data fixups target addresses no
  own object defines yet;
* vector addresses from the original's vector table (234 far calls);
* runtime data placements derived from original operands (249 fields).

Level (c) must produce all of these from a link script and objects.

## 8. Results (design run: sandbox, fresh compile)

* Own (level a): C 212,554; ASM 50,441; DATA_IN_CODE 1,481; DATA 91,233; RUNTIME 12,339;
  RUNTIME_DATA 1,057; **total 369,105 bytes** in 1,876 contributions.
* Generated fill: LINK_FILL 285 code + 35 data (7 of it far paragraph fill); FAR_BSS
  19,408; FORMAT_FILL 221.
* Relocation entries own: 7,241 / 9,075 (28,964 table bytes, 160 of them with proven order).
* Debt: 88,492 bytes.
* Hybrid SHA-256 = original: **PASS**. No gaps, no overlaps, no errors.
* Vectors: 136, of which 127 target own code.
* Runtime: a fresh compile of all 123 modules takes 37 s (42 s in total) at 8 jobs; `--reuse` runs in about
  5 s.

## 9. Findings for the supervisor

1. **Relocation grouping is per frame, not per module** (§4). This matters for the runtime
   frame and for DGROUP. It should be written into `docs/exe-format.md`
   (applied in docs/exe-format.md and docs/level-c-link.md).
2. **`validate.py` residuals are slightly wrong.**
   * `rtlink_manager_bytes_unaccepted` = 17,063 counts frame 2CFB (root:2CFB's 50 ASM
     bytes + 12 fill bytes) as manager. The manager starts at 2CFF0 (17,001 bytes).
   * `unresolved_code_bytes` = 40,272 is 50 too low: root:2CFB is counted as exact code
     but lies outside the game span 0–29F5C.
   * Both are fixed by the region constants in `tools_link.py`.
   * `docs/exe-format.md` says the manager occupies "frames 2CFB, 2CFF and 2FB3". Frame
     2CFB is runtime + game code.
3. **16 zero bytes at 29F4C–29F5C** precede crt0's `_TEXT`. The candidate is LINK's
   `/DOSSEG` 16-byte null area at the start of `_TEXT`. Recorded as `debt:text_prefix16`
   until a rule is recorded with a probe; then it becomes LINK_FILL.
4. **Runtime derived placements**: 249 fields are written from the original operand after a
   consistency check. Single-anchor ones are circular, and deserve a listed review (the
   hybrid is unaffected).
5. **Symbol order looks hash-like**: all insertion-order hypotheses score 48.6 %, below
   alphabetical at 49.9 % (design run). See docs/level-c-link.md.

## 10. Integration proposal

* Add the `collect` hook (`collect_hook.patch`; `git apply --check` passes on the current
  tree). Move `tools_link.py` to `tools/link.py`. Its unit tests (`tests/test_tools_link.py`,
  19 tests, synthetic geometry, no compiler) go to `tests/`.
* Add `validate.py --image`, which runs the harness with the same fresh collection
  (validate already compiles every module once; pass `collect=` there to avoid a second
  compile). It reports level (b) as `whole_executable: HYBRID_EQUAL (debt N bytes)`,
  separate from level (a) totals, and never adds hybrid bytes to any reconstruction
  measure.
* Keep `SIMANT.HYBRID.EXE` and `collection.json` in `build/link/`, which is ignored. The
  hybrid contains original debt bytes and is never an input to anything.
