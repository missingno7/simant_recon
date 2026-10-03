# Returning-Punt database-gate reachability review

Status: **No source-reachable database re-entry found in the reviewed fatal path.**
The three display slots previously treated as unowned now have admitted storage
and target mappings in `work/source-only-dos/callback-table-reviewed-contract-v1.json`
and `callback-table-bindings-v1.json`. Their selected driver targets and the
installed INT 33h/INT 08h callback producers are now traced below. The generic
arbitrary-callback API remains in source, but has no call or address-taking edge
in the closed DOS source tree. On that source boundary, the first `Punt` reaches
full C `exit` before unwinding to the failed database caller. This is a reachability
finding, not a change to either database layout gate or their separate storage
evidence.

## State and synchronous path

`src/root/m1C62.c:31-60` defines private `static int g_54F8 = 0`; the sole source
write is `g_54F8 = 1` at the start of `Punt`. There is no reset. The original
context packet (`python tools/context.py Punt`, no `--raw`) confirms the guard,
store, and order: `vsprintf`, `sprintf`, `printf`, indirect `g_9128(0,15,0)`,
`f_1CE2_01C3`, then `o15_384C_0152(text,1)`. If the guard is already set, `Punt`
branches directly to its `retf`.

`src/S15/m384C.c:97-119` and its context packet establish the dispatcher order:
`f_171C_0676` (exact empty stub), the state-dependent UI stub,
`f_171C_030C`
(enabled for `flag=1`), optional sound shutdown (`fd_55B3_610A`),
`f_1C62_00A1`, conditional `f_1C62_0090`, `puts`, empty `f_00DE_000A(1)`,
then C `exit(0)`. `src/root/m00DE.c` confirms the shutdown hook has an empty body.
The Ralloc dump path performs time formatting and file output; it has no direct
database call in the recovered body.

The sound shutdown callback is table-dispatched through `g_68DA[mode]` in
`src/root/m277E.c:37-40,123-128`. Its table targets are source-defined sound
reset routines. `f_0000_0429` stops the song and releases sample resources;
`f_295C_0391` walks sound channels; `f_28BC_04E0` restores the timer hardware
state. No direct database entry is present in those recovered paths.

## Exit and registered terminators

The source declaration `exit` binds to `llibcr.lib` member `dos/crt0dat.asm`,
public `_exit` at offset 481 (`layout/functions.json` and `layout/symbols.json`).
The pinned MSC 6.00 DOS startup source says this public is **full `exit`** (`xor
cx,cx`): it runs on-exit callbacks, runtime pre-terminators, C terminators, then
calls DOS `terminate`. The quick `_exit` entry is the separate public `__exit`
at offset 488. Thus normal completion of the call does not return to the
database caller, but callback execution happens first.

Recovered source registrations (`rg -n "atexit|onexit\\(" src`) are:

- `f_171C_0020` and `f_171C_0678` (`src/root/m171C.c`): EMS release and DOS
  memory release/reset.
- `f_0250_0114` (`src/root/m0250.c`): EMS release.
- `f_19DC_0008` (`src/root/m19DC.c`): database EMS-cache handle release.
- `f_1F58_00A1` (`src/root/m1F58.asm`): restore the saved INT 23h vector.

Their recovered callback bodies do not call `OpenDB` or `db_SetDataBase`.
The EMS release path can reach `f_195A_02B7`, which issues `int3` and far-jumps
to `Punt`; with `g_54F8 == 1`, that nested call takes the guard return. This
does not itself establish any database re-entry. The pinned CRT also iterates
linker terminator tables; this review does not claim those tables or external
debugger/runtime hooks are empty.

## Admitted callback storage and selected display targets

The reviewed callback-table contract owns `g_9128`, `g_9154`, and `g_9178` as
slots 0, 11, and 20 in a 25-element near array of far function pointers. It
records all four driver target maps. `src/root/m1B4E.asm:56,280-291` makes
`g_3DF8` point at the array and copies 50 words from the selected source table;
the table reset first fills all 25 entries with the empty `f_1B4E_000C` target.
The initializers in `src/S00/m3126.asm`, `src/S00/m31AD.asm`,
`src/S00/m31AD_2AB4.asm`, `src/S01/m3126.asm`, `src/S02/m3126.asm`, and
`src/S03/m3126.asm` pass their own complete 25-entry dispatch tables to that
copy routine. `src/root/m205F.c:92-203` selects the relevant initializer for
the active mode: modes 0/4/8 copy S00, 2 copies S03, 6 copies S02, and 3/5/7
copy S01; mode 1 is redirected to mode 5 and copied through S01 when the
`g_6298` branch runs, otherwise the preceding reset leaves the no-op table.

The three target families are:

