# Shared ideal-machine integration,2026-11-14

Status: **partial; tapes retained**. The latest owner-approved
[sound-off run](sound-off.md) has12/18 strict state lanes and18/18 frame lanes
equal; the remaining rain IDs depend on uninitialized allocation payload.
It also fixes DOS admission of direct keyboard-modifier byte reads. The
measurements below are the retained earlier sound-on experiment.
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
