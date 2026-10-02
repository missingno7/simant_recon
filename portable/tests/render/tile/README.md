# Kind-9 tile raster slice

`tile_raster.c` decodes a 16x16 EGA tile from the DOS kind-9 ground atlas and
composites one EMS life frame over indexed pixels. It intentionally does not
model EGA ports, display placement, the source VRAM atlas, tile flipping, or
the full map renderer.

The ground layout follows `src/S00/m31AD.asm::_o00_31AD_18BA` (lines
3307–3386): each tile has 16 rows, each row has four two-byte plane words,
and the source cursor advances 0x80 bytes per tile. The life layout and
transparent selection follow `src/S00/m31AD_2AB4.asm::_o00_31AD_2B1A` (lines
88–802): the unrolled body reads one mask word and four life-plane words for
each of 16 rows, and computes `base XOR ((overlay XOR base) AND mask)`. This
is a 160-byte source frame. `_o00_31AD_2FDA` (lines 804–826) sends the 128-byte
composite scratch to the 16x16 blitter.

The C test checks source-shaped synthetic pixels and loads every tile from
actual kind-9 objects 9/10 and every 160-byte frame from objects 15–20. The
companion DOS differential executes original `_o00_31AD_2B1A` with 128 random
base/life cases plus the first and last actual frame of each object 15–20; all
128 output scratch bytes match. It supplies the bytes that the selected EGA
read plane would return at `DS:g3DB0+col`, so it validates the helper's pixel
mask/plane contract under normalized readback. It excludes physical EGA
read-map behavior, atlas address placement, and `_2FDA` display clipping.

```powershell
gcc -std=c11 -Wall -Wextra -Wconversion -Werror -pedantic `
  portable/game/resources/database.c portable/render/primitives.c `
  portable/render/tile_raster.c portable/tests/render/tile/test_tile_raster.c `
  -o $env:TEMP\simant_tile_tests.exe
& $env:TEMP\simant_tile_tests.exe assets
```
