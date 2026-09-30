# Handoff: state and next steps (2026-09-30)

Read this first, then README.md, AGENTS.md, docs/worker-brief.md, docs/codegen-rules.md.
`python tools/validate.py` is the single source of truth (writes docs/progress.md); every
number below is from the validated, pushed tree (origin/main).

## 1. Where the reconstruction stands

| Measure (docs/progress.md) | Value |
|---|---:|
| exact C functions / bytes | 1,227 / 224,248 |
| exact genuine assembly (symbolic MASM, all 378 ASM claims classified genuine) | 50,441 (+1,481 code-segment data) |
| ASM used as a workaround for original C | 0 |
| complete translation units (TU) / with proven cross-function relocation order | 88 / 87 |
| historical MSC runtime accepted | 90 members, 12,339 bytes code + 1,559 data |
| data accepted (far 77,846) | 111,308 bytes |
| unresolved game code | 28,628 bytes |
| unresolved data | 3,181 bytes |
| RTLink/Plus manager (third-party, no library available) | 17,001 bytes debt |

Proof levels are reported separately: bytes in complete vs partial modules, steered
(8,119 B, dummy constructs, disclosed), layout-inferred (source layout chosen from
relocation-order / identifier-count evidence), within-group order pending, asm-transcribed,
opaque data, runtime words derived from the original.

**Whole-build harness** (`python tools/link.py`, docs/whole-build.md): (a) own bytes placed
from freshly compiled objects; (b) the hybrid EXE (own bytes + explicitly labelled debt copied
from the original) is **byte-identical to SIMANT.EXE** (SHA-256 aa0596c6…4f11) — this proves
our contributions sit at the right addresses with no gaps/overlaps; hybrid bytes are never
counted as reconstruction. (c) independent historical link: see §4.

## 2. Established facts (all with probes / evidence)

* Compiler: **MSC 6.00AX** (`CL /EM`, DOS-extended; profile `msc600ax`, headless DOSBox-X),
  CONFIRMED (VER-3). Headers from the verified 6.00A retail disks (55 files pinned).
* Per-file debug option: `/Zi` in most modules (ZI-1/2/3), none in 277E, 0798, 0BE8, S05:35F5,
  295C, 208F; `/Zd` in 1C62. Decide per module by relocation-order evidence.
* Assembly: MASM 5.10 reproduction; ASM-1/ASM-2/IDIOM-1 classify genuine assembly.
* Linker: Pocket Soft RTLink/Plus (late 1991). VEC-1 (vectors per symbol via ALWAYS list;
  NEVER for direct references), DATAPTR-1, relocation groups per frame by target symbol,
  group order = hash of the symbol-record creation index (not names; docs/level-c-link.md).
