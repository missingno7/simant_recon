# g_5A97 pre-write dominance receipt (scratch; no admission)

Date: 2026-10-03. Scope: whether source-visible startup can observe `g_5A97` before the first config/command-line write. No original-image bytes were opened or copied. No canonical/production files changed.

## Pinned source basis

The current canonical sources are accepted `EXACT_NATURAL` claims in `layout/manifest.json`:

- `src/root/m15F8.c` (`main`), SHA-256 `d6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a`.
- `src/root/m00F8.c` (`f_00F8_0543`, `f_00F8_0585`), SHA-256 `4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a`.
- `src/root/m1A96.c` (`ch_SetCacheHooks`), SHA-256 `c57124b9d75ea77eb30158c09a71550862cf7081ceed625a2550a26a262bfdfa`.
- `src/S15/m384C.c` (`o15_384C_0125`), SHA-256 `01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5`.
- `src/S20/m39F1.c` (`IBMInitStuff`, `ReadWord`, `SkipWords`, `ReadConfig`), SHA-256 `6fd0a02991a29325f214049a8a8961aaee4bc65fbf760b296e63a6ac8f6fbe7b`.
- `src/root/m205F.c` (`f_205F_0004`), SHA-256 `225326bdd127dd3825035ae0fe8434e6677c0ee81203fee2e16bac0cf90fffc6`.

The earlier pinned full-source scanner is `work/source-only-dos/near-state-debt-audit.py` (SHA-256 `a765712d2e119abf8696f047e4d467264be632cf595131e161cdc2ae033f8637`). Its input pins include canonical manifests/symbols and the registered BEHAVIOR_EXACT manifest/effective implementation sources; the derived `build/workers/dos_near_state_debt_review/source-scan.json` is SHA-256 `384b929eb50ce5832934871a143da4b85f838e4d6ed536cbe4492d3660e04b79`. That scan finds no `g_5A97` address-taking, pointer arithmetic, or indexed use; the one broad-regex apparent hit in `m2662.c:496` is a false positive (`g_5A97` is a later boolean term after `*pic`).

## Dominance and exits

- `src/root/m15F8.c:74-86`: the pre-config `install.exe` open loop can print and `exit(1|2)` before `IBMInitStuff`; its only selector occurrence in `main` is the read at line 95, after `IBMInitStuff` returns.
- `src/root/m15F8.c:88-92`: signals 0x15 and 2 are set to ignore (`1L`); then `f_00F8_0585`, `o15_384C_0125`, and `IBMInitStuff` are called. `f_00F8_0585` (`m00F8.c:343-346`) only installs the cache hook; `ch_SetCacheHooks` (`m1A96.c:280-285`) only stores callback pointers. Its callback `f_00F8_0543` (`m00F8.c:328-339`) reads only the two cache-pointer globals. `o15_384C_0125` (`m384C.c:66-82`) performs BIOS INT 13h drive-reset calls and contains no selector reference.
- `src/S20/m39F1.c:68-69`: `IBMInitStuff` calls `ReadConfig` before any selector read. Command-line `/d` cases at lines 82-114 may overwrite the selector, but are after `ReadConfig`.
- `src/S20/m39F1.c:216-253`: config open failure and invalid-mode paths print/exit without returning. For a returning path, the recognized `mode` cases at lines 223-247 each write `g_5A97`; unchecked read failures can only yield either a recognized mode that is then written or the default exit. Language read/close errors occur before the mode switch but do not read the selector. This notes a pre-existing local-input robustness issue without imputing any selector value.
- The first selector read is `src/S20/m39F1.c:141`, after config assignment, command-line handling, memory check, cwd and optional language-database work, and unconditional `db_SetDataBase("shared")`. A memory/error exit at lines 125-127 occurs after the config write. `_harderr` is not installed until line 154, after this first read and after `f_205F_0004`.
- `src/root/m205F.c:132-138` handles the signed `-1` config sentinel: invalid/no detected mode exits before proceeding; otherwise it writes the detected mode. Later selector dispatch/indexing follows.
- Repository-wide canonical/registered-source search finds no other vector installer or pre-read error-handler registration: the only game `signal()` calls are the two ignored dispositions above; `_harderr` is installed only at `m39F1.c:154`; genuine interrupt ASM handlers exist but are not installed by the pre-read call sequence. This is bounded source inspection, not a model of arbitrary external DOS hardware behavior.

Thus the source-visible startup path either exits without a selector read, or executes `ReadConfig`/`/d` assignment before the first read. This argument does not rely on a presumed pre-main 0 or FF value.

## Typed views and limits

Canonical declarations use `extern char near g_5A97` in startup/mode code and `extern unsigned char near g_5A97` in a subset of consumers; `src/root/m1FBD.asm:13,38` compares the byte to 6. The assigned domain is the config/command-line values `-1,0,2,3,4,5,6,7,8`, then the detected modes in `m205F.c`. Signed `-1` is deliberately read by signed comparisons in the mode path. Unsigned consumers found by the source scan use only low-bit masks and equality tests against nonnegative byte values (`==2`, `==6`); those operations are raw-byte-compatible for the assigned domain, including 0xFF. No pointer escapes or element indexing were found.

## Blocker / no admission

The requested two-entry source-built trace through the actual first consumer (`db_SetDataBase` call selection at `m39F1.c:140-145`) was not run. A faithful executable integration needs the real database open/cache path; replacing that game function with a recording fake would violate the no-game-stub constraint, while linking the database chain is outside this bounded audit. Therefore this receipt supports first-write dominance statically but does **not** claim the requested runtime trace or recommend source-owner admission. It also makes no claim about original pre-main byte contents, original storage ownership, or original initialization beyond non-observability along the source-visible path.
