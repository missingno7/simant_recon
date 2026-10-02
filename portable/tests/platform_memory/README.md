# Native DOS memory-helper boundary

`portable/platform/memory.c` exposes fixed-width host-pointer adapters for the
original large-model helpers. `_fmemcpy` is a forward word-copy followed by
an optional final byte, matching runtime `root:29F4:281A`; overlapping ranges
therefore preserve the DOS helper's forward corruption pattern. `_fmemmove`
matches `root:29F4:26F4` and copies backward only when a later destination
overlaps the source. Do not replace one with the other.

`portable/game/recovered/memory_adapter.c` provides the recovered-core symbol
names. `BlockMove(source,destination,count)` accepts the generated caller's
`int32_t` count, then passes the low 16 bits to `_fmemcpy`: `root:0244:0000`
reads only `[bp+0E]`, while `root:m0EC1` declares the caller count as `long`.
The test passes `0x10013` and confirms the original wrapper copies 19 bytes.
`ABS` uses the DOS signed 16-bit ABI; the `INT16_MIN` case returns `INT16_MIN`
after 16-bit wrap.

The C fixture includes overlap direction, zero count, adapter names, and ABS
endpoints. The direct Unicorn runner executes the frozen runtime entries plus
the original `BlockMove`/`ABS` wrappers and compares destination bytes and
return values. It checks same-segment contiguous buffers and does not model
DOS far-pointer wrap normalization or invalid pointers.

```powershell
gcc -std=c11 -Wall -Wextra -Wconversion -Werror -pedantic `
  portable/platform/memory.c portable/game/recovered/memory_adapter.c `
  portable/tests/platform_memory/test_memory.c -o $env:TEMP\platform_memory_tests.exe
& $env:TEMP\platform_memory_tests.exe
python portable/tests/platform_memory/evidence/dos_memory_differential.py `
  --output portable/tests/platform_memory/evidence/dos-memory-differential.json
```
