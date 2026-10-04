# Sound selector / table-layout audit v21

**Status:** `UNRESOLVED`; `root_reviewed: false`; gates unchanged. Static source/layout audit only.

`/s9` is syntactically accepted but outside the detector, setup, and cleanup tables (each has indices 0–8). It cannot be silently treated as a valid post-init mode, and the source provides no range guard. No clamp, tenth entry, or padding hypothesis is proposed.

## Selector flow

`IBMInitStuff` sets the selector to `-1`, may load a digit from config, then processes slash arguments in order. A lowercase `/s` followed by a digit 0–9 overwrites the selector; invalid values do not, and trailing characters after the digit are ignored. `main` calls `IBMInitStuff`, opens the `sound` database, then calls `f_00DF_0004`. For selector `-1`, that function calls `f_293A_0006`, which probes detector entries 8 down to 1 and returns the first true index or 0. Explicit `/s0` returns before initialization. Selectors 1–9 enter `f_277E_0000`; mode 7 skips its detector lookup, otherwise a false detector result falls back to 1. The valid table domain is 0–8.

## Exact overreads

* **Detector, `/s9`:** `f_277E_0000` computes `74DA + 9*4 = 74FE`. In accepted `root:293A` same-TU `_DATA`, nine 4-byte far function pointers occupy 40 bytes together with the next 4-byte object, initialized `fd_55B3_74FE = fd_50F6_01F0`. The fixed source/object placement preserves that alias and pointer fixup. The 7-word saved state is zero at main under the root-reviewed storage contract. The indexed far call therefore enters the saved-state object as code. Its return, value, and side effects are unproved; this is the first unresolved edge.
* **Setup, if the invalid detector call returns:** `g_68B6[9]` computes `68B6 + 9*4 = 68DA`, exactly `g_68DA[0]`, `f_277E_0938` (empty). Both nine-entry tables are adjacent in the accepted `root:277E` TU’s 72-byte `_DATA`. If the detector returns false, mode falls back to 1; if it returns nonzero with the caller state intact, mode 9 reaches the setup alias and can be saved as 9. These are conditional machine paths, not a proof that the data-as-code call returns.
* **Cleanup, if mode 9 was saved:** `f_277E_0154` computes `68DA + 9*4 = 68FE`. The current manifest places separate `root:2815` `_DATA` at 55B3:68FE; `g_68FE` begins `{0,1,2,6,...}`. Those first four chars form pointer words offset `0100`, segment `0602` when interpreted as a far function pointer. This edge depends on cross-TU fixed allocation/manifest adjacency, not same-TU source/fixups; the bytes have no function meaning in source and no valid return is established.

## Reachability, aliases, and scope

The only source caller of `f_277E_0000` is `f_00DF_0004`; automatic detection is only reached from there. The cleanup table is consumed by `f_277E_0154`, called from `o15_384C_0152` when the selector is nonzero; `Punt` and main’s cancellation path reach that handler. Before successful sound initialization, the saved word remains startup zero and cleanup selects entry 0. A later cleanup after a hypothetical returned `/s9` initialization can select entry 9. The only other saved-state views are report reads 0–6, the initializer’s word-0 write, its 1–6 clears/setup writes, and word-0 reads in `f_0000_046F`/`f_277E_0154`; the 14-byte storage admission covers those data indices but does not make an out-of-bounds detector call valid. No other source caller, table consumer, or alias escape was found.

The pre-init fifth-sound-open/Punt proof is separate. This audit does not claim all Punt routes are post-init: early DB/display failure can reach cleanup while the saved word is still zero. It also does not reinterpret timer routines as no-ops. Successful setup retains timer/PIT/DOS calls; `f_277E_0154` retains cleanup and `f_28BC_04E0(0)`. Fatal-path DOSBox comparison remains outstanding.

## Pinned inputs

Current source snapshots are under `pinned-sources/` and hash-checked against the source files. The current uncommitted v20 build report is a mutable observation (160 TUs, `INCOMPLETE`, SHA-256 `be2871f8acfdcce12ec4026d673a38661a3c67c21bace19d590c8ef8a4a6b61d`), not a claim about HEAD. The four `tools/context.py` queries were non-raw instruction/call/frame evidence only. Mutable manifest/symbol/tool hashes, selected build objects, and the admitted storage-contract identity are recorded in `receipt.json`.

No source, tests, docs, layout, promotion, Git, or build/search inputs were changed.


## Reviewed metadata revision: v21-build-input-verification-1

After the initial receipt, I reread the BE287 build-report row and hashed the actual source, generated source, and object files for `root:277E`, `root:293A`, `root:2815`, and `root:00DF`. All twelve file hashes and sizes match the report. I corrected one transcription error in `root:277E.generated_source_sha256` (old receipt value `4e928689e9b8d9d128cc97cca3da7dcf0ad863dbb5c6df587c601530cbe4ec5e6`; verified/report value `4e928689c743f473c5a007bbbbb5287cdf8728d12e9cae5652b1cb55debf09ee`). The four triplets are preserved under `pinned-build-inputs/`; exact report and file paths/hashes are in `receipt.json`. The report remained BE287 during the check. No context outputs were repinned or modified.
