# Original allocator fixture contract

The parent accepts the fixture repair and its finite corroboration. Canonical
allocator definitions, strict static receipts, inventory, manifest and published
checkpoints remain unchanged. The replay's original pending-parent status is
preserved in `receipt.json`; this review records the subsequent acceptance.

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
