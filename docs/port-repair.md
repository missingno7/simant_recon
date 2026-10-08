# SDL3 port repair method

**Architecture:** readable native canonical C is the shipped source, in the spirit of
stunts_recon. No static recompilation. The closed canonical DOS build
(`functional-source-oracle-v1`) is the oracle; original machine code and the
differential tools are debugging aids, not a proof obligation.

## Layers and oracles

```
original SIMANT.EXE            primary oracle: historical behavior, machine semantics
  -> matching canonical DOS     secondary oracle: readable source of game logic/state
  -> mechanical projection      representation only: widths, ABI, pointers, ASM-to-C
  -> SDL3 platform layer        host services replacing DOS/BIOS/hardware
  -> native presentation        future native windows/UI over the same game core
```

* **Ownership.** Canonical source owns game behavior, the projection owns
  representation conversion, the platform layer owns host services, presentation
  owns presentation. Higher layers never reimplement game logic; they consume
  generated projections, thin adapters and explicit interfaces, so a fix below
  propagates upward by rebuilding, never by repeating it by hand.
* **Diagnose downward.** From a symptom, compare each layer with the one below:
  presentation -> platform -> projection -> canonical DOS -> original EXE. Stop at
  the first layer that differs from the correct output of the layer beneath it,
  fix it there and rebuild upward. Never patch the visible symptom first and never
  compensate in a higher layer for a defect below it.
* **Matched source is historical.** If the original and canonical DOS agree and
  native differs, the defect is above the matching layer (projection, ABI,
  compiler-semantic preservation, platform, presentation). Do not modify matched
  canonical source to suit the native compiler or to clean up awkward, undefined
  or MSC/x86-dependent behavior; encode the needed preservation (overflow, AX
  results, adjacency, folding) in the projection. Canonical source changes only on
  original-binary evidence that the reconstruction is wrong (incomplete or
  misscoped match, misattributed fixups/data, a disproved source hypothesis, or
  canonical DOS disagreeing with the original in the supported domain). Historical
  bugs stay historical; exposing, normalizing or excluding them on the modern
  platform is a separate, explicit platform decision.
* **Keep interfaces corrigible.** Contracts expose semantics, not our temporary
  mistakes; when a lower assumption proves wrong, fix the contract and its
  consumers instead of keeping a compatibility shim. Each layer stays independently
  buildable and checkable. Published oracle checkpoints stay immutable.

## Modern Windows presentation (`--windows`)

The single-window SDL3 build is the accepted baseline (`sdl3-baseline-v1`). The
modern presentation runs the same executable and game with selected logical
windows as native SDL windows; without `--windows` nothing changes.

* **Boundary.** DOS composites all logical windows into one VGA screen: m1E57
  computes each window's visible region from the stack `g_5702`, and
  `clip_SetWin` selects it. Win16 SimAnt replaces exactly this with native windows
  (its `clip_SetWin` is empty; each window draws through its own DC). Here
  `platform/window_hosting.c` observes cross-module calls into the m1E57 clip
  entry points (`-Wl,--wrap`, bodies unchanged), gives each hosted window its own
  VGA plane set (`graphics_vga.c` routes each aperture byte per pixel) and an
  unoccluded clip list; shared windows keep the canonical occlusion, computed by
  `f_1E57_038E` over their sub-stack. Window records, the stack, hit testing,
  event dispatch and draw hooks stay canonical.
* **Hosting** (`platform/sdl3/native_windows.c`, Win16 contracts from
  simantw_recon `docs/portable-windows-reference.md` §0): created on the first
  `win_Open`, hidden on `win_Close`, reused; owned top-level windows (owner: the
  main window) at one global `--scale`. As in Win16 `win_Open`, the title object
  (object 1, type 0x0c/0x12) becomes the native caption and its strip leaves the
  client area; flag 4 gives the close button, flag 8 a sizing frame. Native close
  and resize act through the game's own chrome hot boxes (close box `0xf083`,
  resize icon `0xf084` / `o26_39C7_0671`) as timed synthetic input, so window
  state and size rules stay canonical. Window-local input maps to logical screen
  space; a click on a window that is not on top raises it and is eaten (Win16
  WM_MOUSEACTIVATE, DOS `f_218D_0451` via a visible point). The OS cursor replaces
  the software cursor (Win16 class cursor IDC_ARROW). The main SDL window stays
  the desktop (menu bar, dialogs, shared windows).
* **Tests.** `portable/tests/runtime/run_windows.py`; replay lines `op@ID` address
  hosted windows in client-local coordinates, `close@ID` and `resize@ID W H` the
  native frame, and `--debug` records them.

## Closure target: the normal shipped game

Shipped assets and configuration, normal VGA gameplay, keyboard/mouse input, the
supported Sound Blaster configuration, menus and dialogs, starting a game and real
gameplay, sustained simulation, Save/Load, ordinary successful execution on a modern
host. The SDL3 port is done when it launches normally, plays normally, matches the
DOS oracle's game/simulation behavior over meaningful scenarios, saves and reloads
correctly, runs sustained gameplay without divergence or crash, keeps video, input
and audio working, and has no known observable discrepancy in this domain.

## Loop

1. Build and run the real SDL3 executable through the normal game flow into play.
2. Compare observable behavior with the DOS oracle (`portable/tests/acceptance/`
   deterministic replay: logical game state, SaveRec, RNG, audio command stream).
3. Take the first observable divergence; check original vs canonical DOS vs native
   only as far as needed to know which side is wrong.
4. Fix it at its root cause, preferring mechanical ABI/type conversion,
   ASM-to-readable-C projection, platform boundaries and SDL adapters. Canonical
   game algorithms change only with evidence that the canonical source is wrong.
   If a general converter fix cleanly covers the bug's class, apply it; otherwise
   fix what supported gameplay observes and move on.
5. Add a focused regression; rerun the scenario; repeat.

## Not blockers

A difference does not block SDL3 closure merely because pointer representations,
heap layout or stack/register residue differ without an observable consumer, a
DOS BIOS/device quirk is irrelevant to the SDL3 platform, malformed or custom
resources reach an old out-of-bounds case, or an expression is unproven over its
full theoretical type range with no supported gameplay difference. Record such
findings briefly as unsupported-domain notes; do not open proof campaigns for them.
