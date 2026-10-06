# Shipped resource domains and functional storage footprints

The independent census covers all six oracle-locked DAT/NDX inputs, including
all compressed records: 840 records, 205 LZSS records, decoded corpus identity
`2cd5f2c76ee8a96e`. It reuses the already independently controlled database/LZSS
parser rather than adding another decoder. The tool produces metadata only,
never executable resource capsules or storage definitions.

```
python tools/resource_domains.py --out build/workers/resources/new-resource-run
python evidence/canonical/audio-track-owner/shipped_domain.py --out build/workers/resources/new-audio-run
python evidence/canonical/shipped-resource-domain/palette_probe.py --out build/workers/resources/new-palette-run
python -m unittest discover -s tests -p test_resource_domains.py -v
```

`facts.json` is the small durable conclusion and the reviewed source dependency
set. Generated full record details belong only in ignored build output. Source
dependency hashes and the complete symbolic consumer census require renewed
review if algorithms or consumers change. The production DOS storage gate
independently validates admitted provider shapes; the consumer census excludes
the data-only `src/state/` providers.

These conclusions concern successful loads of the immutable shipped corpus and
nominal source control flow. They make no theorem about arbitrary entry states,
corrupt/replacement resources, memory corruption, allocation failures that
continue, or computed aliases caused by unrelated out-of-domain accesses.

## Audio: complete supported footprint for two functional owners

The earlier audio parser exhaustively verifies 33 song metadata records pointing
to a closed set of 30 SMF streams. Their header and parsed chunk counts agree;
all tracks terminate. Counts range from 2 to 10. All 36 source song callsites
expand to present metadata IDs; its existing receipt records the four dynamic
ID expressions and their source invariants. The corpus-wide maximum includes
the called song 10001. This is substantially stronger than examining one song
or observing an arbitrary runtime sample.

The complete symbolic consumer set of `fd_50F6_4B30` and `fd_50F6_4B42` is
`root:284A`. The following inductive proof establishes the entire operational
footprint, independently of historical adjacency or guessed COMDEF capacities:

| Producer/consumer | Index or escaped view | Bound and lifetime |
| --- | --- | --- |
| `f_284A_0256` | Writes `time[i]` and `status[i]` | `g_7566` is the decoded SMF header count N; loop `0 <= i < N` initializes every live track slot. |
| `f_284A_02E4` | `g_756C=0`, `g_8E02=status`, `g_8DFE=g_8DD8` | N is at least 2; both base views designate live slot zero. |
| `f_284A_038F` | Reads/writes `time[g_756C]`; reads `time[best]`, `time[i]`, `status[best]`, `status[i]` | Current starts zero. Best starts zero, then is assigned only i from `1 <= i < N`. Assigning current=best preserves `0 <= current < N`. |
| `f_284A_038F` | `g_8E02=&status[best]` | This is the only other assignment to the private static status view. It is never incremented or exported. |
| `f_284A_05C5`, `f_284A_067F` | Reads/writes `*g_8E02` | The private view always designates status[current]. Data values can change track timing or event interpretation, but do not supply a new status-array index. |

`g_7566` has only its initial zero definition and the header assignment;
`g_756C` has only its initial definition, zero reset and best assignment. Their
symbolic consumer set is exactly `root:284A`. The track-offset view `g_8DFE`
is also private and points only into `g_8DD8[0..N-1]`; writing stream positions
through it does not write either count or the array views.

`g_756E` starts zero. `f_284A_0013` calls StopSong first. On successful load it
calls the genuine `f_29F0_001A` interrupt-disable helper, initializes every track,
resets current/pointers, then sets `g_756E=1`; the final helper reenables
interrupts. `f_284A_067F` returns before dereferencing either view unless the
state is 1. Both original ISR callsites in `root:28BC` enter this guarded
sequencer without parameters. They do not assign the count, current or views.
StopSong sets the state zero before freeing the song resource. Completion sets
the state 2. Thus startup, song changes and stop/completion preserve the view
lifetime; no array access needs uninitialized track slots. Legitimate CRT
startup-zero communals are compatible with, but not a substitute for, this
dominating per-song initialization.

