# S00 graphics driver table and providers

`f_1B4E_0025` (`src/root/m1B4E.asm`) loads the far pointer in `g_3DF4`,
loads the destination address from `g_3DF8`, then stores that same far pointer
25 times (`CX=19h`). `g_3DF4` initially points at `f_1B4E_000C`, the empty
entry. `f_1B4E_0165` copies `CX=32h` words (25 far pointers) from the input
`DS:SI` to the address loaded from `g_3DF8`; `g_3DF8` contains a pointer to
`g_9128`. S00 `o00_31AD_145E` obtains `DS:SI` from `g_20FC` and calls that
copy routine. `g_20FC` points to `DispatchS00` in `src/S00/m3126.asm`.

The table is copied in this exact order:

| Slot | S00 body | Slot | S00 body |
|---|---|---|---|
| g9128 | o00_31AD_1659 | g9154 | o00_31AD_1206 |
| g912C | o00_31AD_166A | g9158 | o00_31AD_1213 |
| g9130 | o00_31AD_168C | g915C | o00_31AD_062A |
| g9134 | o00_31AD_16A9 | g9160 | o00_31AD_062E |
| g9138 | o00_31AD_0122 | g9164 | o00_31AD_0632 |
| g913C | o00_31AD_037C | g9168 | o00_31AD_0636 |
| g9140 | o00_31AD_0522 | g916C | o00_31AD_148C |
| g9144 | o00_31AD_11FB | g9170 | o00_31AD_1499 |
| g9148 | o00_31AD_0550 | g9174 | o00_31AD_0004 |
| g914C | o00_31AD_0CF9 | g9178 | o00_31AD_1481 |
| g9150 | o00_31AD_0D06 | g917C | o00_31AD_0647 |
|  |  | g9180 | o00_31AD_18BA |
|  |  | g9184 | o00_31AD_063C |
|  |  | g9188 | o00_31AD_1950 |

After this table copy, `o00_31AD_1AE7` writes the word `166Ah` to `g_9130`
and `1AC4h` to `g_912C`. Those writes change the active font callbacks: slot
1 becomes the optional custom 6×4 font selector, and slot 2 becomes the BIOS
8×8 font selector. The table defaults are BIOS 8×8 in slot 1 and BIOS 8×14 in
slot 2. The other source mode setup functions `o00_31AD_2AB4` and
`o00_31AD_2AE5` perform the table copy without these later font overrides.

The bounded native providers mirror those contracts. BIOS font bytes are an
explicit external provider input; no glyph bytes are fabricated. The custom
font selector is a source no-op while its pointer view is absent. The patterned
rectangle provider reads the original 256-byte pattern table through a
caller-owned view. The rectangle XOR provider uses the `0x0f` Set/Reset value
and XOR mode selected by `_0394`. Unknown overlay-resident branches remain
fail-closed.

Validation receipts:

- `../graphics-contract-20261003-v23.json`: strict native callback, font,
  pattern, XOR, source ABI, and bounds contracts.
- `graphics-s00-pattern-rect-dos-v2-20261003.json`: 21 original-DOS pattern
  rectangle cases plus 6 original-DOS XOR rectangle cases, comparing
  normalized indexed frames; the pattern view is read from the DOS VM's
  `g_41C0+16` data region. Both receipts pin their source/compiler inputs and
  record pre/post stability.

The differential normalizes the selected VGA GC writes for this bounded
640×480 source profile. It does not claim full VGA hardware emulation, loaded
overlay behavior, or BIOS font bitmap equivalence.
