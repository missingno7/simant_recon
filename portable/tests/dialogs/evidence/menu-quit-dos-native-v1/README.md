# MenuQuit DOS/native differential packet

This packet compares the frozen S15 `MenuQuit` and `o15_384C_0239` bodies with the source-derived portable C model. It covers all keyboard and window-event choices, unknown input followed by a recognized choice, dirty and clean state, resource/font/frame setup, cleanup ordering, and SaveGame failure followed by retry success. All 18 executed oracle/native cases matched; complete ordered observations are in `run/cases.jsonl.gz`.

The kind-10 prompt comes from actual local repository assets `assets/SHARED` record `(128, 10)`. Those original database files remain local inputs and are not copied into this packet. Their original hashes and the selected record's exact 165-byte payload hash remain pinned here. The payload contains embedded control and NUL bytes; the harness preserves the complete record length and compares the exact payload passed to the print boundary. The model does not interpret or replace those bytes.

SaveGame disk I/O is a controlled host boundary with scripted success/failure. A successful save clears the source dirty word, as the original SaveGame body does; this packet proves MenuQuit retry and exit flow, not filesystem serialization. Prompt resource/window/font/input operations are also explicit deterministic host boundaries. Process termination is represented by a terminal exit-notice boundary carrying the exact source-authored message. A cancellation returns zero and preserves the dirty word.

## Reproduction

From the repository root, run `python portable/tests/dialogs/run_menu_quit_differential.py`. `inputs/` contains exact source and harness copies; `run/report.json` records the locked original executable and source pins. The required pinned Unicorn VM environment is the repository's `build/behavior/deps` installation. The original `assets/SHARED.DAT` and `assets/SHARED.NDX` must be present locally; `.gitignore` prevents accidental packet copies. `pins.json` gives SHA-256 and byte length for committed artifacts, the local DLL, and local-only asset inputs.

The native DLL in `run/native.dll` is an ignored local build product (`portable/.gitignore` excludes `*.dll`). It is retained in the local evidence packet, its identity is pinned here, and it is not part of the committed packet. Rebuild it from the pinned C inputs with the runner's compiler command.

This is bounded differential evidence, not a BEHAVIOR_EXACT registration or a claim about the unmodeled host I/O implementations.
