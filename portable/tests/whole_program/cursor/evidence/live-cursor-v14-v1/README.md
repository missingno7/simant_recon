# Live cursor diagnostic, v14 replay

This packet records the source cursor at the replay’s actual pointer position. It includes the exact full-game input script, GDB commands and logs, plus the indexed frame snapshots, saved-under buffers, and small GDB-captured callback payload spans needed to audit the stages. It contains no copies of original asset files.

The recorded cursor was at `(288, 234)` with a 24×16 save-under region. Across three capture/show stages, each decoded save-under buffer equals the indexed framebuffer crop at capture time. The one-plane kind-7 mask applies the observed AND operation; the four-plane kind-8 image applies XOR. Two restore stages write the saved-under region back exactly. All recorded pixel comparisons have zero mismatches. The detailed machine-readable counts, run identities, asset hashes and source hashes are in `report.json`; `capture.gdb` reproduces the stage dumps using the pinned executable and replay input.

The run does not redraw the scene beneath a stationary cursor. Therefore it does not determine whether another code path fails to invalidate or refresh the save-under buffer after scene changes. The next discriminating test is to leave the pointer still while the underlying map/window redraws, then compare the screen before redraw, after redraw, on the next cursor capture, and after one pointer move/restore.

## Reproduction

From the repository root, use the recorded v14 executable and `input-script.txt` with `capture.gdb`. The GDB file writes its outputs into the corresponding `build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/` scratch directory. Run `python portable/tests/whole_program/cursor/evidence/live-cursor-v14-v1/verify_stages.py portable/tests/whole_program/cursor/evidence/live-cursor-v14-v1/captures` to reproduce the pixel counts directly from this packet. The included callback payload spans were captured at runtime by GDB; raw asset files are referenced only by identity/hash and are not copied here.

The `.bin` files in `captures/` are raw 640×480, 8-bit indexed framebuffers except the three 196-byte planar save-under buffers.
