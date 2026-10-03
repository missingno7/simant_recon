# m1FD2 source queue-view adapter

`conversions/m1b73_queue_source.py` is applied after the existing Timer type
lift and before `whole_program.convert_words`. It removes only the source
`fd_5071_*` extern declarations and queue-operation prototypes, redirects each
queue argument to `portable_m1b73_queue_slot(1..3)`, and replaces
`StillDown`'s one low-byte `g_9120` read with
`portable_m1b73_g9120_low_byte()`. `g_9122/24` declarations are removed in
favor of the typed `int16_t` declarations; source reads remain unchanged.

The queue selector returns borrowed members of the one
`portable_m1b73_queue_set` owner. Slot indexes are 0 Queue0, 1
`fd_5071_0060`, 2 `fd_5071_03C4`, and 3 `fd_5071_0728`. Their row arrays are
exactly 5, 48, 48, and 10 records of 18 bytes. Invalid selectors return null.
The m1FD2 C TU uses slots 1, 2, and 3 only.

The source ASM stack interfaces audited for m1FD2 are:

| Entry | Original stack arguments after far return address | Native C view |
|---|---|---|
| `f_1B73_0B5B` | signed word ticks, far queue pointer | `int16_t`, borrowed `PortableM1B73Queue *` |
| `f_1B73_0B00` | far `Timer *`, far queue pointer | canonical native `struct Timer *`, borrowed queue view |
| `f_1B73_0AC3` | far `Timer *`, far queue pointer | same native view as `0B00` |
| `f_1B73_0BC5` | signed word ID/ticks, far queue pointer | `int16_t`, borrowed queue view; source C declares void and ignores ASM AX |
| `f_1B73_0C42` | signed word ID, far queue pointer, output far pointer as offset then segment words | `int16_t`, borrowed queue view, typed `PortableM1B73Rect *` after source-wrapper normalization |
| `f_1B73_09E9` | signed x word, signed y word | two `int16_t` values |
| `f_1B73_030F` | ASM reads five words at BP+6 through BP+0E in BX, ES, AX, CX, DX order | five explicit `int16_t` values; four-word commands use a separately named helper with scoped `DX=0` normalization |

The source ordering control checks every one of the 33 m1FD2 function names
before and after the transformations. The full translated TU passes GCC syntax
checking with incompatible pointer types and implicit function declarations
treated as errors. A separate native control checks each slot resolves to the
matching canonical queue descriptor and exact row array, rejects slot 255,
and verifies the low-byte accessor against the low byte of a status-word
sentinel.

This is source-view and compile evidence only. It does not implement the other
queue-operation exports listed above or the source far-pointer call mechanics.
The adapter does not mention `g_4366`; the existing signed-byte source view
remains untouched.

## Typed operation closure

The current native provider implements `f_1B73_0C42(id, queue, Rect*)` over the
canonical queue owner. It scans `count` 18-byte rows in source order, compares
the signed ID word at record offset `+12`, and on the first match copies the
four signed words at `+0,+2,+4,+6`. A miss returns zero without changing the
output. `f_1FD2_04B3` is normalized at the m1FD2 source adapter boundary from
the old `id, pointer-offset, pointer-segment` C split into one native Rect
pointer; it returns the ASM lookup result consumed by the S26 caller. The
native record/output checks are covered by
`portable/tests/whole_program/evidence/m1b73-queue-operations-v3.json`; this is
not a DOS segmented-pointer differential.

The typed `f_1B73_030F` signature explicitly names all five words the genuine
ASM body reads: `(BX, ES, AX, CX, DX)`. A separate source conversion covers the
actual S19/S10 callsites: the three four-word command calls route to
`portable_m1b73_event_enqueue_four_word_command`; the two five-word calls keep
the fully explicit entry. The four-word helper supplies `DX=0` solely for the
resulting `Event.v` value. Source inspection shows the corresponding command
paths dispatch/read `Event.code` (and where applicable `Event.message`) and do
not read `Event.v` in S19/S10. This is a scoped native normalization, not a
claim that the missing DOS caller stack word was zero or that all game
consumers ignore it. The immutable controls pin the concrete callsites and
exercise the field map; no DOS execution is included.

`m1b73_queue_source.py` identifier substitutions now scan C tokens, leaving
comments and string/character literals untouched. The lexical control is part
of the v3 operation receipt. Earlier queue-view and event receipts remain
unchanged as historical evidence.
