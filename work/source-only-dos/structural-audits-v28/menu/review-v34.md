# DOS menu resource-bound review v34

**Disposition: investigation only; `menu-table-cross-owner-layout` stays OPEN.** No production source or canonical ownership file was changed.

The `f_1FD2_0663` source walks `g_6054->titles` twice with null sentinels and no cap. It writes `fd_50F6_46BC[i]` before recording `g_604C`, then resets `i` and writes `fd_50F6_46A8[i]`. The views alias at ten-entry offsets: `widths[10] == fd_50F6_46D0`, `xpos[10] == widths[0]`, and `xpos[20] == fd_50F6_46D0`. The neighboring `fd_50F6_46D2` table remains outside this review.

`IBMInitStuff` selects the resource from screen width: at `g_3DB2 == 320`, it tries MENU object 1 and falls back to object 0; otherwise it loads object 0. `db_LoadObject` searches the currently open databases in order. The source opens optional `language`, then `shared`, optional `lrshare` in modes 2/4, then the adapter database; `sound` opens later. The adapter database name is the selected prefix plus `nt`.

The supplied DAT/NDX pairs are HCEGANT, SHARED and SOUND. Their indexes contain no kind-6 object 1. SHARED contains kind-6 object 0. Using the LZSS decoder shape pinned in `src/root/m1B05.asm`, its MENU record expands to 514 bytes and has five non-null title pointers followed by a null sentinel; its five active item tables have counts 8, 7, 8, 6 and 6. The expanded payload is pinned by SHA-256 in the JSON. This establishes the bound for this exact object 0, whose five-title writer pass does not reach the alias offsets.

The observed payload is resource/index-owned: C selects and relocates the loaded pointer graph, while the count comes from the database object. The canonical historical draft at `src/root/m1986.c` keeps a scaffold, but the effective source-only set registers `evidence/behavior/functions/FindIndex/module.c` as a strict, whole-module `BEHAVIOR_EXACT_CONFIRMED` source for `root:1986`; its lookup behavior is closed under the reviewed valid-index preconditions. Optional language and mode databases are absent from the supplied assets, so object 1's count and any first-hit resource in those databases remain open. The remaining gate is resource coverage and count, not unresolved lookup control flow.

## Current source and registry pins

Full SHA-256 values below pin the exact files reviewed; the JSON also records sizes and the DAT/NDX hashes.

| File | SHA-256 |
|---|---|
| `src/root/m1FD2.c` | `f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8` |
| `src/S17/m384C.c` | `028adfd17423f115a800315be32a2aaee0f7049e0b8c3211eebd9d65ab7a1351` |
| `src/S10/m35F5.c` | `69be1d6a9649e99102131c702e1920b6e84acc0c1b4cd737d2a047552f917ed5` |
| `src/S20/m39F1.c` | `6fd0a02991a29325f214049a8a8961aaee4bc65fbf760b296e63a6ac8f6fbe7b` |
| `src/root/m205F.c` | `225326bdd127dd3825035ae0fe8434e6677c0ee81203fee2e16bac0cf90fffc6` |
| `src/root/m1A53.c` | `6bb066ea34c3721c90956a5b7e8849cb3c5916628a842c2684a8c0137154b698` |
| `src/root/m1A28.c` | `5db49039ef64717680153a4b9445554b58ab2abf8a3c3fd9d67e6573af58a740` |
| `src/root/m1986.c` | `c6278f0729f2c7e8c1b36c423c7c4ab081573b8c26a8604ab1ee78036365fc96` |
| `src/root/m19A9.c` | `552ca373a3a3721885915acd0a95e2126b8405b0c555f02d1833381331cda523` |
| `src/root/m1B05.asm` | `3124ef4a45c572a54529bd5a57cd9225b40fdcafadd63c6b06cb748683cacca4` |
| `src/root/m15F8.c` | `d6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a` |
| `evidence/behavior/functions/o10_35F5_0384/contracts/host-service-v1/module.c` | `4b9dda15dbea1c8fd204ed95d4cb6a909751a59d0517909e90c4626cad3c7888` |
| `evidence/behavior/functions/FindIndex/module.c` | `1af5252fe8449eeca44b4099fe4a4bd1ff5ab24521c7a888253adfdd4554ac5a` |
| `build/workers/dos_delay_word_owner_v33/source-addendum-v33.json` | `a6fad53037d90f7dca76828a1c45a73569eb8e8877736dbf0be90b303dde990a` |
| `build/workers/dos_delay_word_owner_v33/source-addendum-v33.md` | `c8ebc194e070ba7774cf11602818e65d02b33976077c91a00ed60ac34d95e073` |
| `layout/symbols.json` | `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125` |
| `layout/manifest.json` | `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50` |
| `layout/oracle.lock.json` | `2c6d9e98c688621ad49a08c78d0e0968f4076b036be56ec0738217b533ccde13` |
| `layout/functions.json` | `6089a06e18fbe8f0960392cfe30357f7c19c886f38f10f7f115c72d127a756e7` |
| `work/source-only-dos/static-completeness/index-v1.json` | `092b3a15aaaf99737020c0c00e2a4340514dda3f0e2ff45369d1fa0a316d9a3a` |
| `work/source-only-dos/static-completeness/FindIndex.json` | `d9f61367df4d79b2bd07e284140b8c9a34db80dda5b1d4bceac7f31ffd6ec5fc` |
| `evidence/behavior/manifest.json` | `dae79bdf74d7660e7e2eb47e8b463a9576c8d74a8e6ccd9e91af6d51f871ecea` |
| `evidence/behavior/functions/FindIndex/evidence.json` | `8de2f5ff812103303c0240d944214bbd0e996a5c9f26ac1b7987abba81a52e1e` |

No executable or resource bytes, decoded strings, or resource dumps are embedded in this worker artifact. The resource parse was performed in memory and retained as hashes/counts only.
