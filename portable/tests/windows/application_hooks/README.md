# Application close hooks: bounded source contract

`evidence/application-close-hooks-next10-v6-20261002.json` records a bounded
original-DOS/native comparison of the actual source close-hook transaction.
The original `f_00BA_0002` registers the recovered before/after hooks; the DOS
run and extracted native bodies produce the same 43 ordered provider/hook
events in each of two initial-state cases, with matching compared source
state: animation handles, cursor/edit
rectangles, edit dimensions, camera clamp, map dirty flag, cache invalidation,
source `g_19CE`, map plane, and tile dimensions.

The proof runs the same transaction with `g_19CE` initialized to both 0 and 1.
In the 0 case both DOS and native change the observed word to 1, establishing
the store rather than merely observing an unchanged default; the 1 case checks
the ordinary initialized state. The source global `g_19CE` is at original DOS
`DS:19CE` (`fd_55B3_19CE`).
`src/root/m0250.c` initializes it to 1 and `f_0250_0E15` writes 1. The Next10
generated `RecoveredState` does not yet declare this global, so the test-local
native storage is seeded to the source initializer and compared against the
actual DOS word. This is not a renderer-only bit or an omitted DOS observation.

The registered sequence is:

* Before close: `win_YardClosed` → `win_ModeControlClosed` →
  `win_CasteControlClosed`.
* At the close boundary: a typed `win_Close(0x1900)` marker.
* After close: `win_CasteControlClosed` → `win_ModeControlClosed` →
  `f_0250_0E15` → `win_MapChanged` → `win_YardClosed`.

The close marker is deliberately an explicit boundary; the test does not claim
to execute the original `win_Close` implementation or establish pixel
equivalence. `f_00BA_0002` takes the source branch with
`fd_50F6_10D0 == 0`, so winheaders file reading and allocation are not
exercised. The fixture has the map and yard-cursor windows open, animation
handles live, MapPlane 2, 16-pixel tile dimensions, known edit/cursor
rectangles, and a controlled camera position.

Reproduce with the checked-in extractor and runner, choosing a unique receipt
filename because the runner refuses to overwrite existing evidence:

```powershell
python portable/tests/windows/application_hooks/extract_application_hooks.py `
  --output build/workers/application_hooks/source_extracted.c
python portable/tests/windows/application_hooks/run_application_hooks.py `
  --report portable/tests/windows/application_hooks/evidence/application-close-hooks-rerun-<unique-name>.json
```

The immutable v6 receipt pins 91 input files (the four source modules, Next10
generated state, oracle and symbol data, probe/runner/extractor, behavior VM,
and its runtime dependencies) with matching pre/post hashes. GCC is
MinGW-w64 GCC 12.2.0; the executable SHA-256 is
`7f1e689f9d384a3a84ffd85eeee08a9b0036e487a467c308d8ab2feec0108451`. Current
test inputs are preserved in
`evidence/application-close-hooks-source-snapshot-v7/`.

The typed provider boundary covers window resource load/draw-hook registration,
application-hook registration, window relationship and map initialization,
clip stack, animation remove/render, window-open queries and rectangles,
cursor erasure, and `_fmemset`. The actual hook bodies perform the state
writes. `fd_50F6_10D2` is the shared cursor rectangle used by map and yard
hooks; `fd_50F6_110C`, `fd_50F6_10E0`, and `fd_50F6_10DE` carry edit
rectangle/dimensions; `fd_55B3_19BE` and `fd_55B3_19C0` supply source tile
width/height; `fd_50F6_0508` is the camera pair. `f_0250_0E15` computes edit
dimensions, stores `g_19CE=1`, and clamps camera state through `f_0250_0F2C`.

The smallest mechanical admission is these ten complete bodies, in original
module order: `f_00BA_0002`, `f_00BA_0211`, `f_00BA_0228`;
`win_YardClosed`, `win_MapChanged`; `f_0250_05CB`, `f_0250_0E15`,
`f_0250_0F2C`; and `win_ModeControlClosed`, `win_CasteControlClosed`. Preserve
the post-hook calls to the *Closed* functions, not the *Changed* functions.
`f_0250_05CB` fills the legacy cache with -1; its backing is a typed test
fixture because that cache is not in the current Next10 state. Real resource
loading/window management, animation implementation, and rendered pixels
remain separate integration work.

This diagnostic copies bodies verbatim and compiles their plain `int`/`long`
locals at host widths. The fixture also views the existing camera word array
through a `struct Pt` pointer. The tested dimensions and camera values agree
with DOS, but this is not admission of those type views into production.
A production conversion must use explicit 16/32-bit source scalars and
lower camera field accesses to the actual array words without incompatible
struct pointer aliasing. The current fixture is compiled without optimization.

Earlier immutable receipts and source snapshots remain preserved. V1 sampled
the wrong contiguous dimension word. V2 fixed that read but omitted original
`DS:19CE`; its comparison failed because native contained a key DOS had not
captured, not because DOS returned zero. V3/v4 passed while treating the
source word as non-DOS state. V5 captured `DS:19CE` but tested only 1→1. V6
adds the 0→1 contrast and compares both initial cases directly.
