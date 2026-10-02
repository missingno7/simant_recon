# Ant list and player helper tests

Build and run the native unit test from the repository root:

```powershell
C:/msys64/mingw64/bin/gcc.exe -std=c11 -O2 -Wall -Wextra -Werror -I portable `
  portable/game/simulation/ants.c portable/tests/ants/test_ants.c `
  -o build/portable/ants-test.exe
build/portable/ants-test.exe
```

Run the bounded original-DOS comparison with `python portable/tests/ants/run_dos_diff.py`.
It executes the frozen original functions only and compares selected list/player state
to the native helpers. The pinned run is recorded in `evidence/ants-dos-diff-final.json`;
the initial 21-case run remains alongside it for reference.

The comparison covers the three direct ant-list appenders, surface-list rebuilding,
black/red list count clears, player-life placement including queen-tail boundaries,
and health clamp/threshold behavior. It does not cover full RandWorld or InitSimYard.
