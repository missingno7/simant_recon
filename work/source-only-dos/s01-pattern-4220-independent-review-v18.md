# Independent S01 4220h integration review (v18)

## Decision

Accept the v18 evidence as a bounded candidate for one S01 symbolic-address binding. Hold production admission until the candidate is normalized into a root-reviewed packet and the closed production hook below is implemented. This review does not close the broader numeric-address audit or prove absence of arbitrary run-time pointer aliases.

## Reproduction and site

The isolated copy of `s01-pattern-4220-probe-v18.py` was rerun with outputs redirected into this worker. It succeeded (`all_required_checks_pass=true`, `root_reviewed=false`) using pinned MASM 5.10, RTLink 4.00 and 6.10, DOSBox-X, and the accepted MSC runtime libraries. Receipt SHA-256: `ba9329a69ced8db4f534253408ab76dd732a30411e952ca9702ff3aa79ec386c`.

The canonical S01 source (`src/S01/m3126.asm`, SHA-256 `ac99ea7821999d034e64201798d49dfaf64632f34e5f5dee428c9b6dec01a44a`) plus the accepted `source-bindings-v1`, `driver-ss-frame-bindings-v1`, and `driver-local-frame-bindings-v1` packets replays exactly to active generated `U004.asm` (SHA-256 `f14c1ebb3391f9188e388105916979f3b3a1c5c9a6a0222686bf15dd404edccb`). Packet counts are 3 base edits, 18 external-frame edits/36 fixups, and 2 local-frame edits/fixups; effective merged binding SHA-256 is `29c681098d2d1c6b897fe7cafbc736011ff75ff07a6d17d219094bbc3cababab`.

The only proposed source operation is canonical line 792 / active generated line 800 in `_o01_3126_0523`:

```asm
mov bh, byte ptr ss:[bx+4220h]
```

becoming a generated-only scoped symbol use:

```asm
assume ss:DGROUP
mov bh, byte ptr ss:[bx+_g_4220]
assume ss:nothing
```

MASM leaves instruction length and segment extent unchanged. The candidate adds exactly one external OFFSET16 fixup at `S01A_TEXT:05A8`: target `_g_4220`, frame group `DGROUP`, displacement/addend zero, frame method 1, target method 2. The control displacement is `20 42`; the candidate displacement is `00 00`. The independently rebuilt control OBJ is byte-identical to the active U004 OBJ (10,051 bytes, SHA-256 `7fd7972dc8ab587f3d34de9e0ef08b763d207245b8f237223b235cf61c84670f`). The candidate OBJ is 10,059 bytes. OMF segment extents/definitions, groups, public/local-publics, externals/scopes, communals, and every pre-existing ordered fixup match; the only differing segment bytes are the two displacement bytes at offsets 05A8–05A9.

## SS entry evidence

The accepted `driver-ss-frame-contract-v1` is root-reviewed and checks all 128 external SS OFFSET16 sites. Its startup receipt pins the accepted `dos\crt0.asm` member: CRT selects DGROUP into SS before the far call to `main`, then initializes DS from SS. S00/S01/S02/S03 contain no `MOV SS`, `POP SS`, or `LSS`; ordinary far and same-TU paths preserve inherited SS.

The contract also traces the asynchronous display routes in `src/root/m1B73.asm`: mouse, timer, and keyboard paths save interrupted SS:SP, load DGROUP into SS, switch to DGROUP-owned stack storage, and dominate their display dispatches with that state before restoring SS:SP. This covers both normal S01 entry and the display callbacks; there is no path in the selected S01 TU that changes SS. The fresh fixture independently observes DS=SS=DGROUP under both linkers, with the DATA frame shifted by 98 bytes.

## Existing owner, writer, and bounds

The accepted root:1B4E provider rebuilds to the active object (2,224 bytes, SHA-256 `afaf236194c2951920ecf9cf9915e8c174c6cf75a56a324d0fe4f7dc457b52b9`). It owns `_g_41D0` in `_DATA` at offset 04B0h, length 100h; `_g_4220` is an existing 10h-byte all-zero interior row at +50h (offset 0500h), with no allocation added by the candidate.

The probe pins all 154 current translation-unit canonical/generated source inputs before scanning direct `_g_3DE4` / `_g_3DE5` and numeric `3DE4h` / `3DE5h` aliases. It classified 42 direct occurrences across 12 files: 14 declarations, 4 word reads, 2 word writes, 4 high-byte reads, 14 C value reads, and 4 zero initializers. There are no direct numeric memory operands and no direct byte writes to `_g_3DE5`. The only direct writer in the source set is the S01 word view at line 323, reproduced in canonical and generated text. It masks AX with `70F0h` before storing the word at `_g_3DE4`, so the overlapping high byte `_g_3DE5` is constrained to 00h,10h,...,70h.

In the selected read, `bx` is first reduced to 0..3 and doubled, then `_g_3DE5` is added to BL. The loop adds 2 and clears bit 3 with `AND 00F7h`, returning the phase to 0,2,4,6 while preserving the 16-byte style band. Thus the maximum displacement from `_g_4220` is 76h; maximum offset in the existing bank is 50h+76h=C6h, strictly below the 100h bank end. The fixture checks every distinct reachable offset (32 style/phase combinations), the 16-byte view, and the real next-row byte 44h.

Under both RTLink 4.00 and 6.10, group-frame controls pass with DS/SS=DGROUP; the `_DATA`-frame negative and +1-base negative fail as expected. Each map proves a +98h DGROUP data offset. Direct-reference closure is established; the proof deliberately does not assert that every arbitrary pointer in the entire game is incapable of aliasing this area.

## Production hook proposal

See `build/workers/dos_s01_4220_integration_review/proposed-hook-diff.txt`. The minimal safe integration is a new closed S01-only operand class and separately pinned runtime contract. Keep the existing S00 `_g_41D0` three-site contract unchanged. Keep `remaining-assembly-address-audit` unresolved, since other families (including 8ED8h and `_g_5A9C`) remain outside this site.

The proposal leaves the existing `--out` interface intact: new candidate-generated source/object data must continue flowing through the `out` argument, while the root-reviewed packet and immutable runtime contract are read as pinned project inputs. `python tools/source_only_dos.py --help` still exposes `--out`; the code resolves the selected output under `build/` and passes it to `prepare`/compile/link stages. Add a narrow regression using a fresh alternate `--out` directory once the production hook exists.

## Artifacts

- Fresh receipt: `build/workers/dos_s01_4220_integration_review/package/s01-pattern-4220-proof-candidate-v18.json`
- Fresh candidate packet: `build/workers/dos_s01_4220_integration_review/package/s01-pattern-4220-bindings-candidate-v18.json` (unadmitted)
- Fresh whole-module and RTLink/DOSBox outputs: `build/workers/dos_s01_4220_integration_review/durable-v18/`
- Isolated rerun script: `build/workers/dos_s01_4220_integration_review/independent_probe_v18.py`
