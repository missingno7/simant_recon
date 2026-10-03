# Whole-program shared database integration check

`run_shared_database.py` compiles the currently generated complete `root_m1986.c`
translation unit with `portable/whole_program/state/database.c` and invokes its
actual `FindIndex` function. The file-backed fixture copies active 8-byte NDX
rows and the actual first reserved row from HCEGANT, SHARED, and SOUND. The
runner verifies every byte survives the native `IndexEntry` struct copy, then
compares the actual cursor, returned pointer rank and returned entry fields, and
the shared global pointer home against an independent signed-id / unsigned-kind
table partition.

The checked-in result is a diagnostic integration check, not a fresh DOS run or
an acceptance registration. The prior direct DOS comparison remains the
separate `portable/tests/resources/evidence/database-dos-differential.json`
packet, which records 1,454 zero-mismatch original-DOS cases.

FindIndex reads `index[count]` after a miss whose insertion rank is exactly the
active count. The fixture provides the real reserved row for that read. This
records the behavior without asserting arbitrary one-past memory safety. A
negative compile control rejects a legacy entry whose host pointer expands the
wire row beyond eight bytes.

Replay in a fresh directory (the runner refuses to overwrite):

```powershell
python portable/tests/whole_program/database/run_shared_database.py `
  --out portable/tests/whole_program/database/evidence/shared-db-fresh
```

