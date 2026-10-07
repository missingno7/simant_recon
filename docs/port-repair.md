# SDL3 port repair method

**Architecture:** readable native canonical C is the shipped source, in the spirit of
stunts_recon. No static recompilation. The closed canonical DOS build
(`functional-source-oracle-v1`) is the oracle; original machine code and the
differential tools are debugging aids, not a proof obligation.

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
