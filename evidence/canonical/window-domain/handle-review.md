The supported window-handle footprint is 34 cells (136 DOS bytes). This closes
the independent storage import in the existing shipped/default successful-service
domain. General window object-index and exceptional effects remain unresolved. The
separate [callback/rectangle adjacency contract](array-gate-review.md) now closes
by composing this ID proof with the palette and array extents.

The owner is a near array of 34 far master-handle pointers, 136 DOS bytes.
This is a supported functional footprint, not a historical allocation or placement
claim. MSC600AX /AL /Os /Gs emits only a near COMDEF of 136 bytes. The other
45-element callback, rectangle, lock-depth and cached-pointer arrays do not
establish this candidate's capacity.

The four direct consumer modules have fourteen table identifier occurrences.
LoadWindow stores an allocator master handle; IsWinOpen clears a discarded
entry; final Unlock clears the discarded window and cache. Consumers use cells,
not an escaping table base. Original CRT initialization clears the proposed
table inside DGROUP 8B9E..94EF before C initialization/main. All 307 original
save destinations exclude the table. These facts need the complete incoming
ID bound; they cannot establish it independently.

The reviewed incoming-domain decomposition is:

* Direct literal window/object arguments select slots 0..33.
* Preloading uses i<<8 for the shipped count 34.
* Open/Swap destinations and every stack reader use the independent stack
  preservation proof. There are 32 possible destinations, but intro 3 and
  prompt 33 cannot coexist, preserving the 31-entry-plus-sentinel stack.
  NewGame's two source-omitted arguments are original AX=0, not arbitrary ints.
* Event dispatch admits an ordinary code only when its high byte equals the
  valid stack top. Hover's selected descriptor code is checked against that
  same top; g6368 comes from these events or the bounded application setters.
  Move/resize helpers derive win from nonempty stack top. Focus traversal adds
  only an object index bounded by the shipped count (maximum 31).
* Resource geometry modes 1..4 read 1,076 pinned references, all selecting
  slots 0..33 and valid target objects. The k/axis formal is a field selector,
  not an ID. Mode 5 uses the already bounded enclosing window. The sole
  linked slider target is 1609h. Registration and selected/selectable group loops mask to the
  window base before adding object indices, so there is no high-byte carry.
* Existing application menu/proxy arithmetic selects slots 6..17 or 32;
  an invalid low byte such as FFh does not change that handle bound. Its
  unchecked object/graphics effects remain a separate open contract.
* History state is sentinel or 0..9; the previous selected object is therefore
  1503h..150Ch. YardMode is initialized/reset to 0 and ordinary writers preserve
  0..3. Its table yields 1908h..190Ah. The mode-4 branch bypasses the table.
  Valid source-produced saves preserve these states; arbitrary saved words do
  not. The guarded mode table selects 0109h..010Dh; Edit graphs select 11h..13h.
* ScoreDialog's loops produce 1802h..1809h. SetMapPlaneLocation's switch produces
  only objects 8..10 and 0105h..0108h; plane values themselves are not IDs.
* ProcMenu's event-pointer dependency terminates in a finite switch. Its yard
  cases 21h..24h produce modes 0..3, and its direct window test is 1900h.
* FileSelect initializes its drive state from the first getcwd character,
  changes B to A when needed, and otherwise preserves it or accepts drive
  buttons 160Bh..1612h. Even the signed-byte startup range plus 15CAh stays
  within slots 21..22. The K: object-index failure remains explicit.
* Uncalled library entry points require absence of direct calls, bare function
  references, registry/program aliases and ASM references before exclusion.
  The full-int second argument of f2505_033C must never be silently truncated.

Negative controls are essential: slot 34 is read before a missing-resource
diagnostic; a nonzero adjacent cell bypasses loading altogether. Guard 41
stops only on the first-error path, while actual reentrant Punt returns.
A fabricated 2201h descriptor is returned unchanged, and arbitrary YardMode 5
produces 5241h from an original table overread. None is admitted by padding,
clamping, expanding a domain, or treating a returning diagnostic as fatal.

The composition is an induction from initialized state, not an assumption that
arbitrary preexisting handles are valid. CRT zeroing, the empty sentinel stack,
zero descriptor counts and the pinned resource control record establish the
base. Literal/preload roots create valid master handles; bounded stack and
application calls preserve valid window numbers; unchanged resource fields,
descriptor copies and guarded dispatch preserve the next incoming IDs. The
allocator/clear rules preserve cell provenance. A source-produced save round
trip preserves the separately proved scalar domains and never overwrites the
table, stack, descriptors or private selector arrays.

The complete coverage guard records 217 relevant function definitions, 1,033
direct calls, seven drawing-hook registrations and no ASM references. The
original 443 direct API slots include both Swap arguments and both full-int
f2505_033C arguments. All 128 reverse-flow boundaries are accounted for by the
classes above; 18 uncalled formal slots remain excluded only while the guarded
call/reference census has no entry. Two source-omitted NewGame arguments retain
their original AX proof. File and alias checks reject new writers, callbacks,
callers and assembly references; unrelated storage inventory additions do not
invalidate the proof. The exploratory call graph and per-case traces are not
production inputs.

The supporting packets are [stack preservation](stack-review.md),
[application proxy IDs](application-ids.md), [event/resource IDs](event-ids.md),
[local application IDs](local-ids.md), and [palette/object provenance](palette-review.md).
`handle_owner_probe.py` retains the original CRT, read-order, save and escape
controls. `handle_ids_guard.py` guards the reviewed caller coverage. Run the
permanent regression with `python -m unittest discover -s tests -p test_window_handle_domain.py`.

Native builds use the same canonical array through ordinary pointer widening.
The former 45-cell native definition and its declaration rewrite are retired.
Independent 45-entry lock/cache/callback/rectangle arrays keep their proven
roles. Historical placement/capacity and the remaining invalid-object,
graphics, optional-word and exception behaviors are not admitted here.