The functional provider can therefore allocate **10 unsigned bytes** and
**10 signed DOS longs (40 bytes)** with static duration. These are supported
allocation choices, not original array capacities or original allocator-TU
discoveries. No initializer, padding, extra adjacency or source algorithm
change is required. The proposed whole data-only TU uses tentative public far
definitions, preserving the consumer extern views. Its MSC 6.00AX
`/AL /Os /Gs` control emitted exactly two far COMDEFs (count 10, element size
1/4), zero code, zero initialized bytes, no imports, no fixups and no live
segments. `dos.build.storage_snapshot` and `verify_storage` both passed.

The existing FARSEG-2 compiler experiments remain historically meaningful:
they show why bytes/fixup grouping cannot prove an original allocating TU or
capacity. They do not forbid a separately reviewed functional source owner.
The `/s9` detector overrun remains a separate historical-layout/unsupported
selector question; it is not silently covered by this track-domain proof.

## Menu: all sentinel writers use five slots

Every active resource in every shipped database was decoded. There is exactly
one kind-6 menu, SHARED `(0,6)`, with five titles and item counts 8/7/8/6/6.
Its outer table, all nested pointer tables and every NUL-terminated string tile
the 514-byte resource without gaps or overlaps. No pointer enters a table or
another string. The parser accepts valid synthetic 11- and 21-title menus;
five is an observed pinned-corpus domain, never a parser-imposed cap.

The only direct S17 loader calls are the S20 startup choices 1 then fallback 0.
The corpus contains no menu 1, so a successful shipped load uses menu 0. S17
fixes pointers, then both title-sentinel traversals in `f_1FD2_0663` visit exactly
indices 0..4. Their writes cannot intersect the historical render-delay/Handle
neighbors. The S17 control registration loop visits the same five pointers and
generates IDs `i-0x200`, whose low event bytes are 0..4.

For a valid incoming menu event, S10 current is -1 or 0..4. Only that valid m is
assigned to current; its title/position/width reads use this range. Its arrow
updates use predecessor wrapping and modulo the loaded count five. S17 reads
the same 0..4. The root title-state readers use `id>>4`; their only direct caller
is `f_1FD2_0059`, which itself has no direct source callsite. The raw-menu helper
`f_1FD2_07CB(menu)` also has no direct source callsite. Neither absence is an
indirect-call exclusion; arbitrary incoming IDs remain outside this proof.

S11's live calls change item-state bytes or the pause item string, never table
pointers or sentinels. Its speed and option item IDs fit the six-item groups.
The sole replacement is `" Unpause"`/`" Pause"` in group 4 item zero; the former
including NUL occupies nine bytes, exactly the original `" Pause  "` allocation.
No nominal update extends that string into a pointer table or another string.
All other menu state/text helpers change pointee bytes, not pointer topology.

Therefore two functional arrays of five DOS ints cover **the complete title
sentinel writer footprint and all nominal valid-ID readers**. This closes the
shipped menu-count premise. The wider menu gate still depends on proving all
delivered menu events obey those valid IDs and on the active menu lifetime;
malformed events are read before S10's later `m>=100` guard. The difference
between the original two symbol addresses is not an allocation record and is
not used to claim historical capacities 10 or 20.

## Windows: preload/palette copy bounds and nominal palette-63 exclusion

HCEGANT `(128,0)` declares 34 windows, 16 color rows and six groups. Window IDs
0..33 form a complete serialized set; object extents tile every window payload.
Palette `(129,0)` is exactly 96 bytes, matching 16 six-byte rows. Purge `(131,0)`
is 40 bytes, so the loader loop indices 0..33 fit its actual local array. The
zero purge flags preload windows 0,1,18,19,25. Thus the shipped preload cannot
write a negative/>=45 handle/callback/offset slot, and the shipped palette copy
has a positive length of exactly 96 bytes. Arbitrary window callers, dynamic
windows and returning resource failures are additional premises.

There is one exceptional palette field: window 18 object 3 (`1203`), type 1,
has normal row 0 and selected row 63, initial flags A003. Selection flag 4 is
absent at load. Every object render enters `win_SetColorFromObj` before the type
switch, so that initial observation alone is insufficient. The following
additional complete nominal writer/call audit excludes selected activation:

* Object-flag writers in root:22BF alter only masks 1 (visible), 2 (selectable)
  and 4 (selected). Resource loading resets type-specific data starting at 2A,
  while recalc alters rectangles/origins; neither replaces object flags. No
  nominal writer changes the auto-selection bit 0800.
* `f_218D_000C` handles this type-1 event through its ordinary branch. Its only
  automatic selection calls are dominated by `flags & 0800`, absent in A003.
  The event then reaches S19 dispatch and ProcModeEvent's case zero, which
  calls only `DoWinHelp(120E)`. Help temporarily changes visible/selectable
  state of its separate object/window; it does not select 1203.
