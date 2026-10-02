# Portable renderer checks

The C fixture checks indexed primitives, raw/type-3 bitmap parsing, packed
resource drawing, and loaded font rendering against actual HCEGANT assets:

```powershell
gcc -std=c11 -Wall -Wextra -Wconversion -Werror -pedantic `
  portable/game/resources/database.c portable/render/primitives.c `
  portable/render/bitmap.c portable/render/font.c `
  portable/tests/render/test_render.c -o $env:TEMP\simant_render_tests.exe
& $env:TEMP\simant_render_tests.exe assets
```

`evidence/dos_render_differential.py` calls frozen `SIMANT.EXE` entry points
through the Unicorn behavior harness. Its pinned report compares packed
resource 2500's full decompressed header and payload, resource 1200's masked
EGA merge at all eight x-bit shifts, and FONT2 widths and glyph raster. These
checks cover data and logical pixels; they do not claim physical VGA or full
window presentation equivalence.

```powershell
python portable/tests/render/evidence/dos_render_differential.py `
  --output portable/tests/render/evidence/dos-render-differential.json
```
