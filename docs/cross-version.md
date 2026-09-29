# DOS ↔ Win16 correspondence

`tools/xver.py build` extracts features from **both original executables** and ranks
pairs against the Win16 reconstruction at `D:\Prog\simantw_recon` (MAPSYM names, cards,
recovered sources). Results: `evidence/cross_version/simantw_correspondence.json`.
Reviewed decisions: `evidence/cross_version/decisions.json` (keys are DOS addresses).
DOS results useful to the Win16 project: `evidence/cross_version/dos_findings.json`.

The Win16 build is a **semantic** oracle only. Acceptance is always DOS compiler output.

## Features (symmetric, from the executables)

* **Strings**: NUL-terminated DGROUP literals addressed by an immediate (`mov r,imm`,
  `push imm`). Shared rare literals are the strongest anchors (diagnostics such as
  "cache table full, can't load object").
* **Constants**: immediates ≥ 0x100 that are not string addresses; rare ones weigh most.
* **Runtime signature**: called C-runtime functions (DOS: located `LLIBCR` publics; Win16:
  MAPSYM CRT names).
* **Switch cardinality**, size, callers/callees and **ordered call sequences** (site order).
* Machine-code similarity is deliberately not used (different compiler, ABI, platform).

## Methods and confidence

| Method | Produces |
|---|---|
| `features-v1`: rare strings/constants/runtime/switch score, mutual best | HIGH (≥2 rare strings, or 1 + rare constant), MEDIUM, LOW |
| `neighbourhood-v1`: anchored callers/callees of c map onto those of c′, unique and reciprocal, iterated | HIGH (≥3 anchors and size ratio 0.5–2), MEDIUM (2) |
| `callseq-alignment-v1`: single-unknown gaps between aligned known calls | votes |
| `reviewed` (`decisions.json`) | CONFIRMED / REJECTED, with written evidence |

CONFIRMED needs at least two independent anchors (e.g. unique diagnostics plus the same
call order, or TU-level structure plus a unique constant). Names are transferred into
`layout/symbols.json` only by `xver.py apply-names` and only for CONFIRMED pairs, HIGH
pairs anchored by rare strings/constants, and neighbourhood HIGH pairs with ≥4 agreeing
anchors; each rename records the evidence in its `history`.

## State (2026-09-29)

21 CONFIRMED, 66 HIGH, 65 MEDIUM, 52 LOW pairs; 60 of 1,240 DOS code names are Win16
names (reviewed decisions plus the `apply-names` policy); the rest keep address names. Notable structure:

* DOS module 0093 **is** Win16 unit `simone_1506` (SetSRandSeed…SRand256), plus three
  DOS-only two-draw helpers and a BIOS tick reader.
* The DOS window system shares its API with the Win16 build's own `win_*` layer
  (`win_LoadWindow`, `win_GetObjRect`, `win_SetObjBitmap`, …) — the Windows port kept
  Maxis' window-object model on top of real HWNDs. This is the key to the future
  DOS-window-system replacement.
* Database/resource layer (`OpenDB`, `OpenIndex`, `db_LoadObject`, `DBRecall`,
  `ch_*` cache) and fonts (`font_ReadFont`, `font_InitFonts`) correspond one-to-one.
* DOS `Punt` = Win16 `Punt` (fatal error sink, 86 DOS callers).

## Feeding Win16 back

`dos_findings.json` lists DOS functions that are byte-exact *and* CONFIRMED/HIGH paired,
with the natural MSC 6 source. Example: DOS `SRand2..SRand256` are inline-asm bodies that
leave the result in AX with no result local; SimAntW's accepted form introduced one.
