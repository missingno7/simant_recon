# CRT sequence / signed ctype prefix v36

Verdict: **the genuine relative `fdata.asm` view is realizable and the historical
owner attribution is substantially stronger, but this does not close the 14
functional bytes or the ctype integration gate.** Keep historical debt too.
No production change or admission is proposed. HEAD was
`8feed73f63e4284c42a653923ea61e00f4d3a8f9`.

The new positive result is narrower than an owner-only waiver: both pinned
RTLinks can link the complete authentic members in this data sequence at
different DGROUP offsets, with `__fheap == __ctype - 46`. Their resulting
signed-character read at DD is the live flags byte of that real descriptor.
The new negative result is equally concrete: with precisely the same data
sequence, moving only the genuine `crt0fp.asm` code member changes twelve
negative-input ctype predicate results through its six relocated pointers.

## Historical attribution independent of the unknown 14 bytes

These are whole contributions, without trimming. The initial comparisons
and OMF models are in `audit.json`; actual symbolic anchors and the complete
cmiscdat binding are in `reference-audit.json`.

| Original DGROUP span | Whole member / owner | Independent evidence |
|---|---|---|
| 798C..79EC, 97 bytes | LLIBCR #35 `output.asm` | Accepted whole code owner; all three own-segment, DGROUP-framed `_DATA` fixups independently give start 798C. Full data equals its member. |
| 79ED, one byte | linker alignment | Output ends odd; next contribution is WORD aligned. Zero fill has no source owner. |
| 79EE..79EF, two bytes | LLIBCR #46 `txtmode.asm` | Accepted `REFERENCED_PUBLIC` owner; the original `dos/open.asm` external `__fmode` fixup gives 79EE. Full member data agrees. |
| 79F0..79FD, 14 bytes | candidate LLIBCR #51 `fdata.asm` | Precisely the remaining word-aligned gap; its descriptor and flags match. No historical direct `__fheap` public/fixup anchor exists. |
| 79FE..79FF, two bytes | LLIBCR #55 `growseg.asm` | Accepted whole code owner; its own-segment DGROUP-framed `_DATA` fixup independently gives 79FE. Full member data agrees. |
| 7A00..7A1D, 30 bytes | LLIBCR #77 `cmiscdat.asm` | Accepted `REFERENCED_PUBLIC` owner; four original `output.asm` external `__cfltcvt_tab` fixups give 7A00. All six pointer32 fixups bind to independently attributed `__fptrap`, 29F4:02C6. All 30 bound bytes and ordered data relocation words agree. |
| 7A1E..7B1E, 257 bytes | LLIBCR #78 `ctype.asm` | Existing accepted ctype public/table owner, including EOF. |

Thus the candidate is bounded by real code and public bindings, not chosen
from its initializer alone. The members share `_DATA`, class DATA, combine
PUBLIC, WORD alignment and DGROUP; their archive indices have exactly this
relative order. A 14-byte gap cannot be explained by the next member's word
alignment. The independently bound neighbors give it a natural candidate
contribution origin at 79F0.

The full pinned-archive census finds two 14-byte `_DATA` descriptors:
`fdata.asm:__fheap` and `bdata.asm:__bheap`. `heap.inc` defines the common
three-far-pointer plus flags-word shape. Their flags are meaningfully different:
fdata uses MODIFY|FREE = 3; bdata uses MODIFY|BASED = 9. The unknown original
span has the fdata initializer, so based-heap storage is an actual negative
contrast. fdata is the archive's sole `__fheap` provider, has no EXTDEF/fixup,
and contributes the complete 14 bytes, with its public at zero.

This strongly corroborates `fdata.asm` as the historical owner. It still does
not provide the original object/PUBDEF record, a direct historical reference
to `__fheap`, or the original archive extraction/input recipe. The existing
historical data-only acceptance route requires independently grounded public
anchors; the new neighboring anchors do not pretend to be two `__fheap`
public anchors. Do not silently convert that distinction into acceptance.

