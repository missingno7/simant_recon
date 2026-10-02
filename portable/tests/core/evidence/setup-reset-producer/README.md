# RandYard setup-reset startup receipt producer

This folder preserves the exact build-only runner used for
`randyard-session-startup-setup-reset-20261002.json`. The old next2 report and artifacts remain untouched.

The run compared 146 source ranges against a resource-backed native SimSession using the
next2 generated profile; it reported zero mismatches. The receipt pins all source inputs and records the setup.c/session.c hashes. See pins.json for the report and producer hashes.

Reproduction: copy `session_startup_diff_setup_reset.py` byte-for-byte to `build/workers/session_startup_diff_setup_reset.py` (the producer computes its root from that worker path), then run `python build/workers/session_startup_diff_setup_reset.py --profile next2`. It writes only under the new `build/workers/session_startup_diff/setup-reset-next2/` directory. The ignored generated profile and local compiler/toolchain must match the hashes in the receipt; do not substitute the previous next2 evidence.

This directory contains no executable, source oracle, asset payload, or generated profile.
