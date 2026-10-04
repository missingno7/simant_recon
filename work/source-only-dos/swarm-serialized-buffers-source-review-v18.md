# DrawSwarm serialized buffers: functional source review v18

Status: **source-functional candidate, unadmitted, `root_claimed: false`**. The audit supports four independent natural `unsigned char far [50]` objects as the current source contract. It does not identify the original COMDEF translation unit, historical capacity, common ordering, or original byte equality.

## Source contract

The audit scanned 127 canonical modules and 29 strict effective whole-module sources (156 unique source paths), plus the code/data registries and 58 MASM source files. The four identifiers occur only in `DrawSwarm`, its textually identical effective-module copy, and S09 `SaveRec`. The only address escape is each exact base in its `SaveRec` row. No other source writer, pointer/aggregate view, registered interior symbol, code symbol in FAR_BSS frame `50F6`, or numeric address view in the scanned C/MASM sources was found. No extent or padding was inferred from neighboring addresses or gaps.

S13 declares signed-byte indexed views. Both active loops test `i >= 16` before accessing the buffers, so direct game indices range from 0 through 15. Game code reads the bytes as signed coordinates and writes through the `SRand16()-10`, `SRand1(3)-1`, and zeroing paths; it does not pass a buffer address. S09 separately declares unsigned-byte views and registers four exact-base rows with `size=1, count=50`. `LoadGame` reads `count * size` raw bytes and `SaveGame` writes that same span without conversion. Consequently bytes 16–49 remain observable saved state, including state supplied by a load, and must be retained even though `DrawSwarm` does not directly index them. The tentative far commons also receive actual startup zero state.

This is a storage/view distinction: `DrawSwarm` interprets bytes as signed and `SaveRec` views the same storage as unsigned raw bytes. MSC OMF records byte width and extent but not signedness. The result makes no blanket C type-compatibility claim.

## Candidate and controls

[swarm-serialized-buffers.c](providers/swarm-serialized-buffers.c) is the test-owned provider: four independent `unsigned char far [50]` tentative definitions. MSC 6.00AX emits exactly four far COMDEFs with count 50, element size 1, and length 50, with no live content, public, or fixup. The tests passed with RTLink 4.00 and 6.10:

| Control | Result per linker |
|---|---|
| Actual startup zero state for all 50 bytes of all four objects | PASS |
| Signed `DrawSwarm`-style byte view, active slots 0–15, untouched zero tail | PASS |
| `SaveRec`-style raw save/load roundtrip of all four 50-byte rows (200 bytes) | PASS |
| Wrong element type (`unsigned int[25]`, same 50-byte total) | expected FAIL |
| Wrong extent (`unsigned char[16]`) | expected FAIL |
| Wrong exact base (first row shifted by one byte) | expected FAIL |

All 12 fixtures produced clean links and executables. For every consumer fixture, its OMF imports all four candidate names; both RTLink map public sections resolve all four names and the mapped test-owner spans are checked within that fixture's FAR_BSS allocation. A case counts as passed only if the version banner matches, the link log has no warning/error/unresolved/fatal line, the map checks pass, and the runtime output matches. The wrong-extent fixture is verified against its intentional 16-byte test owner; the other fixture owners map 50 bytes per symbol. These are test-provider link checks, not claims about the historical image's physical capacity.

## Limits and reproduction

The 50-byte extent is justified as the complete source-visible serialized span and functional storage contract. The audit does not establish storage requirements beyond that span, the historical owner TU or COMDEF capacity/order, or exact original bytes. It preserves raw tail state without assigning those bytes unobserved game meaning. It does not claim that all possible C declarations are interchangeable.

Reproduce from the repository root:

```powershell
python work/source-only-dos/swarm-serialized-buffers-probe-v18.py
```

The JSON report is [swarm-serialized-buffers-source-review-v18.json](swarm-serialized-buffers-source-review-v18.json); fresh generated fixtures and pinned runtime artifacts are under `build/workers/dos_swarm_serialized_buffers/durable-v18/`. The report pins the probe, provider, requested candidate table and family review, the 156 scanned source files, registries, toolchain inputs, and runtime artifacts. Nothing is admitted or promoted.
