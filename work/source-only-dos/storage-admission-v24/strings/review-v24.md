# Read-only root review support for the remaining string pointers

This support packet independently reopens the final v23 candidate with SHA-256 `94736cc423e620781304d910f70f576b1f84e0b4508b4632a28b6e51b3926cb9`. The candidate remains root-unreviewed and unadmitted. It proposes module `source-owned:remaining-preparestrings-string-pointers` with basename `STRREST`; its actual saved storage control was `LANGPTR.C`, and no historical COMDEF-producing TU or placement identity is claimed.

Run `python build/workers/dos_string_root_support_v24/verify-string-root-support-v24.py` to recheck the saved evidence. The verifier writes JSON to stdout only. [root-review-facts-v24.json](root-review-facts-v24.json) is the captured output; [verify-string-root-support-v24.py](verify-string-root-support-v24.py) is the repeatable verifier.

## Reopened source and runtime evidence

The verifier rehashed all 156 selected effective source paths (127 canonical modules plus 29 behavior-source corrections), all 30 strict source-selection receipts, and all 77 archived compiler/linker/runtime input files: 63 MSC 6.00AX inputs, four RTLink 4.00 inputs, seven RTLink 6.10 inputs, and three startup/runtime inputs. All match the v23 packet. It also rehashed all 252 per-case artifacts.

The 18 saved cases contain 18 exact CRLF `RUN.LOG` markers, 18 clean `LINK.LOG` files, and 18 maps with both the Name and Value sections present, for 36 checked map sections. All thirteen candidate publics are present once in each section. The shifted-alias control has 52 measured relations across the two linkers: thirteen independent backing objects × two map sections × two linkers, each public alias at backing offset +2. No allocation-order or adjacency claim follows from these test-owned layouts.

## Source type and lifecycle anchors

`src/root/m075B.c` defines `StrList` as `char far * far *` and declares each candidate as `StrList far`. `initStuff` calls `PrepareStrings` before its first resource load; `PrepareStrings` assigns the thirteen candidates from resource IDs 1000, 1010, 1100–1103, 1200, 1210, and 1220–1260. The other five assignments in that function belong to previously owned pointers and remain excluded here.

`LoadStringAnt` requests resource kind 4, skips a one-byte header, reads a byte count, allocates `(count + 1) << 2` bytes for far row pointers, points rows into the loaded payload, and writes a null sentinel. It has no direct free/unlock call. Resource counts, consumer index bounds, and database/cache lifetime remain unresolved; the pointer-object evidence does not establish loaded payload capacity.

The saved compiler type contrasts cover the far pointer-to-far-row-pointer form, an independent four-byte BYTE view, near outer pointer, near row pointer, wrong pointer depth, and an eight-byte two-entry array. The proposed `STRREST.c` contains only thirteen bare natural-C object definitions: no include, initializer, function, payload, or guessed import.

## Actual saved OMF shapes

The nine decoded control objects are saved in the JSON with raw object pins, segment lengths, external names, and public names as strings. The actual `LANGPTR.C` object has thirteen far COMDEF rows, each count 4 × element size 1, length 4; it has no public code, initialized segments, or fixups. The eight-byte contrast uses thirteen far commons of count 2 × element size 4, length 8. The shifted control has thirteen separate eight-byte backing commons.

The initialized negative is a test fixture, not a production initializer. `LANGINIT5_DATA` is a 104-byte `FAR_DATA` segment. Its raw OMF bytes are 104 zero addends (SHA-256 `39f37f8d1931b3bdf767e7510dd69509fbf23af1f7654933d0a4d291cbdd4418`), with thirteen four-byte `pointer32` relocations at offsets 52, 56, …, 100. Each targets `LANGINIT5_DATA` with displacement 0 and encoded addend `00000000`; thirteen publics occupy the corresponding offsets. The linked values depend on relocation. The control source explicitly initializes each candidate to `&test_rows[0]`; the verifier does not infer that initializer for the production globals.

Consumer OMF external names are limited to the thirteen storage names and MSC startup/CRT names `__aFchkstk`, `__acrtused`, `_main`, and `_puts`. The preserved linker scripts name the test `CRT` object, test `OWNER` section, and standard `LLIBCR`/`LIBH` libraries; they contain no original game/resource imports. No original game object, executable, or resource payload is an input to this proof.

## Mutable tool pins and current production context

Two v22 helper-source pins changed after the saved runtime run. Their original v22 hashes, v23-normalization hashes, and current v24 hashes are all recorded in the JSON. At this review, the v23 and v24 hashes still match: `tools/dos_source_bindings.py` is `2c5cdee627aeca70c737fdc7faf4f31868f25c2e05e0eae8868905ea7ac82a72` (145776 bytes), and `tools/source_only_dos.py` is `533dd2dd627836023a69fcd877f5efd382562ae74ee37fe98e7dbd6333ec363c` (69104 bytes). These mutable helpers are not archived compiler, linker, or runtime inputs; their historical digests remain preserved.

The current build-report snapshot is context only: it reports 166 translation units and 228 unresolved symbols, and contains the previously admitted five-member `source-owned:language-string-list-pointers` module. It does not contain the remaining-pointer candidate module. This verifier did not build or change that report.
