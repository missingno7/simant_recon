# S15 text-pointer lifetime sweep

Target: `o15_384C_0239` in `S15:384C`. The frozen whole-module seed is `s15-base.c` (SHA-256 `01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5`). Its baseline is the documented 326-byte, 137-instruction body. The original listing returns the far text pointer at `+0x3E`, saves its segment at `[bp-6]` at `+0x40`, and pushes that word for `win_PrintTextInRect` at `+0xA0`; the seed emits the same instructions but uses `[bp-2]` at both sites.

The listing and call semantics justified a bounded LIFE-2-style hypothesis: a real zero-valued call argument initialized before the text setup might retain an interfering home, while IDs passed to window calls might be held across the same phases. The sweep used only arguments that replace existing literal call arguments. It did not add unused reads or padding. The shared argument controls covered `int`, `unsigned`, and `unsigned char` locals initialized at five points before or across pointer conversion, font selection, and the optional rectangle-clear call. They used the argument for the actual rectangle-clear and text calls, with a subset also using it for the font reset. Other controls held the actual `0x2100`/`0x2101` window IDs across their existing calls. Five additional controls used distinct clear and print arguments with separate phase lifetimes.

`results.json` records 48 whole-module controls: the baseline and 47 candidate sources. `phase-split-results.json` records five further whole-module controls. All 53 compile successfully. None matches the target. The baseline and four argument controls retain only the same two operand-byte differences; other controls change length to 329, 330, 331, or 334 bytes. Every control preserves the seven accepted peer functions and the `_DATA` (213 bytes) and `CONST` (24 bytes) contributions. No complete-TU extent was claimed or changed.

Target-only `search.py` confirms the base and the closest argument variant both remain 137 instructions with the same two-byte mismatch at `+0x42`. The final `promote.py --verify-only` transcript confirms all seven existing claims and both data contributions, then refuses the new claim because the target bytes still differ at `+0x42`. No promotion was run. These failures do not establish assembly or compiler exclusion.

The explicit control count is 53 whole-module variants. Including the stack-slot diagnostic, three target-only search compiles (the first search invocation compiled its baseline before a generated-path typo interrupted the second source), and one verify-only compile, the total was 58 compiler attempts, below the 60-control cap. The path typo was corrected; the retained `search-results.json` contains the successful baseline/candidate rerun.

## Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `s15-base.c` | `01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5` |
| `run_lifetimes.py` | `d79b2b9f192ed8d979b1c7db38c29fc1ac4e2986a7e08898b39397ff4bed2e44` |
| `results.json` | `70fd11c7d4abdf3029ec4454366cf4bdd0be2d89d9b4491510b421ca322096b4` |
| `run_phase_split.py` | `e6e36e001d5653b8261ed43c6aa621c2409845502a1ae3e32cf641dbad14fb6b` |
| `phase-split-results.json` | `7336f133ae9f2be8431382da82a9df61acb1ff2098f234b6f9984518798b872d` |
| `search-results.json` | `887cc1a0ee61ed4afaeec63ae781d22660c119d2f702ab4df6ff04eea8472482` |
| `promote-verify-only.log` | `d52466f40002f9307206dd81cff30ee0f4e74c724dfb48c4e1641fe2d71a5f3f` |

The repository status also showed concurrent edits to `tools/diag.py`, `tools/match.py`, and `tests/test_diag.py`; this worker did not modify them. All authored drafts, generators, and reports are under `build/workers/fleet_s15/`.
