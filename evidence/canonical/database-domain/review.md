# Successful shipped VGA database lifetime

The two slot adjacency gates are excluded for one explicit operational domain:
one ordinary `main` lifetime with the locked default VGA configuration and
SHARED, HCEGANT and SOUND resource pairs, no external language/lrshare package,
no display override/alternate setup or `/s9`, and successful file/header/index
operations in valid nominal game state. This exclusion does not admit an extra
record, slot, initializer, clamp or failure-path layout assumption.

The proof adapted the active database worker's static/corpus census. It checks
every C/ASM file in `src/program.json`, requires discovery to equal that
inventory and every source hash to match, and classifies every occurrence of
the acquisition/release/selection entries as a known definition, prototype or
direct call. Address-taken uses, new callers, changed loop placements, reentry into
`main`, and even underscore-mangled MASM references fail closed. The reviewed
source pins additionally prevent a legitimately updated inventory hash from
silently admitting a changed acquisition predicate. Generated source controls
never modify canonical source.

The closed acquisition graph is `main -> IBMInitStuff`, then optional language,
shared, optional lrshare and one `f_205F_0004 -> graphics`; `main` subsequently
opens sound. `ReadConfig` precedes these calls. Its pinned V configuration sets
the selector to 8, so the lrshare cases 2/4 do not execute. The pinned corpus has
no language package. The default graphics prefix and `ant` suffix name HCEGANT.
Thus successful source calls acquire shared, graphics and sound once each.
No call or callback reference can reenter this graph from menus, save/load,
device selection, object release or shutdown.

The boot sequence establishes the cache hook with a pointer-only setter before
IBM initialization. The hook itself returns two already initialized objects
or NULL and opens no database. The setup, disk reset and config/parser prefix
open no resource DB. The graphics initializer resets callbacks and detects the
adapter, then opens its DB before cursor/resource and driver-loading calls.
IBM's subsequent menu/tile setup therefore sees the first two valid database
handles. Sound opens before main's intro, dialogs, NewGame and event loop.
Earlier resource lookups within IBM initialization follow shared acquisition.
Startup errors are terminal or enter error helpers; their returning/error
continuations are outside this successful-operation domain.

`db_numOfHandles` has one initialized owner, begins at zero, increments only
after each `db_SetDataBase` store and decrements only in `db_CloseDataBase`.
That release entry and therefore `CloseDB` have no live inbound caller or
address-taken use. `GetFreeHandle` first clears four record name markers and
returns the first empty slot. Each successful OpenDB copies the nonempty root
name before returning. Induction over the three acquisitions gives both record
and front-end slot indices 0, 1, 2 and then preserves count three for the lifetime.
The first-use flag has exactly three source references in its sole static owner:
the zero initializer, the conditional read and the sole assignment to one in
GetFreeHandle. No address-taking, additional writer or cross-TU/ASM consumer is
admitted. An unchanged-original control starts with all four markers occupied:
flag zero clears exactly the four first bytes and returns zero, preserving all
other record bytes; flag one preserves occupied markers and returns minus one.
Original loaded counter and first-use initializer words are also checked zero.

Object cache purges, releases and subsequent recalls change object Handles,
not DB slots. Every DBRecall call originates in `db_LoadObject`'s bounded
`i < db_numOfHandles` loop and takes `db_handles[i]`. FindIndex's DB argument
comes only from DBRecall. OpenIndex/CreateIndex get the successful OpenDB index;
CloseIndex only receives CloseDB's unchanged argument. The source storage census
includes every TU using the record or handle arrays. Read-only DBAdd/Delete/Pack
stubs do not introduce acquisitions; they signal an unsupported write operation.

SaveGame and LoadGame use ordinary file descriptors and the exact 308-entry
SaveRec table. The replay compares all 307 active original descriptors with
canonical symbolic pointers, sizes and counts, checks the zero sentinel and
rejects wrapping ranges. No transfer range intersects database records, handle
slots, the counter/cache/closed words or GetFreeHandle's first-use flag. Valid
save/load therefore cannot restore a different DB lifetime through an escaped
transfer pointer. A generated save-destination mutation is rejected.

Original-instruction controls complement the static induction. The original
front end writes slots 0â€“2 for explicit successful OpenDB outputs and safely
writes slot 3 in the capacity contrast. A fifth returning failure genuinely
writes at 50F6:3B58 before checking the negative result. This test models only
the OpenDB output and starts with an existing cache; it is not a DOS open test.
The independent error-continuation probe executes actual GetFreeHandle and
CopyRootName: full occupancy plus returning guard writes record[-1], while
occupancies 0â€“3 write the normal records. The original db_LoadObject iteration
calls the DBRecall boundary with handles 0, 1, 2 and never recalls a slot-3
canary. No dynamic control supplies the source closure by absence alone.

The source and resource census, not a finite runtime trace, establishes the
slot invariant. DOSBox-X remains authoritative for original whole-game runtime
acceptance. This claim closes neither FindIndex's one-past read nor independent
heap, ctype, graphics, sound or UI blockers. Punt's nonzero guard still returns.
External language with mode 2/4 permits five opens; failed/corrupt resource and
allocation operations or state corruption remain outside the supported domain.
Such cases still require source/error contracts and cannot be classified as
harmless historical layout.

```powershell
python evidence/canonical/database-domain/replay.py --out build/scratch/database-domain
python -m unittest discover -s tests -p test_database_domain.py
```

The lead admitted `database-open-minus-one-record` and
`database-handle-plus-four` as resolved supported-domain contracts for this
pinned successful default VGA lifetime. `src/program.json` owns this scope
and retains the two cross-owner failure facts and returning Punt regression
as explicit exclusions. Build and execution receipts carry the contract;
launch arguments are checked separately from the successful-operation premise.
No universal failure correctness is inferred.
