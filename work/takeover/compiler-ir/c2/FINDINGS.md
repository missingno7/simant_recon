# MSC 6.00AX C2 local-home tie-out

This bounded investigation captures C2's output via the CL `/B3` pass override,
then compares named-local records from its `PR` stream against homes from an
ordinary MSC600AX `/Fc` listing parsed with `tools/slots.py`. It does not fully
decode the C2 stream or change production sources, layout, or acceptance state.

## Result

The four controls all expose the local's name in pre-C3 `PR`, but none contains
the complete signed 16-bit frame offset reported by the final listing anywhere
in that `PR` file. The listing reports `-4` (`FC FF`) for the far-pointer local,
the renamed far-pointer local, and the `long`; it reports `-2` (`FE FF`) for the
`int`. Their nearby named-record bytes instead include `FC 00` or `FE 00`.
Because neither full signed sequence occurs in those files, those controls
alone could not establish that C2 serialized the assigned frame home. A final
same-type, same-name discriminating control moves `saved` from BP-4 to BP-6:
the byte at offset +10 from the `saved` name in `PR` changes from `FC` to `FA`,
matching the low signed byte of the `/Fc` homes (-4 and -6). This supports a
tentative one-byte home/displacement field in the pre-C3 named record. The
adjacent byte also changes (`00` to `06`), so the field format is not decoded
and whether C3 uses that byte directly or transforms it remains unknown. Those
named-record controls alone say nothing about ownership of a split pointer's
segment word; a separate bounded control below tests that stream reference.

| Control | `/Fc` local home | PR name offset | Bytes after name and NUL | Signed 16-bit home found in PR? |
| --- | ---: | ---: | --- | --- |
| far pointer (`saved`) | -4 (`FC FF`) | 76 | `80 C1 00 00 FC 00` | No |
| renamed far pointer (`payload`) | -4 (`FC FF`) | 76 | `80 C1 00 00 FC 00` | No |
| `long` (`saved`) | -4 (`FC FF`) | 76 | `80 82 00 00 FC 00` | No |
| `int` (`saved`) | -2 (`FE FF`) | 76 | `80 81 00 00 FE 00` | No |

The rename control preserves the type-like bytes and the `FC 00` pair while
changing the name. These records demonstrate that names and type-like data
reach the pre-C3 stream; they do not establish the meaning of the trailing
bytes.

To separate local type from home, the baseline `saved` far pointer was held
constant while an address-taken `int hold` was passed to `barrier` and read
after the call. `/Fc` places `hold` at BP-2 and moves `saved` from BP-4 to
BP-6. In the C2 `PR` record, the same `saved` name and type prefix remains, and
the byte at name-relative offset +10 changes `FC` -> `FA`; the two bytes there
are `FC 00` -> `FA 06`. This is the positive discriminating control supporting
the tentative signed 8-bit home byte. The alternative `long hold` control puts
`hold` at BP-8 but leaves `saved` at BP-4, so it was not captured through `/B3`
and provides no additional `PR` comparison.

The wider pass investigation found no established user-facing optimizer,
lifetime, symbol-allocation, or stack-allocation report switch in the pinned
MSC 6.00AX binary strings or the tested CL options. `/Zi` changes C2 raw streams;
for the earlier one-line local control `/Zd` matched no-debug at this boundary.
`/B3` is the useful observation hook because it runs after C2 and before C3,
but the captured files are binary and remain undecoded. This experiment does
not provide an optimizer/allocation report.

## Reproduction

From the repository root:

```powershell
python work/takeover/compiler-ir/c2/verify_homes.py
python work/takeover/compiler-ir/c2/probe_home_delta.py
```

The runner checks pinned tool hashes, captures the four sources through `/B3`
using `capture_b3.py`, compiles them normally with `/AL /Os /Og /Oe /Zi /Fc`
(the `msc600ax` profile appends required `/EM`), and removes each normal
compile's temporary directory after parsing. `/B3` captures remain only under
ignored `build/workers/c2_observability/b3/`. `home-tieout.json` records source
hashes, listing slots, `PR` hashes, byte windows, and exact full-word searches.
`probe_home_delta.py` first checks the two new controls' `/Fc` homes and invokes
`/B3` only for a control that moves the same `saved` local; here, only the
address-taken `int` control moved it. `home-delta-probe.json` records both
listing results and the C2 byte comparison. All six exact source files are in
`sources/`.

## Split far-pointer segment-word reference

The four `split-far-*` controls keep the far-pointer use live across a call,
with its offset in `SI` and its segment word stored in a BP home. The ordinary
`/Fc` listing gives these pairs (the slot is the named whole-pointer base):

| Control | Named `text` slot base | Segment-word home | C3 behavior |
| --- | ---: | ---: | --- |
| base | BP-4 | BP-2 | store `DX` to `[bp-2]`, reload `ES` from `[bp-2]`; offset stays in `SI` across `barrier` |
| whitespace | BP-4 | BP-2 | same listing and byte-identical `PR`/`GS` streams to base |
| address-taken `int hold` | BP-6 | BP-4 | corresponding store/reload at `[bp-4]` |
| address-taken `long hold` | BP-8 | BP-6 | corresponding store/reload at `[bp-6]` |

The named slot moves with the segment word, so the latter is at base+2 in all
four controls. This does **not** establish an anonymous/CSE temporary: the
segment spill may simply be the high word of named `text`. The `int` and `long`
cases are positive changed-home controls while the whitespace source is the
negative control.

In C2 `PR`, the tiny controls contain the operand-like store motif
`01 02 04 FE|FC|FA 05` and reload motif
`01 02 01 08 04 FE|FC|FA 05`; the displacement changes with the `/Fc`
segment-word home (-2/-4/-6), while the rest of each motif is preserved. The
base and whitespace `PR` and `GS` streams are byte-identical. This demonstrates
that the current candidate's segment-word addressing displacement is present
in the pre-C3 output. It does not decode the `PR` grammar or show which earlier
pass chose the home; it only places this reference before C3.

For fleet S15, `/Fc` names `text` at BP-4 and stores the returned segment word
at BP-2, again base+2. Its `PR` named-local bytes at offset +9 are `FC 06`
(the whole named pointer slot), while a nearby `01 02 04 FE 05` matches the
tiny-control segment-store motif. The same record/motif positions are present
in the same-line-top-extern capture. No matching `FA` store motif occurs near
S15's `text` record, and the exact tiny reload motif is not present there.
`GS` contains no candidate segment displacement in the tiny controls and no
literal `text` name in S15; this is not evidence that `GS` lacks an indirect
reference.

The original historical target's C2 streams/debug identity are unavailable in
this probe, so its reported BP-6 cannot be assigned to a whole-pointer base or
segment half from these candidate captures. The unresolved compiler fact is
where/how that target split component receives its home across C2→C3, including
whether it is coalesced with a named pointer word. These captures establish a
pre-C3 reference for the candidate S15 BP-2 segment word, not the target's
BP-6 allocation/coalescing decision.

Reproduce this bounded comparison with:

```powershell
python work/takeover/compiler-ir/c2/probe_split_segment.py
python work/takeover/compiler-ir/c2/inspect_s15_context.py
python work/takeover/compiler-ir/c2/analyze_split_streams.py
```

The source, listing, and `PR`/`GS` context hashes are recorded in
`split-far-listings.json`, `s15-segment-context.json`, and
`split-far-stream-analysis.json`. Raw captures stay in ignored
`build/workers/c2_observability/b3/`; no binary artifacts are checked in.
