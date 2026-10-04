# Post-load alias resolution addendum v23

This addendum corrects the v22 wording that the `LoadGame` post-read callees “have no definitions in the current source tree.” They are declared imports under historical code names, but the symbol registry binds each through a code-address alias to an accepted source definition. The three callees are **not** selector sanitizers; the restored spider state remains unbounded by this post-load chain.

## Address resolution

The pinned v20 source graph has 156 unique source paths: 127 canonical plus 29 effective strict sources. The three actual provider source files below are members of that graph, and their current SHA-256 values match the graph pins. This resolution follows `layout/symbols.json` `alias_of` code-address entries to the manifest's accepted definitions; it does not infer absence from an exact-name grep or from scaffold state.

| `LoadGame` import | Registry alias and address | Accepted definition |
|---|---|---|
| `f_15D9_009C` | `EditMessage`, `root:15D9:009C` | `EditMessage`, `src/root/m15D9.c:46`; exact natural claim in extent-bearing `root:15D9` |
| `o11_35F5_0000` | `SetMenuEntries`, `S11:35F5:0000` | `SetMenuEntries`, `src/S11/m35F5.c:9`; exact natural claim in extent-bearing `S11:35F5` |
| `o11_35F5_0088` | `PauseGame`, `S11:35F5:0088` | `PauseGame`, `src/S11/m35F5.c:30`; exact natural claim in extent-bearing `S11:35F5` |

All three names appear as `extern` declarations in `src/S09/m35F5.c:30-32` and are called in `LoadGame` at lines 125, 130, and 131. Those declarations are imports, not missing bodies. Manifest modules `root:15D9` and `S11:35F5` have extents and empty scaffold lists; their relevant claims are `EditMessage` (size 344), `SetMenuEntries` (136), `PauseGame` (22), and `SetPause` (239 at `S11:35F5:009E`). Machine-readable registry, source-pin, and claim receipts are in [`alias-resolution-v23.json`](alias-resolution-v23.json).

## Effect on restored selectors

The calls do not normalize `SMode`, `Scycle`, or `fd_50F6_1004`:

- `f_15D9_009C(0L, -2L, 1)` resolves to `EditMessage`. Mode 1 bypasses its mode-0 guard; negative duration sets the two message deadlines to the sentinel and updates message pointers/refresh flags. The body does not access spider selectors.
- `o11_35F5_0000()` resolves to `SetMenuEntries`, which only updates speed/pause/menu entries and their text. Its helpers `SetMenuItemState` and `f_1FD2_0135` write menu storage.
- `o11_35F5_0088(1)` resolves to `PauseGame(1)`, which delegates to `SetPause(1)`. `SetPause` calls `EndLifeTransferMode` or `EndTargetMode` only for value 0, so that branch is skipped. The value-1 path sets pause/message, clipping, and selected-window-object state, then refreshes menus. These are UI effects, not selector range checks or selector writes.
- `o09_35F5_0DBB` is defined at `src/S09/m35F5.c:563`; it rebuilds life maps and UI/yard state and likewise does not touch the three selectors.

`LoadGame` restores each selector from a 2-byte `SaveRec` entry (`src/S09/m35F5.c:1145-1149`) without a range check, then invokes the three aliases and the visible rebuild (`src/S09/m35F5.c:125-132`). Because the actual post-load bodies leave those bytes unconstrained, the saved selectors can still fall outside the normal-source-state domains established in v22. This resolves the missing-definition claim while preserving the same precise resource-domain frontier: malformed/restored selector values are not bounded before the reachable DrawSpider path, and the alternate resource bundles remain unavailable.

No probe, compiler run, game execution, production change, or admission change was made. The original v22 parser and header-observation JSON are unchanged.
