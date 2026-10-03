# Native heap guard diagnostic archive

This directory preserves readable inputs and transcripts for the bounded v12 first-write diagnosis and the v13 guarded replay. It is diagnostic evidence only; it does not change or promote production source.

`archive-manifest.json` lists byte sizes and SHA-256 hashes for every archived file and explicitly records unrecovered execution inputs. The v12 first-write transcript is `v12/first-write-gdb-transcript.txt`; the later guarded-v13 no-hit transcript is `v13/no-hit-gdb-transcript.txt`. Both scratch guard allocator revisions are preserved as `handles_guard.c` files. The shared replay script is `quick-game-vga-v1.txt`.

The scratch guard runs replaced the native handle allocator object with a VirtualAlloc-backed diagnostic shim. The v12 trace shows the `subinclude` handle's 2048-byte payload filled by 256 Rects, followed by a sentinel write one Rect past the allocation in `f_1D8E_003F`; the check in `clip_SubInclude` occurred after the loop. The captured `g_5AAC` pointer was in executable constants, evidence of an invalid or unterminated clip list, but not proof of its assignment path. With the v13 source fixes, the same bounded replay exited at the 30-second smoke deadline with 110 outer-loop iterations and no guard hit.

Exact GDB command scripts for the v12 first-write and v13 no-hit transcripts were not retained. Link command logs are empty. The exact transcripts, readable guard sources, migration/application reports, and replay input are retained, but this archive does not promise a byte-for-byte rebuild of either diagnostic executable. Original binaries/assets are not duplicated here; their pins and prerequisites are recorded in `diagnostic-report.json` and the retained migration reports.
