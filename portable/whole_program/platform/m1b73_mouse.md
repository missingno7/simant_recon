# Native m1B73 mouse boundary

This provider is a source-derived native adapter for selected public m1B73
entrypoints. It does not install DOS vectors or emulate the DOS interrupt
stacks. `PortableM1B73MouseAsmState` is a pointer view over single native
owners; the cursor image/mask are borrowed pointers held only while their
database/session resource owner remains alive.

| Entry | Source behavior retained | Native boundary |
|---|---|---|
| `f_1B73_0025` | Clears the INT 33h vector only if it still points at this module's one-byte IRET stub. | SDL never installs an IVT stub, so the native fallback-stub state remains false. |
| `f_1B73_0046` | Checks mouse availability, sets screen limits, initializes the coordinate pair from the source's exact `g_3DB4/2` then `g_3DB2/2` assignments, and marks cursor support initialized. | Requires the current Host pointer query, a profile-supplied source/host coordinate map, and a successful Host warp. The source's argument order is intentionally preserved. |
| `f_1B73_0218` | Forwards its two words to INT 33h function 0Fh. | Retains both ratio words; event mapping belongs to the active presentation profile. |
| `f_1B73_0235` / `f_1B73_02A9` | Saves/restores the BIOS NumLock bit and increments/decrements the source hook nesting byte. | Activates/deactivates the ordered SDL mouse-event consumer. INT 33h callback and INT 08h/09h/15h vector installation/restoration are retired explicitly. |
| `f_1B73_01E1` | Stores image/mask pointers and reads the image width/height words. | A session resource validator must approve the borrowed spans and return the source header dimensions; no guessed bounds or copied image bytes. |
| `f_1B73_00D9` | Increments the 32-bit callback count, clears the pending byte, refreshes hot-box selection with query `FFFFh`, and shows the cursor only when the show-level byte is zero. | Requires both a real hot-box hit-test and cursor renderer callback. Missing callbacks return a provider error through the native API; the source void alias fails hard. |

`portable_m1b73_mouse_consume_event` receives events only after the shared Host
queue has retained/popped each SDL event once. It maps Host logical coordinates
through the configured profile, records source button state and INT 33h event
mask bits (move, then press/release pairs for left, right, middle), and follows
the source visible-cursor sequence: hide, hit-test with the updated mouse-status
word, show. A hidden cursor updates the source coordinates and drawn flag
without rendering. The source mapping and renderer are required dependencies,
not successful stubs.

The scalar initializers lifted in `m1b73_mouse_state.c` come directly from the
readable `_DATA` declarations: zero-initialized button/cursor/callback/hook
fields, and the cursor's initial 22-by-22 dimensions. `g_9120/22/24` are the
source-shared zero-initialized status/coordinate words; `g_3DB2/4` remain
borrowed from the existing graphics source owner.

The focused native test exercises source entrypoints and ordered callback
arguments with controlled providers. It is not a DOS differential or proof of
physical cursor raster equivalence. The full hot-box table and rendering
callback implementations remain outside this provider until their source
owners are bound by the whole-program integration.
