# Monochrome pattern tail: unresolved owner and conditional escaped read

`_g_8ED8` remains an unresolved source-storage import consumed by S15 `LoadMonoPats` and the four S01 monochrome assembly routines. The admitted 24-byte `g_8EC0` prefix supplies no tail allocation authority. This evidence does not admit an owner, rename storage, or establish that a running game reaches the fixture input.

## Current source and access domain

S15 loads second resource `(10010,22)`, obtains its count from plain-char header byte 1 and copies inverted bytes to `g_8ED8`. Original CBW/SHL3 and signed JL allow 0..1016 writes for headers 0..127, and zero writes for headers 128..255. That generic producer domain does not determine an allocation extent.

Every S01 source index is a zero-extended byte from LODSB. The pattern read formula is `SS:(_g_8ED8 + 8*row + (selector&7) + lane)`.

| Body | Source bytes per call | Lanes | Selector in actual DOS caller |
|---|---:|---:|---|
| 328E:000A | 128 | 0..3 | Width128 at BP+0E, hence selector0 |
| 328E:009D | 64 | 0..3 | y at BP+10 |
| 328E:012C | 128 | 0..1 | y at BP+0E |
| 328E:01D5 | 64 | 0..1 | y at BP+0E |

`src/S12/m384C.c:o12_384C_03D0` passes `(src,dst,width,y)`. Its original argument pushes are S12:03EB..041C. `src/S04/m35F5.c:Mini_MakeTable` passes `(src,dst,y)` directly to the two miniature routines at S04:04B0..04D5. These distinct frames explain why the main 000A caller's selector is zero despite its generic assembly accepting a masked argument.

The in-bounds mapping table `fd_3D57_054E[208]` has maximum72 and yields72 at indices94,95,102. Visible other monochrome tables have smaller maxima: 04CE=29,061E=40,0656=49. These are static table facts, without a complete proof of raw map/life input bounds or reachability.

For a hypothetical584-byte owner, the required consumer bounds are:

- Main000A: row<=72, because selector0.
- 009D: `8*row + (y&7) + 3 <584`, with its width64 source domain proved separately.
- Mini012C/01D5: `8*row + (y&7) + 1 <584`; row72 therefore excludes selector7.

## Bounded original-instruction witness

`asm_witness.py` executes all four unmodified original S01 bodies in explicitly test-owned memory with SS=DS=DGROUP. It stops immediately before authentic RETF after register restores, and asserts pattern read counts512/256/256/128. Its zero pattern prefix and adjacent marker are fixture state, never an owner proposal or copied source storage.

At row72, main000A with width128 reads through579 and ignores the marker at584. Miniature y6 reads582/583 and also ignores the marker. Miniature y7 reads583/584: changing only fixture byte584 from00 toFF changes the second output plane from00 toFF. A source-byte255 contrast in009D reaches displacement2049. This proves a conditional escaped read with an observable effect. It does not prove actual gameplay supplies odd miniature top, assign ownership to byte584, or verify the return ABI.

## Resource corroboration and next premise

The read-only matching-resource facts and input hashes are in `resource-facts.json`. Win16 MWINNT kind22 id10010 unpacks to586 bytes, header0049, then73x8=584 pattern bytes. MAPSYM `_DMPat` at DGROUP:26A0 is corroborated by the second-resource producer and all four Win16 monochrome consumers. The Win16 recovered `DMPat[584]` extent derives from a next-public MAPSYM span; neither that span nor the payload count proves a DOS allocation.

DOS startup concatenates stem `mono` and suffix `nt` in the relevant modes. The checked local DOS corpus lacks MONONT.NDX/DAT and contains no kind22 records. The exact resource premises still needed are MONONT kind22 id10010, kind0 window20, and kind9 mode3/5/7.

`OpenMiniMapWin` sets row step2 in odd display modes; `Mini_DrawMapI` starts at `win_GetObjRect(1401).top` and draws64 rows. Step2 preserves starting parity. Win16 MWINNT window20 x/y relation5 references `win_Open` parameters, so its stored top22 does not prove final caller parity. DOS HCEGANT differs and cannot substitute for MONONT. `win_LoadAllWindows`, `win_LoadWindow`, and `win_Open` can supply/restore/recalculate origins and move the window.

Allocation admission still requires an authoritative DOS source object/type/extent, producer bounds, complete caller row/selector closure, and initialization/lifetime/escaped-view proof. A minimum write, adjacency gap, resource length, guessed capacity/sentinel, or compiler owner-size experiment is insufficient. Existing symbolic DGROUP/SS base admission can be reused; this report makes no new base or owner claim.

## Reproduction

After installation, from any working directory:

```text
python <repository>/evidence/canonical/monochrome-owner/asm_witness.py --out build/workers/monochrome-owner/asm-witness-run-001
```

The runner locates the repository from its own ancestors. `--out` is mandatory, repository-relative unless absolute, must resolve strictly beneath `build/`, and must not exist. It writes only `asm-witness.json` there after the bounded assertions pass. Receipts pin the current program/source inputs, immutable original EXE and S01 contribution, current `tools/exe.py`, runner and Unicorn module inputs. Unicorn must be installed or available in the current `build/behavior/deps` dependency directory. No output is written into evidence or an existing receipt directory.
