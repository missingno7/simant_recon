# S00 source-aperture capture v9 archive

This write-once bundle preserves the exact input closure recorded by `s00-source-aperture-capture-v9.json`, plus the executed native binary and receipt. Each archived input SHA-256 was checked against both receipt input maps. The two source-clip owner files had drifted in the checkout and were restored read-only from Git commit `791aada`; all other inputs were copied from the working tree after hash verification.

The original DOS/native comparison is the four FNV-1a capture values in the preserved JSON receipt; raw DOS capture bytes were not saved by the v9 run and are not claimed to be archived.

Scope and limitation are unchanged from v9: visible capture rows come from the single indexed framebuffer, off-visible rows come from the same native planar backing after source page uploads, and generic checked capture remains display-bounded. The test does **not** establish that real BIOS mode-setting clears off-viewport planar aperture bytes or that historical uninitialized off-screen VRAM matches the native backing.
