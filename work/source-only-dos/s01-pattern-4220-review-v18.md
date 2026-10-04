# S01 4220h binding candidate v18 (pending review)

This is a bounded, unadmitted one-site binding candidate. The current S01 control is reconstructed from the canonical source through the exact accepted source-binding, external-frame, and local-frame packets. The rebuilt control object matches the directly pinned active U004 object; the build report is retained as an observational run input.

- Receipt: `work/source-only-dos/s01-pattern-4220-proof-candidate-v18.json` (`c6e8b283ceedc2e01eabaf3ca911473872c1ed26f979836d4276dad4e8c80d52`).
- Candidate binding packet: `work/source-only-dos/s01-pattern-4220-bindings-candidate-v18.json` (`6617bbf158e9a602f45bf9e083580f73a08b38446e0df838ae716bf88fd6d345`). Root review is false.
- Apply-chain counts: 3 base edits; 18 external-frame edits/36 frame sites; 2 local-frame edits/sites. Replayed text equals current U004 exactly; the observed report row binding merge check is True.
- U004 control object reproduces the current build object; candidate adds one DGROUP-framed OFFSET16 fixup at `S01A_TEXT:05A8`.
- Candidate module extents, segment definitions, groups, publics, externals, and every other ordered fixup match the U004 control. Only the displacement word changes from `20 42` to `00 00`.
- The complete alias census classified 42 direct `_g_3DE4/_g_3DE5` occurrences across 12 pinned source files; only the canonical/effective setter writes through the overlapping word, and no direct byte writer or unclassified alias remains. Its `70F0h` mask bounds `_g_3DE5` to 00h..70h by 10h.
- The selector contributes 0,2,4,6; the loop transition `+2; AND 00F7h` cycles within that phase band for any positive count, so the largest displacement from `_g_4220` is 76h.
- `_g_4220` is the existing 16-byte zero row at `_g_41D0+80`; the reachable addresses continue into following existing rows but remain below the bank's 256-byte end. The complete owner U086 source/object is rebuilt and matched to the directly pinned active provider source/object.
- RTLink 4.00 and 6.10 each pass the shifted-DGROUP group-frame case and detect both a segment-frame negative and a +1 base negative. The boundary contrast uses the actual adjacent 44h row byte after the existing 16-byte zero view.
- The fixture has one separate 16-byte prefix solely to shift DGROUP. Empty support labels satisfy the complete provider's unrelated, unexecuted imports; they add no owner storage.
- Candidate linker/runtime outputs are in `build/workers/dos_s01_pattern_4220/durable-v18`; the full root:1B4E provider is used as-is, and the checker adds only a 16-byte shift prefix, no owner storage.
- No canonical or production build input is edited; this packet does not resolve the wider numeric-address gate. The 8ED8h mono base/frame/extent work remains open.
