# NEXT8 event-width diagnostic packet

This packet preserves the bounded evidence for the S24 `ProcHistoryEvent`
host-width correction. It is diagnostic input for the portable source profile,
not a behavior-exact registration or a historical-source claim.

`evidence.json` records the NEXT7 parent identity, source and original-instruction
anchor, generated module and state hashes, compiler identity, harness pins, all
64 directed DOS/native callback traces, and the old-width negative control.
`SHA256SUMS.json` hashes every retained packet file except itself. The source,
generated TU, exact wrapper and harness snapshots, and positive/negative probe
sources are preserved. Compiled executables, oracle assets, and object files are
excluded.

The original DOS instruction reads a 16-bit word at `Event + 0x0c`; the next word
at `+0x0e` is independent. With a host `unsigned` member, GCC reads both words
when evaluating `code`. The fixed `uint16_t` view preserves the event contract.
The prior-width probe coincides for `xE=0` and diverges for nonzero `xE`; its
case-by-case output is retained in `evidence.json`.

Run the focused checks from the repository root:

```powershell
python -m unittest portable.tests.recovered.test_next8_event_width
python -m unittest portable.tests.recovered.test_next8_build_controls
```

These checks rebuild the diagnostic profile and reject four malformed profile
records before compilation. Replaying the DOS cases requires the local original
oracle/tool assets referenced by the harness; those files are not copied into
this packet.
