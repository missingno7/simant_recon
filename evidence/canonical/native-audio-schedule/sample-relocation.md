# The three requested DAC cases are DOS heap-move artifacts

The byte differs, but it is not a native decoder, volume-table, mixer,
resampler or sample-cache content defect. IRQ0 interrupts
`mem_slide_next_block_down` inside `mem_copy_paragraphs`'s overlapping forward
`REP MOVSW`. The live sample handle still points at the old source block.
The copy has already overwritten that byte in the old storage; the destination
and the decoded sample captured at voice setup both contain the native byte.

| Lane / entry | Object / position | DOS | Native, decoded payload and copied destination | Move down / copied bytes |
|---|---|---:|---:|---|
| ant-commands/original 598 | 14 / 2587 | 132 | 72 | 1328 / 5064 of 5232 |
| full-game/canonical 618 | 14 / 2545 | 20 | 148 | 1040 / 4122 of 5232 |
| interactive-play/original 832 | 36 / 756 | 126 | 123 | 400 / 1468 of 1904 |

Each wrong source byte equals the original payload byte at `position + move_down`:
3915, 3585 and 1156 respectively. Both the damaged source cell and the correct
copied cell lie within the already copied destination prefix. Saved FLAGS have
IF set. The hardware return PC is the actual `REP MOVSW`, and the helper's saved
return and arguments independently bind its caller and both copy addresses.
The handle is not updated until after the helper returns, as the DOS source and
its instructions show. No interrupt, handle, register or expected sample value
is injected to obtain this observation.

The actual linked native volume table equals all 2048 observed DOS table bytes;
the observation executable has the same table. Entire decoded start payloads
match native. All three native output positions, rates and volume rows match,
and native emits the unchanged payload byte. Reproducing the transient wrong
DOS read would reproduce CPU/IRQ placement during relocation, not repair a port
sample bug. No producer algorithm was changed.

The read-only probes retain full memory/GPR diagnostics in ignored worker output.
The accepted claims concern conventional RAM/GPR values and the captured output;
no complete device microstate invariance is claimed for memory snapshots. Every
probe's state hashes, service order, raw OUT sequence and content prefix equal
the ordinary US reference through entries 600, 620 and 834 respectively. Prefix
controls and source/executable/observer/capture identities are in
[sample-relocation.json](sample-relocation.json). The analysis script and build
recipes are pinned there and retained under `build/workers/audio-content/`.

Actual emitted bytes are not normalized away: the literal content verdict keeps
these AUDIO_DIFFERENCE rows. This closes the requested port-bug attribution for
these three first differences, not every later divergence in their lanes.