* The primitive selected-flag writer is `win_SetObjSelectedStateI`. All its
  callers are the wrappers/group loop in root:22BF. The sole positive group
  wrapper `win_MakeGroupSelected` has no direct source caller or non-declaration
  source reference; other group invocations explicitly clear selection. Radio
  propagation also passes zero. Arbitrary external API invocation is outside
  this nominal call closure.
* The full parsed direct call census contains 38 selection/color callsites,
  including wrappers. All fixed positive selection targets are 000F, 0010,
  1205, 1305, 190E or 1910, never 1203. Variable target proofs are below.

| Variable positive-selection argument | Explicit domain |
| --- | --- |
| `g_1960[mode-4]` | Dominated by `4 <= mode <= 8`, values 0109/010A/010C/010D/010B. |
| `g_1984[YardMode]` | Supported YardMode 0..3 gives 1908/1909/190A. Startup RandYard sets zero; menu commands derive 0..3; yard events use constants 0/2/3 or a guarded XOR when less than 2; SetMapModeAnt reuses the same state. Loading is restricted to matching genuine game saves with this invariant, excluding corrupt/custom save state. |
| `win`/`obj` in SetMapPlaneLocation | Initialized zero and assigned by cases 0..3 only; guarded calls use 0008..000A and 0105..0108. |
| `s_2966+15CA` in FileSelect | Startup uses the first byte of a successful DOS absolute getcwd path, an uppercase drive letter A..Z; resets/oldDrive also allow zero. User drive events are guarded 160B..1612 and give A..H. All resulting targets stay in window 16 (or 15 for zero), never 1203. This exclusion does not independently prove every drive button exists. |

`f_22BF_094F`, the ordinary object normal-color writer, has no direct caller or
non-declaration source reference. All literal `win_SetColorNum` callers use 3.
Its variable list/elevator callers read normal/selected fields from valid list
or slider objects: those resource fields are all 0..15. The anomalous type-1
help object does not enter those helper routes. `win_DrawButtonBorder` enters
only for button types 5/17 and uses their normal field, also in range.

This establishes **nominal selected row 63 exclusion for the pinned shipped
resources, valid object IDs and the stated ordinary-state/save domain**. It
does not exclude arbitrary corrupt state or a guessed API caller, and does not
close the larger window-ID/failure-continuation gate. A functional colors[16]
owner is still deferred until that object/ID provenance is fully integrated;
no 64-row palette, fake padding or clamp is proposed.

The original `f_218D_000C` corroboration uses the actual serialized help object.
With A003 it executes 22 blocks, issues zero selection calls and preserves the
object. A single-bit altered A803 contrast executes 35 blocks and issues
`win_SetObjSelectedState(1203,1)` then `(1203,0)`. Object lookup/lock, timing,
clip services, selection and wait are explicit model boundaries; the gate and
event logic execute original DOS instructions. The receipt retains scalar
outcomes, oracle/source/input hashes and boundaries rather than instruction
dumps. This is an isolated active-original control, not full-game DOSBox parity.

## Styled text: useful narrower premise

Nine raw SHARED kind-10 text records contain high bytes (AA or D1). Across all
paired kind-21 style records, all **82 face-0100 serialized highlight intervals
contain only ASCII bytes**. Menu strings and their mnemonic second bytes are
also ASCII. This narrows which input domains can invoke the signed CRT prefix
reads. It is a serialized interval premise: DisplayCard's control/NUL removal,
position adjustment and renderer boundary handling must be connected before a
whole execution exclusion is claimed. Keyboard codes also reach `_ctype` and
are not bounded by resource enumeration. The entire CRT gate stays open.

## Falsification and validation

Permanent tests cover generic menu counts including 11/21, rejected
out-of-resource pointers/missing terminators, rejected pointer-table aliases,
the original palette-selection gate with its one-bit contrast, and the complete
pinned corpus/reviewed consumer and direct-call census. The later menu-owner
packet adds complete event delivery and five-title footprint controls. The existing audio
runner also passes malformed NDX/SMF count/truncation controls and accepts a
valid synthetic 19-track SMF. These positive out-of-domain controls prevent the
proof tools from imposing the claimed shipped maxima. The focused tests and
audio census grant no claim that the whole DOS game has run.
