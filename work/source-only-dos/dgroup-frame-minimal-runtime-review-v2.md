# Minimal `g_5A9C` SEG-frame runtime contract

**Disposition: controlled source-only runtime evidence for parent review; no admission.** This isolates the `SEG` relocation used by `root:1B73` and does not establish screen-Rect ownership or field initializers. The 113 data-debt bytes remain explicit.

The whole-module source comparison in [the map/OMF review](dgroup-rect-frame-review-v1.md) identifies the original site as `src/root/m1B73.asm`, `MOUSE_TEXT:0133`: a 2-byte `base16` fixup to external `_g_5A9C`, framed by segment `_DATA`, with encoded addend `0000`. The neighboring `MOUSE_TEXT:0139` offset fixup remains external `_g_5A9C`, framed by `DGROUP`, addend `0000`.

The minimal harness compiles two assembly helpers with the same instructions, C objects, startup libraries, and linker inputs. Their sole source-expression difference is `mov dx,DGROUP` versus `mov dx,seg _g_5A9C`. OMF confirms that the old helper fixup at `CHECK_TEXT:001A` has the same target, frame, width, location, and addend as the whole-root site. The reviewed helper changes that fixup to a zero-addend `DGROUP` group frame. The target OFFSET fixup at `CHECK_TEXT:0013` is unchanged, and helper segment bytes, lengths, definitions, and groups are equal across the two objects.

The helper checks DS and SS against DGROUP, stores the selected segment word and the `OFFSET DGROUP:_g_5A9C` word in typed `g_5AAC`, then compares those words against DGROUP and the expected offset before any far dereference. On the deliberately old-framed helper, it reports `FAIL`; on the reviewed helper, it reports `PASS`.

Both runtime cases completed under each linker, with no timeout, linked EXE/map, `STATUS.LOG=EXECUTED`, emulator exit 0, and six-byte `RUN.LOG`:

| Linker | Reviewed DGROUP helper | Original `_DATA` SEG control |
|---|---|---|
| RTLink 4.00 | `PASS` | `FAIL` |
| RTLink 6.10 | `PASS` | `FAIL` |

Both maps place DGROUP at `0092:0000`, `_DATA` 66 bytes into the group, and `_g_5A9C` at `DGROUP:0042`. Thus the original SEG fixup resolves the `_DATA` paragraph while its adjacent offset remains DGROUP-relative; the checked segment word differs from DGROUP in the shifted-group fixture. The negative test only reads the stored words and does not follow the wrong far address.

The full run receipt, including per-linker case outputs, map/log/EXE hashes, the exact root/helper OMF fixups, pinned build inputs, and the no-original-EXE-input guard, is [dgroup-frame-minimal-runtime-v2.json](../../build/workers/dos_clip_data_ownership/dgroup-frame-minimal-runtime-v5/dgroup-frame-minimal-runtime-v2.json). The reproducible probe is [dgroup-frame-minimal-runtime-probe.py](dgroup-frame-minimal-runtime-probe.py); use a fresh `--out` path under `build/` because it refuses to overwrite prior runs.

The earlier whole-module runtime harness still has its separate bounded timeout receipts in [the map/OMF review](dgroup-rect-frame-review-v1.md); those timeouts remain unresolved. This minimal fixture isolates the ABI behavior and does not explain those hangs. No canonical source, production tool, inventory, promotion packet, or debt count was changed. The symbolic source correction remains unadmitted pending parent review.
