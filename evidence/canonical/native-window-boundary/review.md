# Bounded window ABI audit

The static audit first reviewed the consolidation draft and its generated C.
`installed-correspondence.json` now proves identical audited installed text
under CRLF-to-LF conversion only and records actual installed file hashes.
Original review pins in `receipt.json` remain immutable historical provenance;
its scratch paths are not replay dependencies. Fresh annotated DOS disassemblies,
full shipped resource parse, and native controls are retained alongside this review.
`replay.py` verifies the current audited source/resource domain and compiles
current window helpers, writing only into a fresh `build/` output directory.

## Classification

| Adapter/helper | Finding |
|---|---|
| window_parameter_abi_v1 | Explicit supplied values/count and 16-bit types are ABI conversion; zeroing unprovided slots is semantic normalization of DOS caller-stack residue. Validated game observers do not consume those slots for known shipped callers/resources. Guards are native unsupported-domain failures. |
| window_swap_parameter_abi_v2 | Same normalization, with concrete nonzero DOS state-write correspondence below. Not literally mechanical state equivalence. The 3 shipped calls target windows 1 or 25, whose parameter vector is unobserved by canonical game behavior. |
| newgame_zoom_window_v1 | Mechanical recovery of actual AX fastcall argument at exactly two NewGame calls. Branch and ordinary state/call order unchanged. Does not prove downstream zoom completeness. |
| s26_window_object_views_v1 | Mechanical far-pointer table representation conversion for four lookups, valid only for currently bound live windows. Source branches, writes and call order preserved. Null guard does not implement graceful failure at its immediately dereferencing callers. |
| window_parameters/window_refs | Width-preserving writes and sequential resource-to-host pointer correspondence on valid owner records. Adds malformed/stale/missing-argument/allocation failure policies. The helper is an ABI resource boundary, not proof of arbitrary records. |

No emitted historical return-address values should be manufactured. No new
compatibility memory architecture is justified by this audit. The optional-word
normalization must remain explicitly classified rather than called universally
mechanical. Its bounded game-observable equivalence is supported below; raw
window bytes differ.

## Actual DOS argument correspondence

`win_Swap` is root:20E8:032F. From/to are `[BP+6]`/`[BP+8]`; `[BP+0A]`
is ignored. At 042D..0445 it reads `[BP+0C,+0E,+10,+12]` and writes
window+10,+12,+14,+16 in that order, unconditionally before `win_Recalc(to)`.
All three actual callsites push only to, then from: YardToMap at 04AC..04B4,
MapToYard at 04EF..04F7, SetYardMode at 0383..038B. Therefore these words are
not four secretly supplied C arguments:

* YardToMap/MapToYard are frameless. At caller entry let SP point at its far
  return IP. The unused word is that IP; p0 is its far return CS; p1..p3
  are subsequent caller-frame words. Their values depend on the invoking
  path. They are not proven zero.
* SetYardMode has BP, four local bytes and saved SI. The unused word is saved
  SI. p0/p1 are caller BP-4/BP-2, the live far address temporary established
  at 0299..02A3 for YardMode (registered 50F6:035C). p2 is saved caller BP;
  p3 is its return IP. This directly excludes the assertion that all omitted
  DOS words were zero.

The adapter instead supplies count=0 and four zero words. It replaces only the
four stores with the helper/status branch. Both success paths keep the source
order: lock/snapshot from; conditional border/hook/kill/clear/hook; unlock from;
lock to; write destination origin and rectangles; store parameters; recalc;
hook; set open bit; border bookkeeping; clipping/drawing/hook; unlock; clip_Off.
On helper failure the source window is already closed and destination origin/
rectangles already changed. It calls Punt, then unlock/return if Punt returns;
there is no rollback. That failure behavior is newly introduced.

`win_Open` root:20E8:04B6 reads `[BP+8,+0A,+0C,+0E]` at 04ED..0507.
The 0/2/4 optional-word calls supply respectively none/first two/all four;
others are frame residue. `win_DoProxMenu` root:22BF:0BAB explicitly forwards
its `[BP+0A,+0C]` regardless of whether its caller supplied them. Native count
and p0/p1 preserve actual supplied arguments; count=0 for AntMenu window 6
replaces the forwarded residue. The count=2 forwarder zeroes Open's final two
slots. `win_Open` retains its top-window equality branch and final
`win_FlushEvents` on success or already-top entry. Its new failure return skips
the final flush. Normal Punt routes through S15:0152 and exits; recursive Punt
can return, so the fallback is material and must not be called original DOS
behavior.

## Resource and observer closure for normalized slots

Fresh parser walked every active kind-0 window ID 0..40 in all local NDX/DAT
pairs. It found exactly 34 records, HCEGANT IDs 0..33. No SHARED or SOUND
window rows matched. Resources 0, 1 and 25 have no mode-5 axes. Thus the
Swap targets 1 and 25 have no source geometry read of any parameter slot.

