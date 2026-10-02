# Mouse hotbox scanner differential

Run from the repository root with a native C compiler and the pinned behavior
VM dependency available:

```powershell
python portable/tests/windows/mouse_hotbox/test_mouse_hotbox.py `
  --report portable/tests/windows/mouse_hotbox/evidence/mouse-hotbox-differential-v5.json
```

The runner refuses to overwrite an existing report. It compiles the portable
scanner caller against `window.c`, executes the original near scanner
`root:1B73:0CEF` from the hash-locked DOS image with a real near-return frame,
and compares normalized object indices. Cases use the source 18-byte record
layout, registration mask word `1`, the left-press source mask `AX=0x0201`,
overlapping records, frame index 0, selectable filtering, rectangle edges,
misses, and deterministic signed coordinates. The source path is
`f_2505_0831` → `f_1FD2_03EB` → prepending `f_1B73_0B00` → scanner
`f_1B73_0CEF`.

The native helper models object hotboxes after source event-mask routing. The
scanner-only disjoint-mask case confirms that `AX=0x0400` misses a registered
mask-1 record; it is not compared to the maskless native helper. Callback
dispatch/Event construction, decoration precedence, dynamic re-registration,
and the physical INT 33h producer are outside this proof.