## New independent controls

Eight complete isolated programs link cleanly and run in DOSBox-X: four
contrasts under both RTLink 4.00 and 6.10. Every file input is a fresh whole
MSC 6.00AX `MAIN.OBJ`, or a complete unmodified member extracted from pinned
LLIBCR. Real LLIBCR/LIBH supply dependencies. There are no allocator or
application stubs, patched objects, inserted prefixes or padding declarations.
The original is consulted only by separate research comparison routines.

All six complete `_DATA` contributions are checked in each link: 48 whole
bound data comparisons and relocation-set checks. RTLink 6.10 reports the
contribution table directly. The 4.00 map lacks that table; its contributions
are independently derived from actual mapped publics at their OMF PUBDEF
offsets and OUTPUT's three actual code-to-data fixups. These are not inferred
from the requested order. The two map formats and the original parser failure
are explicit in the probe.

| Control under each linker | Observation |
|---|---|
| Complete members in OUTPUT, TXTMODE, FDATA, GROWSEG, CMISC, CTYPE order | `__fheap == __ctype-46`; separately emitted signed-char helper reads DD as the flags low byte. Typed flags 3→0 produce predicate 1→0. |
| Move whole `syserr.c` before the sequence | Its genuine 462-byte contribution shifts ctype and fheap by 462. Every one of the 127 startup raw prefix bytes and predicates is unchanged; DD still produces 1→0. |
| Move CMISC ahead of FDATA/GROWSEG | All whole members still bind, but fheap becomes ctype-16. DD no longer aliases the heap flags; typed flags mutation gives 0→0. |
| Move only whole `crt0fp.asm` code before the sequence | Data coordinates/order remain unchanged. `__fptrap` changes 0011:060C→0011:0012. Predicate results change for c = -31,-30,-27,-26,-23,-22,-19,-18,-15,-14,-11,-10. |

The prefix partition is complete: 78 bytes from OUTPUT, one linker fill byte,
two TXTMODE bytes, 14 candidate FDATA bytes, two GROWSEG bytes, and all 30 CMISC
bytes. It sums to 127, for c = -128..-2. CMISC's first 24 bytes are six far
function pointers, not invariant ctype flags. Their offset fields depend on
code placement and their segment fields also depend on code frames/load
relocation. The code-placement negative control proves that preserving data
order alone does not preserve the entire physical read environment.

The initial same-function observer emitted `MUT 1 1` because the compiler
reused its ctype read across the heap store. Its MAIN source/object/model and
result are preserved in `MAIN-initial.*`, `main-model-initial.json` and
`links/sequence-initial/`. It is not an alias negative. The final source calls
a separately emitted `lower_test(signed char)` twice; all eight primary
controls use that fresh whole object and give the stated results.
`observer-disassembly.txt` records the complete unbound initial/final code
as a diagnostic: the initial object has only one DD load and reuses AX;
the final object has two calls to the signed helper around the flags store.
Its unbound operands are interpreted with `main-model*.json`, never as final
addresses.

## Exact remaining premise for the heap slice

D1..DE are c = -47..-34, so a source link can account for their physical
owner by requiring the actual FDATA public at ctype-46. DD specifically
reads its flags low byte at descriptor+12. This is a useful new binding,
not proof of the original descriptor's runtime state.

The minimal stock CRT's startup mutates all three heap pointers before main:
the observed descriptor contains three far pointers 1966:0000, then flags 3.
The original file contribution initially has three null pointers. More
decisively, the original `stdalloc.asm:__myalloc` `_malloc` far-call fixup
resolves to the game's allocator at 171C:2208. The minimal program uses stock
malloc→fmalloc instead. The v36 runtime/API controls establish genuine
mutable heap storage, but cannot stand in for that application-specific
startup and writer graph.

