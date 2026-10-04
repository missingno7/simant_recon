# S01:328E / 8ED8 worker receipt

Status: root-false and unresolved. The target code remains a complete accepted ASM TU; no source-owned storage type or extent is established for `g_8ED8`.

The current source traces the producer to `LoadMonoPats`, which loads `(0x271A, 0x16)` and copies an inverted header-sized payload to `g_8ED8`. The exact resource row is absent from the supplied set. S12 installs S01 entries `000A` and `009D`; S04 calls `012C` and `01D5` directly. Visible mini-map generation yields pattern values through `0x48`, but that only bounds part of the source route. The signed SS/DGROUP packet has no S01:328E sites, so the entry stack proof remains open.

See [receipt.json](receipt.json) for evidence hashes, exact arithmetic ranges, and the four remaining questions. No linker or emulator was run.