* ~40 compiler codegen rules (docs/codegen-rules.md, evidence/codegen/*.json, reproduced by
  validate): slot order, CSE temps, identifier-count sensitivity (period 17, SYM-1), NAME-3/4,
  REG-2..6, ALIAS-1, STORE-1, DEAD-1/2, LOOP-1, PROTO-1/2, SPLIT-1, TERN-1, BSS-1/2, FARSEG-1, …

## 3. Remaining game code (~28.6 KB, ~40 functions) — all hard residues

Current residue per function: `build/workers/resI/survey.txt` plus the later reports
(resJ: `build/workers/resJ/residue.txt`, sub-dirs dle/s06/ovl/s23/mem; autosearch:
`build/workers/autosearch/results.md`). Best drafts sit in SCAFFOLD blocks of the canonical
sources or in those directories. Largest items:

| Module | Open | Notes |
|---|---|---|
| root:0250 | 1018, 129E, DrawSpider, DrawCurBalloons, DrawBalloons | 7–10 missing natural identifiers before 1018 (idscan); DrawCurBalloons exact at +5..11 |
| S25:3BA4 | DoAntMoveY (+1035, 1686) | 13 B slot swap tx/tattr; steered stand-in holds 10 claims' record order |
| S10:35F5 | 0384 | 1746 vs 1759 |
| S09:35F5 | FileSelect | 30 B, 4 causes; Win16 drafts exist in D:\Prog\simantw_recon\build\lift\open\FileSelect.c (unread) |
| S23:39C7 | GetStyleTextHeight, PrintStyleTextInRect, DisplayCard | lineH kept in memory |
| root:171C | 0CF4, 0160 (2 B `mov dx,es` vs `cx`: 32-bit arithmetic lead), 09CC, 0ADC, 0FBC | draft build/workers/resJ/mem/best_m171C.c |
| others | S13 InvertPatch/DrawColonyBars, S14 CalcScore, S17 0039, S24 drawHistGraph, S04/S12 cursor, 1E57 038E, 259D DrawBitMap, 0CDB SpiderScan, 2815 0165/0275, 290D 000E, 284A 0138, 23E6 0000, 1C62 0415, 0E2E LessonDone, S08 RandWorld, 1A96, 1986, 20E8 0903, 23AE, 2505 0453, 29D6, 295C 0391, S15 0239, 293A 017F, S05:3663 DoExpMenu | see survey |

Recommended next pass: run the rule-driven search first —
`python tools/autosearch.py --all` (or per function), continuing from
`build/workers/autosearch/results.json` — then hand-work what it cannot solve. Twins
(A/B/R functions, Win16 sources D:\Prog\simantw_recon\src\recovered) are the best evidence
for statement form (REG-6).

## 4. Ready-to-install proposals (reviewed, not yet installed)

1. **CODEALIGN-1 + 19A9 boundary fix** — `build/workers/align/` (FINDINGS.txt, patch/,
   migrate.sh). The accepted 19A9 extent starts at an odd address that no linker produces;
   its three unreferenced `retf` stubs (19A95–97) belong to 1986 (MS LINK 5.10 and RTLink
   6.10 both reproduce the original only that way). Install order: run
   `bash build/workers/align/sandbox_run.sh` (~25 min) to confirm, then apply the patch and
   `migrate.sh` together (validate refuses 19A9 between the two). Also fixes
   tools/rtlink.py's linker-profile lookup and puts late root objects (2CFB MEMHOOK) in the
   LIBRARY list, as the original link did.
2. **promote.py `--note`** — `build/workers/autosearch/patch/promote-note.patch` (journal
   free-text, e.g. rules applied by autosearch).
3. Worth adding to shared tools: `build/workers/resJ/mem/multi.py` (20–30 variants of one
   function per compile, analysis only).

## 5. Level (c): independent historical link

* The Dec 1991 RTLink/Plus (4.x/5.0) was **not found** (archive.org, WinWorld, Vetusware).
  Clean route: ask Pocket Soft (today RTPatch). Available research instruments (C:\tools,
  provenance.json each; kept outside Git): RTLink/Plus 6.10 (1993; BBS dump, warez-scene copy —
  research only), RTLink for Clipper 3.11/3.13 (WinWorld, SHA-512 verified).
* `python tools/rtlink.py` / `tools/link.py --rtlink-trial` performs a trial link with 6.10:
  83/85 complete modules placed at accepted addresses, section table fields match, relocation
  sets and all non-fixup bytes of the fully reconstructed overlay sections match; manager bytes
  and relocation group order need the 1991 linker plus the complete object set in original
  command-line order. Link-script inputs read from the original (ALWAYS/NEVER, areas,
  PRELOAD/RELOAD) are labelled in build/workers/rtlink/linkscripts/SIMANT_derived.lnk.

## 6. Data (3,181 B unresolved)

Owner-undecidable small ranges (~72 B: DGROUP 2100–2117, 2328–2337, 5A96–5AAF, 68AC–68B5,
56FE, 5A28), S09 save table 4E4B (2,464 B, far) and S05:3663/S17 module data (with their
open functions). FAR_BSS 50F6 (19,408 zero bytes) sizes: 180 B pinned, 4,300 consistent,
14,928 unverified (`tools/farbss.py`). Opaque-data count (5,161 B) also includes structured
numeric tables; refine the lint to skip typed struct initialisers.

## 7. Operating rules that matter (details in AGENTS.md / docs/worker-brief.md)

* Canonical files have one writer: promote.py (sources/manifest), rename.py/symbols.py/
  functions.py (registries), the supervisor for tools/ and docs/. Workers work in
  build/workers/NAME/ and hand tool changes over as patches.
* Git Bash: `MSYS_NO_PATHCONV=1`, one flag per argument; never write Python edits through
  heredocs with backslash escapes; never kill processes you did not start (DOSBox-X runs are
  shared with other projects on this machine).
* Names: Win16 names need xver CONFIRMED/HIGH or a decision with ≥2 anchors; DOS-only names
  follow rule DOS-1 (own identifier-shaped string, DOS build only); third-party names (e.g.
  S21 VIDEO_ID lineage) are held until an exact primary listing is in hand.
* User decisions (2026-09-30): original assembly reproduced exactly counts as finished; ASM
  standing in for C is reported separately; prefer the historically correct toolchain and
  acquire tools (with provenance) instead of emulating around them; pushing to origin is allowed.
* Checkpoint pattern: `python tools/validate.py --no-tests` (full run with tests before
  releases), commit only on PASS, then `git push`; `python tools/link.py` to re-check the hybrid.