The current 188 hash-verified source objects have no `__fheap` or `__fmalloc`
declaration/live fixup. The application's same-object `__ffree`/`__frealloc`
declarations belong to its own definitions. None of the archive's seven
`__fheap`-importing members is among the 90 attributed original runtime code
owners. A research locator finds no intact whole member or exported body
for those seven members anywhere in the original units; this excludes those
pinned spellings, not rewritten/partial/unregistered code or computed writes.
The prior full original operand census likewise excludes direct numeric
79F0..79FD operands within its disclosed scope, not computed aliases.

Therefore the missing premise is **original owner/state-transition
equivalence for the complete D1..DE slice in the real application**, including
any indirect writes. It is not merely that some unrelated broad gate is open.
Neither matching initialization nor this isolated startup proves that the
14 original bytes retain their initial values, or that the independent
application's CRT selection leaves the same field state.

## Disposition and prior exhausted classes

Retain all 14 functional and historical debt bytes. Preserve the new result
as a relative-owner binding candidate. A future granular receipt could require
the genuine whole member, its archive hash, complete object/public/fixup shape,
and `__fheap == __ctype-46`, with these order/binding contrasts. The existing
`ctype-out-of-range-index-layout` gate must still retain the application's
14-byte state equivalence, all applicable remaining prefix reads (including
relocated CMISC pointers), and the separate 0x8xx dialog suffix dependency.
Do not remove the data debt through an owner-only disposition while that
semantics premise lacks a reviewed proof.

Earlier classes remain exhausted rather than retested: generic unreferenced
data/code-member autoload was rejected by the clean v37a librarian controls;
A2/A3 comments are ordinary OMF pass/module metadata; v38 found no app
unused `__fheap` EXTDEF trigger; moving only root:171C first left v39 selection
unchanged under both linkers. The incomplete full-app images were never run.
Their 6.10 fdata-without-fmalloc trigger remains unexplained.

Authentic local RTLink 4.00 READ.ME lines 1966..1969 explicitly describe RESCAN
as establishing segment order by scanning a library. Its HLP lists FILE,
LIBRARY, RESCAN and ORDERBYCLASS. That supports the distinction between
selection and ordering, but does not identify the historical selection cause.
6.10's documented DROPUNREFERENCED improvement requires C7/VC1 packaged
functions compiled with -Gy; it does not explain these MSC6 ordinary OMF
members. No undocumented historical extraction rule is invented.

## Reproduction / identities

All new artifacts are confined to this worker directory. `probe.py audit`
performs research comparison and captures whole members; `probe.py compile`
builds MAIN; `probe.py run --plan NAME --profile PROFILE` links and executes
one isolated control. `reference_audit.py` performs the separate original
reference/binding research. `finish.py` consolidates controls and writes the
packet index; `finish.py --recheck` checks its pins without invoking the
compiler, linker or oracle. No search/promotion candidate is claimed,
`source_only_dos.py` is untouched, and validate.py was not run.

The packet index records exact raw-byte hashes of sources, whole objects,
tool trees, logs, maps, executions and receipts. Selected stable pins:

- LLIBCR: `3d0c6ae92972789e87def01fa96351c39216d731d5c880370155c5613d78c884`
- FDATA whole OMF: `7eb6a9bfcb257d6470b0bc9c9f7c6215052a7a78749e463a4a6ebaa2294e70ec`
- MAIN.C: `a79648eae81198d3bf43694e3108ed2724f671ee73e10264acbe5989b8ebc324`
- MAIN.OBJ: `6ead2ac7158a6d7a67ac1b6e279a289d74db15a76d6dc605a34c2e305a57399d`
- audit.json: `0318cf5842182eefa2d05b964502bf03400ce0c95694e6d0f4ebaac2b1a26de5`
- reference-audit.json: `b46b28fa9d0f18f17526c3b6ec0848b67e20cf200e4c11f3d1d3a25c764d80c1`
- summary.json: `96a459ef6d37f89bc8c03c28ea3d48666a88c3cea553586073a84a497493fa8a`

These are research proof artifacts, not an independent game executable,
historical identity claim, production gate implementation or source admission.
