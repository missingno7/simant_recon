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

## Caller-frame repair

`python evidence/canonical/event-omitted-word/caller_frames.py` recompiles four
whole canonical modules using each manifest profile and flags, rechecks their
strict claims, and emits `caller-frames.json`. All four modules are exact; the
fresh object hashes equal the manifest object hashes. Instruction offsets in
the receipt are canonical frame offsets; `object_offset` records the actual
OMF public offset (main has a four-byte frame delta). Original bytes are never
used as native runtime data.

There are **three**, not four, direct four-word sites:

| Site | Canonical call | Wrapper BP+0Eh | Source value |
| --- | --- | --- | --- |
| S10 selected item | 35F5:09C0 | popup BP-74h, saved incoming SI | bar-selection `m * 4` |
| S10 empty menu | 35F5:0A4B | popup BP-74h, saved incoming SI | bar-selection `m * 4` |
| S19 key command | 384C:02F2 | key-dispatch BP-8, saved incoming SI | `DoEvent`'s current SI |

The pre-argument SP points at the saved SI word. Four argument pushes, a far
call and the wrapper's saved BP put its BP fourteen bytes below that SP, so its
BP+0Eh is exactly that word. Popup reserves 70h bytes then saves DI and SI;
key dispatch reserves four bytes through `__aFchkstk`, then saves DI and SI.
The receipt also checks the original runtime helper: on success it subtracts
AX from SP without touching SI; the failure path transfers to error handling.
Neither word is an uninitialised local. Later assignments to the callee's own
SI register variable do not change its saved incoming value.

At bar-selection 0272..0276, `m` is copied to AX and SI is shifted twice.
The title draw preserves SI; at 02B8 the popup receives that `4*m`. It must be
captured before entry, rather than reread from a mutable global or confused
with popup `i`. The conversion adds a private argument to the popup and uses
it explicitly at both sites. For menu 5 this is 20, explaining the reported
FD12 Event.v value without special-casing that event or scenario.

For the S19 path, main keeps `register unsigned frames` in SI (0192/01B0),
then calls the edge-scroll event pump at 02E7/02FD. The pump calls `DoEvent` at
01F2 before its own `dy` assignment at 01F9. `DoEvent` likewise preserves its
incoming SI until its Ctrl-scroll loop; that loop's SI is `dy` (0194..0214).
Key dispatch at 0237 therefore receives main `frames` when the loop did not
run, or the last loop iteration's `dy`. The conversion transports this context
as explicit private parameters and records the last `dy` before the loop exit
test. It does not reconstruct game logic or depend on native register allocation.

The typed frontend applies the two forwarding-owner adaptations, after the
existing startup/scalar passes, and includes `event_caller_frames` in the
per-TU receipt. The enqueue owners are adapted earlier by the existing build
hook. Source hashes, exact object hashes, instruction/fixup records and a pinned
evidence digest bind every site. Five-word calls retain all their original words.

### Remaining explicit context limit

`ui_pump_events_periodically` also calls the edge-scroll pump at 00F8:01B0.
It has no reference in the current canonical source inventory (including
symbolic assembly and aliases). Its instructions do not assign SI before the
call. If entered from an external caller, its incoming SI is that caller's
register context, not a value recoverable from this function's locals. No proof
establishes it as uninitialised or zero. That unbound entry still passes an
explicit zero normalization; the S19 receipt and platform exception remain open
for that context. This is not a claim that all theoretical callers are covered.

The live regression and disabled control are recorded under
`build/workers/event-v/`. No claim is made about the reported logo-click hang.
