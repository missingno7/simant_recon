# Resource database tests

Build and run from the repository root with MSYS2 GCC:

```sh
C:/msys64/mingw64/bin/gcc.exe -std=c11 -Wall -Wextra -Wconversion -Werror \
  portable/game/resources/database.c portable/tests/resources/database_test.c \
  -o portable/tests/resources/database_test.exe
portable/tests/resources/database_test.exe assets
C:/msys64/mingw64/bin/gcc.exe -std=c11 -Wall -Wextra -Wconversion -Werror \
  portable/game/resources/database.c portable/game/resources/tiles.c \
  portable/tests/resources/tiles_test.c -o portable/tests/resources/tiles_test.exe
portable/tests/resources/tiles_test.exe assets
C:/msys64/mingw64/bin/gcc.exe -std=c11 -O2 -Wall -Wextra -Wconversion -Werror \
  -shared -o build/workers/database_dos_differential/database.dll \
  portable/game/resources/database.c
python portable/tests/resources/evidence/database_dos_differential.py
```

The test loads every active record in the pinned HCEGANT, SHARED, and SOUND
indexes, which covers the raw, `FF FF` wrapper, and LZSS database storage forms.
It also checks key resources used by the initial port and the exposed one-past
FindIndex compatibility boundary. Asset identities are listed in
`ASSET_SHA256.md`; original asset files stay in the ignored repository `assets/`
directory.

The retained direct-DOS differential report is
`evidence/database-dos-differential.json`. Its producer calls the frozen DOS
`FindIndex`, `f_1B05_0008`, and `f_1B05_0046` entry points under Unicorn, with
database rows from the pinned assets. It compares all 205 LZSS records byte for
byte and probes actual NDX records, signed query boundaries, and each file's
first reserved lookahead entry. Three out-of-active-range queries match that
reserved one-past entry in DOS; the portable bounded lookup reports not-found,
while `portable_db_find_index_compat` exposes the historical result when given
the adjacent entry explicitly. This is a porting diagnostic and makes no
historical proof-category claim.

`tiles.h` exposes kind-9 objects 9/10 plus EMS chunks 15–20 as owned opaque byte
records. Ground selection 0 loads object 10 and selection 1 loads object 9.
Independently, `LoadTiles` maps 15–17 with `g_19D2` (surface) and 18–20 with
`g_19E2` (nest); `f_0250_05EB` selects the page map from `MapPlane`. This keeps
the two source-defined roles separate. No pixel geometry is claimed: the
previous inference from 0x5000 bytes and a 0xA0 pointer multiplier was not
enough to establish tile dimensions or row layout, and has been removed. No VGA
page or EMS manager is represented in the portable API. The rejected inference
and source anchors are preserved in `evidence/tile-layout-review.json`.
