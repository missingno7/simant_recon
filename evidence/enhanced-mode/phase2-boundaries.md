# Phase 2 boundary audit

Authored implementation map; no copied game art or original bytes.

* `portable/whole_program/enhanced/workspace.c` includes only its native model,
  libc string/stdio/storage operations. Its panel IDs are unrelated to source
  logical IDs. No canonical routine, timing service, global or asset is imported.
* `platform/sdl3/native_workspace.c` imports const snapshot/asset projections.
  Its only gameplay submission is the explicit primary N01 menu action.
  Docking, tab/focus, visibility, float, splitter, preset and persistence routes
  do not use that submission. Layout operations do not read source time.
* `host.c` consumes workspace mouse/keys before hosted event translation and
  supplies neutral physical state; deterministic replay keeps its existing
  channel. Rendering the root exits before the DOS raster upload. Source-mode
  geometry changes still update hidden graphics support, without resizing the
  native workspace frame.
* `native_windows.c` bypasses hosted presentation for native ordinary panel
  families. It retains source lifecycle/dialog windows, popup compatibility and
  their existing dispatcher until phases 3-5. No source-lifetime mutation was
  added for native layout.
* World panels share phase 1 pure cell/overlay composition and immutable assets.
  Inspectors read all-plane arrays already in `EnhancedWorldSnapshot`. No plane
  global is temporarily changed, and extra views do not run original producers.
* `portable/tests/enhanced/invariance.py` adds Win32 stationary/repeat/stress
  lanes. Every existing raw comparison remains active. The probe observes actual
  layout, persistence and snapshot-copy counters, not a synthetic pass flag.
* `portable/tests/enhanced/workspace.py` checks native handles/keyboard/recovery,
  UIA and normal shipped startup, and captures actual native window contents.
  UIA failures remain failures; the separate stock-button baseline diagnoses the
  environment and does not turn a failure into acceptance.

The final scratch report `build/workers/enhanced-phase2/RESULT.md` is the runtime
receipt index. Static separation, model validity, bounded gameplay comparisons,
raw equality, native accessibility and hardware validation are different claims.