| slot | S00 | S01 | S02 | S03 | source behavior |
|---|---|---|---|---|---|
| `g_9128` / 0 | `_o00_31AD_1659` | `_o01_3126_0167` | `_o02_3126_0040` | `_o03_3126_019E` | Set the driver pen/color state; no calls. |
| `g_9154` / 11 | `_o00_31AD_1206` | `_o01_3126_0516` | `_o02_3126_0636` | `_o03_3126_0C11` | Bitmap blit, or a clipping wrapper which calls `f_1D8E_*` and dispatches through slot 12 (`g_9158`). |
| `g_9178` / 20 | `_o00_31AD_1481` | `_o01_3126_0F78` | `_o02_3126_0051` | `_o03_3126_01B3` | Restore/set the video mode through `f_1B4E_015B` and INT 10h; no database call. |

The selected `g_9154` blitters and their slot-12 targets can call the cursor
maintenance routines `f_1B73_0196`, `f_1B73_04BB`, and `f_1B73_00D9`. The
clipping helpers in `src/root/m1D8E.c` compute clipped rectangles and call
`g_9158`; they do not call the database API. The direct display paths likewise
contain no `OpenDB` or `db_SetDataBase` call. These indirect calls are not
unresolved display pointers: every selected driver slot is in the reviewed
dispatch table.

## Interrupt queue producers and callback closure

`src/root/m1B73.asm:122-150` defines the three INT 33h event queues and the
separate INT 08h timer queue. `f_1B73_0AA3` resets the event queue counts and
sets the mutable mouse dispatch slot `g_5FFA` to `f_1B73_0CB3`; the assembly
`f_1B73_0CB3 -> f_1B73_0CEF` scanner invokes a stored far callback at
`ES:[DI+8]` only for a matching queued record. Queue contents are copied into
place by `f_1B73_0B00` or `f_1B73_0AC3`, not by the scanner.

The source call graph closes those producers as follows:

* `f_1B73_0B00` has three source callers. `f_1FD2_032F` is called only by
  `f_1FD2_02FF`, which passes `f_1B73_0D4B` into `g_6016.fn` before insertion
  into the separate INT 08h queue at `fd_5071_0728`. `f_1FD2_03EB` inserts
  `g_6004`, whose initialized callback is `f_1B73_030F`, into
  `fd_5071_03C4`. `f_1FD2_044F` inserts `g_603A`, also initialized with
  `f_1B73_030F`, into `fd_5071_0060`.
* `f_1B73_0AC3` has one source caller, `f_1FD2_0390`. That generic helper
  copies the caller's arbitrary `fn` into `g_6016.fn` and inserts it into
  `fd_5071_0728`, but the canonical source tree has no call, address-taking,
  function-pointer-table entry, or alias referring to `f_1FD2_0390`. Its
  existence and public declaration alone do not populate the queue in the
  closed DOS program.
* The source writes to the stored callback fields are the static initializers
  and the assignments in `f_1FD2_032F` / `f_1FD2_0390`. There is no other
  writer or escape for `g_6004`, `g_6016`, or `g_603A` in `src`. The interrupt
  queues are zero-initialized, and `f_1B73_0AA3` explicitly clears the event
  queue counts at startup.

`f_1B73_030F` calls only `f_1B73_036E`, which stores an input event in the
keyboard/event ring. The reachable INT 08h callback `f_1B73_0D4B` enters
`f_1B73_0D4C` and, on cursor changes, `f_1B73_0DA4`; that path uses the
source-owned display slots `g_9148`, `g_9128`, `g_9164`, `g_9160`, `g_9154`,
and `g_914C`. Their four mode targets are in the accepted dispatch tables; the
targets update/copy video state and may poll the same fixed callback queues.
No target in this callback closure calls `OpenDB` or `db_SetDataBase`. A nested
`Punt` from the cursor guard sees `g_54F8 == 1` and returns to the current
display/callback code; it does not return to the original database caller.

The installed INT 33h and INT 08h handlers are removed by
`f_1C62_00A1 -> f_1B73_02A9` during the fatal cleanup, before the final
`g_9178`, `puts`, and `exit` calls. While they remain installed during the
Ralloc dump, sound shutdown, and display work, their stored callback targets
are the closed set above. The callback objection in the earlier review was
therefore about target reachability, not missing storage; the admitted slots
and the reachable queue producers now supply those missing anchors.

## Result for the returning-Punt database gates

For a first `Punt`, the source stores `g_54F8 = 1`, runs the fatal path, and
reaches the full MSC `exit(0)`. The asynchronous paths within that interval
resolve to the fixed callbacks above. The Ralloc, sound, interrupt-removal,
display-restore, and registered exit-cleanup paths contain no source call to
`OpenDB` or `db_SetDataBase`; the exact C `exit` entry terminates after its
registered callbacks. Thus a missing-slot `Punt` in `OpenDB` or
`db_SetDataBase` does not return to the failed database operation in the
reviewed source build. Recursive `Punt` calls made by the cleanup paths take
the `g_54F8` guard return only within that fatal path.

This closure is specific to the tracked DOS source call graph. It does not
authorize guessed storage or alter the admitted four-record/handle owner
extents. If another unrepresented binary component writes the queue records,
calls the otherwise-unreferenced `f_1FD2_0390`, or invokes a database API from
outside this source closure, that would be new evidence and would reopen this
reachability result.

