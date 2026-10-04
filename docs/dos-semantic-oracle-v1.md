# Historical semantic checkpoint

`dos-semantic-oracle-v1` remains immutable at
`66e85041ee54f59774ae0fd5a08b37ffbcf77172`. Its original source, workflows and
freeze report are available from that Git tag. The tag contains no original game
or compiler binaries; the hash-locked local prerequisites are still required.

This was a semantic checkpoint, not a complete standalone DOS reconstruction.
Later strict review and source-ownership work corrected the active source.
The current [canonical architecture](canonical-source.md) consumes those
corrections directly. Old published mistakes and internal tooling are preserved
by Git, rather than by runtime compatibility layers.

An independent source-built DOS executable, zero unresolved imports/layout
dependencies, DOSBox-X comparison and human acceptance are still required before
claiming `functional-source-oracle-v1`.