Across canonical sources the sole direct reader of window+10..16 is
`f_2505_04D7` (04F7..0509), called solely by `f_2505_03B9` case 5 from
`win_Recalc`. No canonical code writes the axis-mode words: m20E8:0903 only
reads them while editing object origins. Mode 5 reads only the indexed supplied
slot. Actual resource requirements are:

* IDs 7..17, 29 and 32: only indices 0,1, all active direct Open/Prox callers
  supply two coordinates. DoExpMenu's dynamic submenu IDs are the canonical
  list 12,15,16,17,13,14 and supply two.
* ID 30: indices 0..3, PictureDialog's aliased f_20E8_04B6 call supplies all
  four rectangle coordinates.
* Other shipped IDs: no mode-5 reader. The omitted words may change raw state,
  but their values do not drive canonical window geometry or behavior.

Both function spellings and canonical aliases were inspected. The generic
bring-forward path f_20E8_0725 still calls Open with count=0. Its literal game
callers target 1 and 25. Its event-selected path is f_218D_0451: a top window
with flag 0x40 skips the search. Every shipped mode-5 window has 0x40. This
explains modal behavior; it is not an unrestricted proof that arbitrary caller-
constructed stacks cannot attempt a mode-5 bring-forward. That domain is
rejected by the new helper, whereas DOS would use physical frame words.

Additional observers were checked: all canonical f_2505_0006/win_WinAddr and
win_handles consumers; S26, border/title/draw paths, event handling, m00BA
registered close/change hooks; f_1FD2_044F (copies first rectangle only); and
f_22BF_0E83 (copies object0 origin x/y only, no parameter vector). There is no
SaveWin/CloneWin symbol or heap-window serializer in current canonical source.
SaveGame writes the static SaveRec owner list; neither that list nor its load/
save setup includes window handles/payloads. Generic allocator relocation can
copy the differing bytes but does not interpret them. No active db_SaveObject/
db_ReplaceObject callsite serializes a window. Winheaders in m00BA are separate
intro-data input, not a live window-header dump.

This discharges the identified omitted-slot differences for the present
canonical game observers and immutable local shipped assets. It does not
cover external/debug raw-state observation, resource replacements with changed
mode-5 requirements, unknown heap-corruption observations, or arbitrary direct
API calls. Such cases cannot be admitted as pure ABI equivalence.

## NewGame register proof

At S15:0508 NewGame calls f_22BF_0A65 without setting AX. SetDefaultWindows
unconditionally calls OpenEditWindow(0). The following SetMapPlane ends in
UpdateEdit, which returns AX=0 both if window 0 is closed (IsWinOpen returned
zero and OR/JE preserve it) and if open (last clip_Off at root:1E57:0362 has
SUB AX,AX). SetMapPlane's POP/MOV SP/POP/RETF and NewGame's POP BX, OR SI,SI,
JNE do not change AX. Thus predicate receives win=0. Its false result is AX=0;
OR AX,AX / JNE at 050D/050F preserve that zero into the zoom call at 0511.
Explicit int16_t(0) is actual register-ABI recovery, not guessed default input.
Only those prototypes/calls change; r!=0 still skips both and a true predicate
still skips zoom. Existing canonical zoom's uninitialized `saved` rectangle
on first zoom is unchanged; prior resource0-profile-v2 documents clip-list
dependence on that residue. This adapter does not resolve that separate debt.

## S26 and resource-helper invariants/failure domain

Original drag loads object1 via LES at 0478 from +30, then object0 at
05A5/05A9 and refreshed object0 at 05F7/05FB from +2C/+2E. Grow loads object0
at 0832/0836. The four replacements retrieve the same sequential object
addresses from the native registry. Struct scalar fields retain offsets
0C,18,1A,1C,20,22,24..2B under int16_t conversion and pack(2); widened `objs`
member starts +2C but is never actively read after replacement. All writes to
origin, width/height, flags, rectangles, offsets, and call ordering are intact.

The S26 helper adds null/count/registry checks, returning NULL. Callers still
dereference that result. For absent/stale bindings this may fault; it is not
a Punt/recovery contract. On the supported loaded/locked resource domain,
RepointObjects binds the owner Handle and exact allocation extent; parser
validates header/table/positive sequential object extents before populating
sidecars. Its source sequential assignment loop remains. Relocation refresh
requires identical count, offsets, sizes and types, then retargets all pointers;
on failure registry wire=NULL hides stale addresses. Native OOM, truncation,
negative extent, invalid serialized handles, stale buffers and wrong types
are boundary failures rather than newly accepted ordinary game states.

window_parameters requires registry/current buffer/count correspondence and
valid object arrays/sizes; accepts only counts 0,2,4; checks every mode-5 index
before any parameter write. Source had no such guards. For valid supplied
references it writes four little-endian signed 16-bit words in source order.
Fresh native controls against these exact draft helper files passed on all 34
actual resources, with required count 0/2/4, missing-argument rejection before
write, count-1 rejection before write, and successful four-word store. They
corroborate representation/domain checks, not whole-game semantics.

`ui_model/menus/source_record_view` is not called by these four adapters or
their window helper chain. It is used by the separate S17 menu adapter and was
not represented as evidence for this window audit.
