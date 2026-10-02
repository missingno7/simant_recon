# StopSong cleanup helper contracts

This report records a bounded executable comparison of the two cleanup helpers called by `StopSong`. It extends the earlier StopSong orchestration packet; it does not replace or promote that evidence. The runner is [run_dependencies.py](../tests/audio/stop_song_dependencies/run_dependencies.py), its small host-side state model is [helper_contract.c](../tests/audio/stop_song_dependencies/helper_contract.c), and the fresh receipt is [dependencies-v4.json](../tests/audio/stop_song_dependencies/evidence/dependencies-v4.json). All results remain diagnostic pending independent review.

## Source contract and layout

`src/root/m0000.c` defines packed `Sample` records and the 14-bank `Song` body. In this compiler profile, `Sample.data` is a four-byte far handle cell pointer at offset 0, `Sample.loaded` is a signed word at offset 12, each Song bank index is a word beginning at offset 28, and `Song.data` is a four-byte far handle cell pointer at offset 56. `Instr` rows are six bytes: a two-byte kind and a four-byte far `Sample *`. The fixture follows those layouts and supplies all 14 bank rows, including kind-2 rows and kind-1 rows with null sample pointers.

`f_0000_039B` first releases and clears a non-null `Song.data` through `f_171C_1C0A`. It scans exactly the 14 bank slots. A row queues its sample only when the indexed instrument has `kind == 1` and a non-null sample pointer. Before queueing, `loaded == 2` becomes 1; other loaded values are left alone. `number` is unused. The helper calls `f_0000_0149`, whose real body appends a four-byte far sample pointer to the freelist and immediately calls `f_0000_00DE` when `g_7574 == 0`. The actual `f_0000_00DE` body brackets its queue walk with `f_29F0_000A` / `f_29F0_0012`, releases only records with `loaded == 1 && data != 0`, clears their handle and loaded flag, then resets the freelist count.

The source disassembly for `f_0000_0149` identifies the private count as `DS:181C`, the far-pointer freelist as `50F6:0150`, and the flush condition as `g_7574`. Thus the test's private count address is source-derived from the instruction stream rather than a guessed exported name.

`src/root/m295C.c` defines a six-byte channel record `(type,num,c2,c3,c4,c5)`. `f_295C_0391` walks until the first `type == 0` sentinel and invokes `f_295C_02E8(c3,c4)` exactly when `c2 != 0`. Since `c3` is `unsigned char`, `c3 >= 0` is always true. The differential intercepts the call to `f_295C_02E8` at its ABI boundary and observes the `(device,note)` argument pairs. A sixth active slot and the following zero sentinel establish that this bounded fixture scans all six channels, rather than stopping at an assumed smaller count.

## Executed cases

The runner uses strict `PreparedPair` whole-module candidates for `f_0000_039B` and `f_295C_0391`; both current strict claims passed at the pinned manifest. For release it also compiles and executes the real same-module `f_0000_0149` and `f_0000_00DE` bodies in the candidate, with the original implementations running in the original DOS lane. It compares the ordered normalized calls to the external memory/database and pause/resume leaves, then compares the Song, sample, freelist, and count ranges byte-for-byte between DOS and candidate after each operation.

Two release sequences ran in both DOS and candidate machines:

- Immediate release (`g_7574 == 0`): one helper call, nine qualifying bank references. The observed order is the Song-data release followed by one pause/release/resume flush for each queued sample. Samples with `loaded == 1` or `2` and nonzero handles are released and cleared. Kind-2 samples and non-selected records retain their original state; the selected loaded-zero record queues but is not released by the flush predicate.
- Deferred repeated release (`g_7574 != 0`): two successive helper calls, producing freelist counts 9 and then 18. The second call does not release the Song handle again because the first call cleared it. An explicit real `f_0000_00DE` call then flushes the duplicate queue, releases each eligible data handle only on its first occurrence, and empties the count. This demonstrates why the caller's active-state guard matters: the helper itself can enqueue the same sample more than once.

Two channel scans ran in both lanes. The first has six nonzero channel types with `c2` enabled on slots 0, 2, 3, and 5, and produces four ordered note-off calls. The second places `c3 == 255` on active slot 2; that value reaches the callback unchanged, confirming the byte-width predicate is not a signed-negative filter. The 255 case is only a predicate-width diagnostic; the report does not assert that device 255 is valid for any actual audio backend.

The C model agrees on the normalized release-call ordering, queue sizes and pointer order at every flush entry, and the note-off list. It is an independent readable contract model, not a substitute for the DOS comparison. The receipt records two release scenarios, two channel scenarios, the three release-helper invocations in the deferred sequence, strict module identities, oracle identity, compiled native model, and before/after source/tool/evaluator hashes.

## Explicit boundaries

These comparisons do not model or claim equivalence for:

- `f_171C_1C0A`: the call and far handle-cell pointer are recorded, while DOS heap freeing, handle-table mutation, coalescing, and physical memory effects are outside the modeled boundary.
- `db_ReleaseHandle`: actual calls and handle-cell pointers are recorded; database ownership and allocator effects are not simulated.
- `f_29F0_000A` and `f_29F0_0012`: pause/resume ordering is recorded as callback order. Timer and physical audio-device behavior are excluded.
- `f_295C_02E8`: the dispatch arguments are captured, but its channel-record clearing, driver-table dispatch, and physical MIDI writes are not compared by this packet.
- Heap-address identity, host callbacks, hardware failure paths, invalid bank indices, freelist overflow, and invalid hardware-device identifiers.

The packet therefore establishes a reviewable helper-level cleanup contract for these directed valid fixtures. It is not a full sound-lifecycle proof, not a `BEHAVIOR_EXACT` registration, and not permission to alter the frozen historical tree.
