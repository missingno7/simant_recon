# DOS control-state ownership review

This is a scratch candidate for `functional-source-oracle-v1`. It does not
change `src/`, the manifest, the promotions journal, or the source-only build
inputs. `ant-ui-control-owner-probe-v17.py` freshly scans the 127 canonical
code TUs, the 29 effective strict module sources, and the reviewed DrawBalloons
correction. It compiles only test-owned C sources and runs the bounded far-communal
controls under the pinned MSC runtime and RTLink 4.00/6.10. No game executable
or original object is an input.

## Proposed functional owner

The candidate definition in `providers/ant-ui-control-state.c` covers one semantic UI
control-state family: two three-word level triples; the bitmap size; four
triangle dimensions; two six-point triangle records; the slope word pair; and
the two derived knob points. Its object extents follow declared C fields and
the source writes described below. It does not fill address gaps or include
unrelated external declarations.

`root:0798` is the producer module. `initControls` loads bitmap 0x578 into
`knobSize`, copies three words each from the existing `fd_3D57_080A` and
`fd_3D57_07EC` default tables to `modeLevels` and `casteLevels`, and calls both
control-change functions. Those call `InitTriVars`, which writes all six
members of the mode/caste `TriPoints`, `triHeight`, `triWidth`, `triWidthR`,
`triWidthL`, and `fd_50F6_382E`; `SetTriLatPoint` writes each derived point.
The four default/preset tables remain owned by the existing data-only
`src/data/d3D57.c` source, with initialized bytes visible at lines 203-220.

The saved level arrays have direct S09 rows `{2,3,&casteLevels}` and
`{2,3,&modeLevels}` (six bytes each). The table has only address views, so it
does not supply their type. Canonical `root:0798` defines `TriLevel` as three
unsigned words, while `root:1383`, `root:0E2E`, and `S25:39C7` read `modeLevels`
as three words. The differing C views all agree on six bytes and the save
extent. The generated owner therefore keeps the natural `TriLevel` shape used
by its producer and consumers; the C array view stays a separate translation
unit view. `casteLevels` has the same `TriLevel` fields and six-byte save row.

The registered names at 50F6:0482/049E and 50F6:380E/3810/3812/3814/3832 are
exact-base aliases for the seven reviewed symbols. The symbol registry has no
registered interior names in those extents. 50F6:3816, 3822, 382E, 0358, and
022E are separate, typed objects immediately used by the same producer/math
path and are included. Adjacent `fd_50F6_0468`, `fd_50F6_0370`,
`fd_50F6_024E`, animation handles/IDs, and unknown 50F6 fields remain separate
work; this provider does not claim them by proximity.

The fresh source graph contains no accepted-storage claim; it finds no relevant
symbol or numeric-offset access in the 29 canonical ASM sources and records
potential numeric matches separately from code labels. The fresh probe checks
compiler communal sizes, zero-fill, same-symbol struct/array/byte views, and independent
RTLink allocation. It cannot prove startup call ordering or historical layout.
The dynamic producers remain required before their values are consumed. The
existing RTLink controls prove the MSC startup's FAR_BSS zero-fill contract;
they do not replace that ordering review.

The same `initControls` function also stores `fd_50F6_0468 = 1` and
`fd_50F6_0370 = fd_50F6_024E = -1`; S09 serializes those three two-byte fields.
Their current registry names do not describe behavior, so they remain explicit
separate state work. The 37F2/37F6 handles and 37FA/37FC animation IDs have a
create/update/close lifecycle in this TU and remain outside the numeric
triangle-state owner candidate.

## Explicit limits

This scratch candidate is not admitted to the generated source-only build. The
source scan and probes are evidence for a parent review. Original 50F6 offsets,
the original COMDEF contribution owner/order, runtime call ordering, and the
nearby unresolved control handles/flags remain outside its claim. Unknown
initial state or layout bytes stay unresolved.

## v17 durable candidate evidence

The durable provider is `providers/ant-ui-control-state.c`; the adapted guarded
probe is `ant-ui-control-owner-probe-v17.py`. Its fresh report is
`../../build/workers/dos_v17_fresh/antctl/ANTCTL.V17.JSON`. The probe rebuilds
the source reference scan from the durable 127-TU intake, the 29-entry strict
index, and the reviewed DrawBalloons source, then pins and scans the resulting
156 distinct source files. It also records the intake/index/symbol/manifest
pins, compiler and linker inputs, provider hash, and probe hash.

The runtime fixture keeps the original `/AL /Os /Zi` compiler request (effective
profile flags include `/EM`) and reports one positive isolated control per
RTLink profile: `isolated_owner_zero_fill_cross_view_and_independent_extent`
returned raw `PASS\r\n` under RTLink 4.00 and 6.10. Each report row also requires
the EXE and map, all 12 expected owner names in the map, and no unresolved
linker diagnostic. The separate `/AL /Os /Gs` plus `/EM` control compiles the
exact durable provider and preserves its OMF communal records and external
record order; it is compiler-only and is not runtime evidence.

Both negative controls remain compiler/OMF-only: the shortened `modeLevels`
reports a four-byte FAR communal where six bytes are expected, and initialized
`knobSize` becomes four-byte initialized FAR_DATA public storage rather than a
communal. Neither negative object is linked or described as a runtime rejection.
This package remains a source-only candidate with `root_reviewed=false` and
`admitted=false`.
