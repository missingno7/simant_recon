# The unprovided fifth event word

`python evidence/canonical/event-omitted-word/probe.py` executes the original
`f_1B73_030F` and enqueue instructions with contrasting caller frames. Both
four-word calls supply identical arguments. Changing only the next caller-stack
word from 1212h to ABCDh changes queued `Event.v` from 1212h to ABCDh. Two
five-word controls supply zero explicitly; changing the following ambient word
leaves their complete event records equal. The queue accepts exactly one entry.

The canonical ASM wrapper reads code at BP+6, the event segment word at BP+8,
modifiers at BP+0Ah, h at BP+0Ch and v at BP+0Eh. The enqueue copies v into record
offset 0Ah and code into 0Ch. Direct S10 menu and S19 keyboard calls include
four-word frames. Other direct forwarding calls supply five words. The callback
dispatcher at `f_1B73_0CEF` also pushes five words; it is a separate ABI path.

Source contains coordinate observers in S04, S05, S13, S22, S26 and root:23E6.
In particular, S04's modal map loop reads `ev.v` after `win_GetEvent` without a
local event-code test. The root:218D dispatcher permits high-bit FD/FE commands
through its general path and `win_GetEvent` copies the accepted event. These
facts prevent a global dead-field argument. They are not a replay of a specific
interactive interleaving: ordering, modal entry and each observer's input domain
still require proof.

The native zero substitution remains an explicit unresolved exception. No
canonical argument is invented, no native symptom is patched, and this receipt
does not attribute the reported logo-click hang to this field.