## Evidence pins

SHA-256 of the reviewed files (paths relative to repository unless absolute):

| File | SHA-256 |
|---|---|
| `src/root/m1C62.c` | `927309d2bf5019e17e58962c7da6a0d45298a2f3bf18fef0b0347cc4498ada6c` |
| `src/S15/m384C.c` | `01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5` |
| `src/S17/m384C.c` | `028adfd17423f115a800315be32a2aaee0f7049e0b8c3211eebd9d65ab7a1351` |
| `src/root/m00DE.c` | `ed0dcfe0256211fd6a2e368deb6ab4eae5df29b582c52966e21fd7dd31c3720c` |
| `src/root/m1B73.asm` | `3097a6b03ff1d8bdfa7d573632d9905de88d754c8b1e047de4014c4f186cb848` |
| `src/root/m1FD2.c` | `f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8` |
| `src/root/m1CE2.c` | `e5c2cb4b8dbe7af6d263072002a49e012b290c1082f0fc877b479728b75bacd3` |
| `src/root/m24AB.c` | `1d263c6e1f242981d7c3e37d839dc481dc75deed45d7d1bcaaa075cad124de7f` |
| `src/root/m277E.c` | `4e928689c743f473c5a007bbbbb5287cdf8728d12e9cae5652b1cb55debf09ee` |
| `src/root/m171C.c` | `31bd9caa243220db2bd1ba940ac8fae7f5d189b2ec95f1662918e9ca2160b10e` |
| `src/root/m0250.c` | `bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b` |
| `src/root/m19DC.c` | `90b0d3a7a6e171bb7395410af72ec10d3a094865c0395824cb744b9ba5a48c8c` |
| `src/root/m195A.asm` | `b634ca4916d811140f6a06b29f731bd323d49f5c50a76ef3afee38a7f23f6a81` |
| `src/root/m1F58.asm` | `9f314c6e964bcb0955c1f3e976819bdbeddf048781c1bb257c30b2c0b25d49d2` |
| `src/root/m205F.c` | `225326bdd127dd3825035ae0fe8434e6677c0ee81203fee2e16bac0cf90fffc6` |
| `src/root/m1B4E.asm` | `a32d75d2d4ea36980b659d26e9ddd86bcde65d9e250ebac4cdc29c0e847c67a2` |
| `src/S00/m3126.asm` | `be7a4a3b0fd9c56c47be50d20c60b0c2835002b7721bd913d36f8183be47ce5a` |
| `src/S00/m31AD.asm` | `5d2ad69ff4affb4be4242e82187065cc5e0b3502cc0cc3e00ad3802ccee2656e` |
| `src/S00/m31AD_2AB4.asm` | `3ef3979a3c35e9e36c4ddc48408bc4cac601ad26f4728e044012a489f831fd55` |
| `src/S01/m3126.asm` | `ac99ea7821999d034e64201798d49dfaf64632f34e5f5dee428c9b6dec01a44a` |
| `src/S02/m3126.asm` | `4291e4084ff26dcee75016b03c1b8d8412129a97ad00787b41ac567c16f5178b` |
| `src/S03/m3126.asm` | `b0b9d296f23b4f8a5b4706008b21b6ad96429636da11bf22ddb2126ee362f2ff` |
| `src/root/m1D8E.c` | `afe9364f319633dd85c276bed18e848a605934156bfbb4fc276d304cd2ec2556` |
| `work/source-only-dos/callback-table-bindings-v1.json` | `457cdc94b7b1c2b07908352e4b736d0de8cb47f8d65e44b475e993e5b93d648d` |
| `work/source-only-dos/callback-table-reviewed-contract-v1.json` | `687b19c934090234f23a129088fede174c97394bceb65f83c83b48ddd61c83d1` |
| `src/root/m0000.c` | `d9ccffbb69c4fdcae55eef918bf420cff81ead6849f67298271c2844e04199f9` |
| `src/root/m295C.c` | `d392b6ce886cfd664a192194b79569bb6a0d4dea8b0bc029ffa9e32ff44add89` |
| `src/root/m28BC.asm` | `361f33c1d86502fef4d43559cb7f424e350eee3fe8a31881ed3c21b4d865f7a5` |
| `layout/functions.json` | `6089a06e18fbe8f0960392cfe30357f7c19c886f38f10f7f115c72d127a756e7` |
| `layout/symbols.json` | `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125` |
| `C:/tools/msc-6.00/STARTUP/dos/crt0dat.asm` | `33eead508c0b2941f9cc95d17ebbda1ba8de196431a90091a8e2f26527ce11e0` |
| `C:/tools/msc-6.00/LIB/llibcr.lib` | `3d0c6ae92972789e87def01fa96351c39216d731d5c880370155c5613d78c884` |

Contexts were generated with `python tools/context.py FUNCTION` (no `--raw`).
No original executable bytes were used as build inputs; no production, canonical,
tooling, packet, or Git files were modified.
