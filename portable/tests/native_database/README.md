# Current canonical native database/resource checks

Replay with a current complete native conversion report in a fresh result folder:

```powershell
python portable/tests/native_database/run.py `
  --conversion build/current/portable `
  --out build/current/tests/database
```

The adjacent fixtures are self-contained test logic. The current build report
supplies whole canonical TU and native-service paths,
compiler flags and authoritative generated-header precedence. Runtime compilation
uses the current canonical DB/index storage providers, never
`portable/whole_program/state/database.c`, frozen behavior source, or old generated
TUs. GCC dependency files capture the compiled header closure. Reports pin current
canonical source, generated source/header inputs, current service inputs, assets,
compiler, commands and fixture files. Execution writes only to scratch.

The current corpus checks:

- 1,483 index queries with actual pointer/cursor/home/entry observations.
- Actual OpenDB/OpenIndex/DBRecall/CloseDB results for all 840 existing HCEGANT,
  SHARED and SOUND records; every payload compared bytewise with an independent
  test-only Python wire parser and LZSS decoder. Its 840-record aggregate is
  `2cd5f2c76ee8a96e`, matching the retained corpus identity. The expected fixture
  never supplies data to the actual database or handle services. No retired
  PortableDatabase model source/header is compiled or required. All 205 LZSS
  records are included. No fixture sentinel
  is installed for these source lookups.
- Two actual OpenDB/CloseDB 14-byte wire writes, covering a fresh create and a
  dirty existing header. Independent little-endian encodings match the files.
  The fresh process selects zeroed/new or valid source-allocated slots; this does
  not prove arbitrary slot reuse or game SaveRec behavior.
- A whole-TU DBRecall header-offset +1 mutant fails with exit 15; the pointer-
  bearing wire-entry negative fails compilation.

There is an explicit **SEMANTIC / PORT-BLOCKING** exception: native FindIndex
returns NULL at `cursor == count` before testing the one-past entry. The same
whole converted TU with only this guard removed returns a matching reserved row.
Three asset-derived queries demonstrate the changed return value:

| Fixture database | Query ID | Query kind | Insertion rank/count |
|---|---:|---:|---:|
| HCEGANT | -32222 | 148 | 271 |
| SHARED | -32222 | 148 | 449 |
| SOUND | -32222 | 148 | 120 |

The query fixture allocates `count+1` rows and copies the first reserved file
row. Canonical OpenIndex allocates/reads only `count*8` bytes. Thus these three
observations are source-parametric tests with defined fixture storage, not proof
of original game reachability or original adjacent heap contents. Both versions
preserve the insertion cursor and global one-past pointer before the guard; the
returned pointer and returned entry fields differ. A separate two-row synthetic
lookahead-hit/miss fixture checks the same relation directly. Existing-record
recalls reach ranks below count and pass separately.

This suite makes no fresh original-DOS call or native-vs-DOS equivalence claim.
Unproved database `OpenDB[-1]`, `db_handles[4]`, heap adjacency and unavailable EMS
remain outside its acceptance. The separate current runtime suite exercises the
original SaveGame/FileSelect/LoadGame flow and all 307 save-record reads; it does
not establish after-load state or DOS save equivalence.
