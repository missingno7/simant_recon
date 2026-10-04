# DOS control-flag storage binding proposal (v19)

This is an unreviewed source-binding proposal for the three registered two-byte
words `fd_50F6_0468`, `fd_50F6_0370` and `fd_50F6_024E`. It does not claim storage
ownership, historical object ownership, flag meaning, lifecycle, or domain behavior.
`root_reviewed` and `admitted` remain false.

`source-review-v19.json` flattens and rechecks the 156 source hashes and 29 strict
receipts from the unadmitted V18 review, pins the existing provider and compiler,
header and runtime inputs, and records the scalar OMF short, long and initialized
controls unchanged. It audits each complete linker log, map, executable and runtime
log directly under `build/workers/dos_control_flag_words` for both linker profiles
and all four cases. Runtime expected and actual strings retain `PROGRAM_NONZERO`.

The executable pins contain only original build paths, SHA-256 and size. No binary
payload is copied into this proposal. `dos_source_bindings_v19.proposal.py.txt` is a
ready insertion proposal for the generic V18 contract helpers; it has not been
applied to `tools/dos_source_bindings.py`.

Run `python build/workers/dos_v19_flag_packet/normalize_v19.py` to regenerate the
review after the pinned evidence has been checked. It does not compile, link, execute,
or modify existing packets.
