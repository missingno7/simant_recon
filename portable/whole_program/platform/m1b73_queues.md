# Native m1B73 queue initializer

`m1B73.asm` defines the four queue extents as 5, 48, 48, and 10 rows of 18
bytes. The words immediately before the four count words give capacities
4, 47, 47, and 9. `g_5484` dispatches the first three queues with event masks
`FFh`, `FFh`, and `1Eh`; the separate `g_549A` descriptor addresses the fourth
queue for cursor hit-box refresh.

`f_1B73_0AA3` matches its writes: it clears only Queue0 and
`fd_5071_0060` counts, sets the canonical `g_5FF2.r.bottom` view (source bytes
`g_5FF8/g_5FF9`) to `1F00h`, and sets the same canonical Timer's `fn` member to
`f_1B73_0CB3`. It does not initialize the other queue counts. `o17_384C_0000`
is exercised from its original C body in the focused test; the other startup
services are observed controlled providers.

The dispatcher retains the original descriptor-mask order, signed inclusive
rectangle test, record condition-word test, and source-order callback scan. A
zero callback result ends the current record scan, after which `0CB3` advances
to the next descriptor. Bytes +8..+11 remain an opaque DOS far callback
pointer; native code never casts them. A matching row requires an explicitly
bound record resolver. The public void callback fails hard if a matching
record is present without that resolver; an empty or nonmatching queue succeeds
without inventing a callback. The resolver is also responsible for any
application-specific mutation made by the old DOS far callback. This is a
logical queue/callback boundary, not DOS interrupt, far-pointer, or mouse
hardware emulation.
