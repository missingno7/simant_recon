# g_8CCB runtime-owner audit (read-only; no admission)

Scope: test whether `g_8CCB` at `55B3:8CCB` is an interior/high-byte view of selected MSC runtime storage. No production, tool, canonical, manifest, evidence, or Git file was changed. No original byte sequence was copied into this report. Runtime placement derivation is kept separate from source-only claims.

## Canonical view

- `layout/symbols.json` registers `g_8CCB` as a byte at segment `55B3`, offset decimal `36043` (`0x8CCB`), grounded by `f_1C62_06A6`.
- `src/root/m1C62.c:329` declares `extern char near g_8CCB;`; `:350-353` contains the error-message selector. The function first checks `err > sys_nerr || err < 0`, then returns `g_567A[g_8CCB]`. This is a signed-char index into the critical-error text table, not an `errno` read. The only canonical text references are the declaration and that indexed read; no canonical write is present.
- The `root:1C62` accepted `_BSS` contribution is `55B3:8CBE` length 4, and `root:1CE2` begins at `55B3:8CCC` length 8. These neighboring placements do not establish the owner of `8CCB`; I use runtime public/common/BSS placement records below for the runtime-alias test.

## Accepted runtime source and public evidence

Pinned inputs: `layout/manifest.json` SHA-256 `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`; `layout/symbols.json` `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`; accepted runtime libraries `llibcr.lib` `3d0c6ae92972789e87def01fa96351c39216d731d5c880370155c5613d78c884` and `libh.lib` `a4492e8f63da409d949643fd448f29e65e2cc9a8f2deea977372177bbe0ad818`.

The accepted runtime manifest selects 90 code members and 8 data-only members. The existing `build/runtime/verify.json` records 90/90 code members and 38/38 file-backed DGROUP data segments exact. Its `dos\\crt0dat.asm` data contribution is `55B3:771E`, size `0x56`; its `_errno` PUBDEF is offset `0x1C`, giving `55B3:773A`. This agrees with `layout/symbols.json`â€™s `errno` address.

The installed MSC source corroborates type and initialization: `C:\\tools\\msc-6.00\\INCLUDE\\errno.h:30` declares `extern int near ... volatile errno`; `C:\\tools\\msc-6.00\\STARTUP\\dos\\crt0dat.asm:188` defines `globalW errno,0`. It is a 16-bit word, initially zero. `_doserrno` is a separate word (`crt0dat.asm:212`, accepted public at `55B3:7745`). The source hashes are `errno.h` `1db2af1fcfbcb33cf1be4f97430cdf8194bf1d60f586c1f432832d69aa5bfe91` and `crt0dat.asm` `33eead508c0b2941f9cc95d17ebbda1ba8de196431a90091a8e2f26527ce11e0`.

Selected runtime code does write these error values, but at those separate addresses: pinned `llibcr.lib` member `dos\\dosret.asm` (index 12, SHA-256 `cd1526b0f6398bdd10acd3b86252bab5984992706f0980e17c50f36a689c5a17`) has an OMF fixup to `__doserrno` at code `+0x29` in `mov byte ptr [__doserrno],al`, and a fixup to `_errno` at `+0x4E` in `mov word ptr [errno],ax`. Selected `dos\\getcwd.c` also has word stores to `_errno`. Neither word is at or near `8CCA/8CCB`.

## Selected versus unselected runtime storage

I inspected all 343 LLIBCR and 80 LIBH OMF modules and distinguished them using the accepted runtime manifest. The selected OMF set has one COMDEF: `_file.c` (index 26), near `__bufin`, length 512. A read-only `runtime.verify_all()` plus `runtime.verify_data(..., communals=...)` query against the existing image operands places it at `55B3:92E4` with two agreeing anchors (end `0x94E4`). It does not cover `8CCA/8CCB`. The runtime verify result also has `_edata=0x8B9E` and `_end=0x94F0`; that broad BSS interval is not used as an owner claim.

The selected runtime has five nonempty near-BSS segments relevant to DGROUP placement. Their original-derived segment starts and OMF lengths are:

| Selected member/segment | Start | Length | End |
|---|---:|---:|---:|
| `sprintf.c` / `_BSS` | `0x8E06` | `0x0C` | `0x8E12` |
| `vsprintf.c` / `_BSS` | `0x8E12` | `0x0C` | `0x8E1E` |
| `asctime.c` / `_BSS` | `0x8E1E` | `0x1A` | `0x8E38` |
| `tzset.c` / `_BSS` | `0x8E38` | `0x02` | `0x8E3A` |
| `onexit.asm` / `XO` | `0x8E3A` | `0x80` | `0x8EBA` |

The starts above are derived from agreeing fixups in the exact selected runtime code records (`build/runtime/verify.json` `placements`), not from a gap or numeric-literal absence. The `crt0dat.asm` `XOB`/`XOE` bounds are at `0x8E3A`/`0x8EBA`. The selected runtimeâ€™s nonempty BSS owners are therefore all above `8CCB`.

A full selected-library PUBDEF/COMDEF scan finds no selected runtime public or common at `55B3:8CCA` or `55B3:8CCB`; the only relevant selected public is `_errno` at `773A`, and the only near common is `__bufin` at `92E4`. Unselected archive members may contain their own publics, but they are absent from this accepted imageâ€™s selected runtime set and cannot own these bytes in this link.

## Finding and limit

No selected MSC runtime public, near common, or placed BSS segment owns a word beginning at `55B3:8CCA`, or a byte at `55B3:8CCB`. In particular, `g_8CCB` is **not** a high-byte view of MSC `errno`, `_doserrno`, or the selected `__bufin` communal. The runtime-alias candidate is rejected for the current selected link.

This does not identify who owns or initializes `g_8CCB`; its canonical source still only shows a byte extern and the table-index read. No new scalar owner or initialization claim follows from the runtime rejection.
