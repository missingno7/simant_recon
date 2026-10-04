# Free-list Punt re-entry audit (v31)

Status: **candidate for root review; `root_reviewed=false`; source/static follow-up only.** No production source, manifest, journal, probe, object, image, or Git file was changed.

## Finding

The `g_181C > 38` test does not establish that the 40th store is blocked on every path. On an ordinary first call to `Punt`, `src/root/m1C62.c` sets its static `g_54F8` recursion latch and calls `o15_384C_0152(text, 1)`. That dispatcher calls `exit(0)`, so the original `f_0000_0149` invocation does not resume. Before `exit`, however, it conditionally calls `f_277E_0154` when `fd_55B3_610A != 0`. That shutdown calls `f_295C_0391` and `f_0000_0429`; the latter calls `StopSong`, calls `f_295C_0391` again, then sends every `fd_50F6_0000[i]` with `kind == 1` through `f_0000_0149` for `i = 0..55`.

If the outer guard was reached with `g_181C == 39` while `g_7574 != 0`, the fatal shutdown runs before `g_7574` is cleared by the interrupted sequencer call. A nested `f_0000_0149` calls `Punt` again, but `g_54F8` is already 1, so that nested `Punt` returns; the unconditional post-increment store then writes `fd_50F6_0150[39]`. A selected sample table gives a concrete producer: mode 1 copies the 56-entry `fd_55B3_0C42` table, whose rows are all `SND_DAC` (value 1), into the runtime instrument view. Thus fatal shutdown can perform the 40th store before the eventual `exit(0)` when that runtime state is selected.

The source graph does **not** prove that a particular shipped song/resource and execution state first accumulate 39 entries with `g_7574 != 0`, or that `fd_55B3_610A` is nonzero on that exact overflow. Those are explicit runtime/resource preconditions, not assumptions in this receipt. `f_284A_067F` sets `g_7574` for MIDI event processing and clears it only on return; its timer-side callers are in `src/root/m28BC.asm`. Type-1 voice-stop callbacks can reach the free-list writer during that interval, and the list is not drained merely because the callback returns. This establishes the conditional re-entry path, not an unconditional shipped-session reachability claim.

Accordingly, the old guard supports a **logical normal-path capacity of at most 39 entries before the fatal check**, but it does not prove the physical extent is exactly 39 or protect all fatal-cleanup stores. The physical extent/adjacency of `fd_50F6_0150` remains separate layout debt. Do not promote an exact `[39]` owner from this guard.

## Count and producer census

Across 127 canonical source files plus the 29 pinned strict-effective source files (156 unique paths), the only `g_181C` occurrences are its zero initializer, the `f_0000_00DE` loop read/reset, and the `f_0000_0149` guard/post-increment write. The only direct `f_0000_0149` producer callsites are:

| Source site | Append condition / call order |
|---|---|
| `src/root/m0000.c:f_0000_039B` | Up to 14 bank rows; `kind == 1`, non-null sample; demotes `loaded == 2` to 1, then appends. |
| `src/root/m0000.c:f_0000_0429` | `StopSong()` → `f_295C_0391()` → up to 56 instrument rows with `kind == 1`; no drain at function end. |
| `src/root/m290D.c:f_290D_0193` | Replaced channel owner is appended when non-null and `loaded == 1`, before installing the new owner. |
| `src/root/m290D.c:f_290D_026C` | Channel owner is appended when non-null and `loaded == 1`, then owner/sound pointers are cleared. |
| `src/root/m295C.c:f_295C_0015` | Walks channel records to zero sentinel; idle type-1 channels append non-null `snd` with `state == 1`. |
| `src/root/m295C.c:f_295C_00C9` | Same idle type-1 cleanup while walking the channel records, before priority selection. |

`StopSong` only calls `f_0000_039B` when `g_756E` is nonzero; that cleanup visits 14 song banks and then calls `f_295C_0391`. In the fatal audio shutdown, `f_277E_0154` invokes channel cleanup before `f_0000_0429`, whose own 56-row scan follows `StopSong` and a second channel cleanup. `g_7574` is initialized to zero in `m284A.c`, set to 1 around the sequencer event loop, and reset to 0 after it. `f_0000_0149` drains via `f_0000_00DE` only when `g_7574 == 0`; `f_0000_00DE` iterates the recorded count and resets it to zero.

## Pins and method

Required instruction files were read before the audit. The scan used source text only: 127 `src/**/*.c`/`.asm` files and the 29 strict-effective whole-module source paths from the pinned overlay check. Every source hash in the prior 156-path owner inventory was rechecked against the current filesystem; all 189 recorded role/source entries matched. The strict overlay's only corrected module is `DrawBalloons`, unrelated to this owner. No `context.py --raw`, original executable bytes, generic behavior matching, compile, or runtime probe was used.

The machine-readable companion records the source hashes and inventory receipt identities. Existing owner evidence remains root-false and unchanged.
