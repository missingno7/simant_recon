# Original allocator fixture contract

The parent accepts the fixture repair and its finite corroboration. Canonical
allocator definitions, strict static receipts, inventory, manifest and published
checkpoints remain unchanged. The published replay reports FIXTURE_CONTRACT_VERIFIED. The earlier worker
receipt and parent acceptance remain recoverable through Git.

## Three corrected premises

* Original startup gives s_2F46 offset zero. Allocation stores raw OFF(h) in
  Block.handle; movement/recovery adds that signed word to the master base.
  The previous nonzero base allowed seeded helpers to pass but actual allocation
  followed by pointer recovery reaches the original bad-handle Punt. Descending
  FFFC..FF00 slots now follow the original convention, are cleared and observed.
  Sparse fixtures distinguish the allocated high-water counter from live count.
* f_171C_0FBC returns an unfinished raw Block before its caller installs the live
  header and master handle. The old nine-step sequence's final compaction was
  invalid persistent history. Raw helper histories now end at that boundary.
  A separate completed original public allocation/free history executes current
  candidate compaction and then original pointer recovery.
* Startup copies s_2F4E {0,0L,0,5} into the DiscardEntry payload. fd_3948 points
  at the template itself; discarded master cells point two paragraphs later.
  HDR subtracts those paragraphs and reads type5, size0. The previous fixture
  pointed fd_3948 two paragraphs too far and seeded an incorrect nonzero size.

Shared dialog, window, list, rendering and viewport consumers use this single
fixture with explicit arena parameters. No mutable global fixture overrides or
second allocator model remain in these callers. Invalid indices, missing slots,
physical header sizes, nonzero bases and overlapping arenas fail explicitly.

## Evidence and validation

```powershell
python evidence/canonical/allocator-fixtures/replay.py --out build/allocator-proof
python -m unittest tests.test_memory_fixture_contract
python tools/canonical_behavior.py --count 16 --out build/behavior/allocator-current
```

Fresh outputs belong strictly below build/. The replay executes original allocation,
header/handle recovery, movement and resize instructions relevant to
these claims; it does not execute complete DOS allocation/EMS startup or game
reachability. Template placement remains a test-owned proxy.

The parent replay passes 102 comparisons across all four reviewed memory targets,
with four distinguished source mutations, actual allocation/recovery controls,
invalid-premise negatives and completed persistent history. Eight repository
regressions cover the corrected premises, original reclaim/type/free behavior and
discarded-lock Punt. All 29 current behavioral domains pass 12,130 paired cases
and their source negative controls. Repository validation passes 279 tests with
two intentional skips; historical validation passes all 49 compiler probes and
existing exact/runtime gates. Ten resize and two cache-invalidation pairs still
agree under the existing viewport premises.

The prior ralloc_memory_v2_stateful nine-step success is superseded as evidence
of valid persistent heap history. Its historical receipts remain in Git. Strict
static semantic conclusions are unchanged; repaired finite fixtures corroborate
the current implementations rather than proving completeness by themselves.

## Discarded resize observation

`discard_probe.py` executes two real original soft allocations (160 and 32 bytes),
reclaims both, calls original f_171C_1C1C and observes sizes0/0. Original
f_171C_18A6 then resizes the first to100 bytes/type1, preserving its master handle.
The second remains discarded/type5. During new allocation the shared template's
old type is temporarily cleared and restored; this is not persistent corruption.

`native-discrepancy-before.json` preserves the actual pre-fix provider observation:
sizes160/32 and refused resize with SIM_HANDLE_DISCARDED_DATA. Passing that old
witness proves a discrepancy, not equivalence. Any provider repair must separately
validate size, identity, allocation/free accounting and isolation from other
handles against the source contract. Whole heap-history equivalence and ordinary
gameplay reachability remain open.

## Accepted native boundary repair

The current whole provider clears size and charged bytes in both explicit discard
and budget-reclaim paths. Resize can allocate fresh bytes into a discarded slot,
skips its old payload copy, and preserves the master slot. The shared DOS source
is unchanged; this repairs the existing native physical-memory replacement.

Run the current provider and source mutation controls with:

```powershell
python evidence/canonical/allocator-fixtures/native_discard.py --conversion build/portable-sdl3 --out build/native-discard-current
```

`native-repair.json` records the parent independent replay using the current
complete build's flags and all current input pins: 37 positive controls pass.
Both full-TU negatives are distinguished: retaining old sizes fails explicit and
budget-discard checks; rejecting discarded resize fails stable-handle restoration.
Other controls verify index/master identity, no spare slot requirement, isolation
of another discarded handle, charging 112 bytes for the 100-byte host allocation,
failed host-budget restoration without changing the target, retry after freeing
a hard allocation, and preservation of existing live lock/resize behavior.

Only the zero-size and successful discarded restoration observations are DOS
semantic corroboration. Host budget/failure checks are native regressions, and the
live resize controls preserve existing native behavior rather than establish DOS
equality. Original live resize uses paragraph counts: same-paragraph changes can
retain the old requested size, and small shrink can retain the old type. That
broader discrepancy is not repaired here.

Discarded name, age and attributes still use per-slot native fields instead of
the shared DOS template; the original can also mutate shared age. Paragraph
copying, header-inclusive DOS accounting, raw flags and 16-bit arithmetic,
reclaim ordering/EMS layout, and Punt versus host-return failures remain outside
this bounded repair. These remain SEMANTIC / PORT-BLOCKING. No complete native
allocator, standalone DOS link or functional-source milestone is claimed.

The native manager token-identity control is a host API regression. Original
f_171C_18A6 rejects the DOS index-handle form; public native wrappers currently
accept that form. This ABI difference remains outside the repaired real-master
handle domain and is SEMANTIC / PORT-BLOCKING.
