# Shared ideal-machine integration, 2026-11-15

Status: **18/18 gameplay lanes equal in each sound mode; 22/22 playback lanes
equal; tapes retained**. The latest [shared observation run](shared-observation.md)
uses the same keyboard-context and animation-identity rules for every ideal-v1
variant. All state, frames and raw audio pass. The combined cached check took
246.14 s; sample timestamp tolerance remains 1 ns. See the
[retirement proposal](tape-retirement-proposal.md) for the final replacement
set and its coverage limits. No retirement or upper-test switch occurs here.
The earlier clock repair remains documented in [sound-on-clock-v3.md](sound-on-clock-v3.md).

## Retained earlier integration findings

Status: **sound-off state/frame parity; tapes retained**. The latest owner-approved
[identity-pattern run](identity-results.json) has18/18 state and18/18 frame lanes
equal, with eight additional scalar holders and raw ID diagnostics. The
[proof](animation-identity.md) and [retirement proposal](tape-retirement-proposal.md)
record the boundary and next review. The [earlier raw sound-off run](sound-off.md)
also fixed DOS admission of direct keyboard-modifier byte reads. Measurements
below are the retained earlier sound-on experiment; audio remains separate.
The production timer now follows source
fast/slow programming at exact device instants, including chain phase and the
last partial PCM frame. ISA bus/status/reset uses the shared zero-latency clock.

The full untaped corpus has2/18 equal state lanes,16/18 equal frame lanes and
0/18 equal exact per-entry audio lanes. All26128 entries and152 checkpoints
complete. [Results](results.json) retain the first fields/audio differences and
per-lane recording/check costs. Nothing is normalized or reclassified. Native
CH context and pause/modal timing still differ; Random17 has143 changed pixels
at its final checkpoint. The current v10 upper-layer check and every tape remain.

Specification and reproduction: [ideal-v1](../../../portable/tests/acceptance/ideal/README.md).
Detailed implementation, directed snapshots, CPU-budget control, fresh-suite
receipts and new-file registration list: build/workers/ideal-check/SOUND_ON_RESULT.md.
The current report is build/workers/ideal-check/RESULT.md.
Active DMA/AdLib PIT-latch and general mask/status-only coverage remain open.
