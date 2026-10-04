# DGROUP 60B0 ownership review: hot-box semantics (v35)

Status: research only. No canonical source, manifest, promotion journal, debt ledger, layout file, or Git state was changed. The old `TIMER_COMPATIBLE` label is semantically wrong: code in `root:1B73` treats this 18-byte shape as an event-region record. Source-functional provenance is the mouse event/hot-box subsystem; a complete natural `HotBox` type and field-level initializer are justified. Historical defining object/TU, registration, and runtime reachability are still unknown, so this is not an admission or a harmless/dead-data finding.

## Field interpretation

`f_1B73_0AC3` and `f_1B73_0B00` copy nine words (18 bytes) from the first far pointer into a far list entry (`src/root/m1B73.asm:1538-1619`). The walker advances by `0x12`; `f_1B73_0CEF` consumes the copied fields as follows (`1833-1879`):

| Offset | Natural field | Width / meaning for this record |
|---:|---|---|
| `+0` | `left` | signed 16-bit screen x coordinate |
| `+2` | `top` | signed 16-bit screen y coordinate |
| `+4` | `right` | signed 16-bit screen x coordinate |
| `+6` | `bottom` | signed 16-bit screen y coordinate |
| `+8` | `callback` offset | low word of a far function pointer |
| `+10` | `callback` segment | high word; the original relocation here targets `1B73:030F` |
| `+12` | `code` | 16-bit event payload word passed first to the callback |
| `+14` | `xE` | 16-bit event payload word passed second to the callback |
| `+16` | `event_mask` | 16-bit bit mask tested against the packed mouse event word |

The rectangle comparisons are signed (`jl`/`jg`) and inclusive on all four edges. `m1FD2.c`'s `struct Event` names the payload words `code` and `xE` (`30-39`). `f_1B73_030F` takes those two words followed by event, x, and y, passes them to `f_1B73_036E`, and returns zero (`m1B73.asm:566-578, 624-687`). The enqueue routine stores them as `code` and `xE` in the event record. `f_1B73_0A89` also compares the list API's key with word `+0x0C`, so `code` doubles as the record key for remove/query calls. The list walker tests the callback's AX result; zero stops this list scan, matching `030F`'s return.

The mouse hook packs the incoming callback registers into the tested word: it moves incoming AL into AH and incoming BL into AL (`m1B73.asm:734-784`). The hook is installed with CX=`0x7F` (`481-523`). Thus `event_mask` is a packed 16-bit filter, not a timer field. This record's mask is `0x0601`: low-byte bit 0 and high-byte bits 1 and 2 are selected. The exact test is `(event_mask & packed_event_word) != 0`; it is an any-bit match. The candidate's callback payload is `code=0, xE=0`.

The decoded initializer is therefore a whole nine-word record: rectangle `{0,0,639,16}`, callback `f_1B73_030F`, payload `{0,0}`, mask `0x0601`. No padding or unexplained byte is needed. A descriptive source-only model could be:

```c
struct HotBox {
    struct Rect r;
    int (far *fn)(int code, int xE, int what, int h, int v);
    int code;
    int xE;
    unsigned int event_mask;
};

static struct HotBox candidate = {
    { 0, 0, 639, 16 }, f_1B73_030F, 0, 0, 0x0601u
};
```

`HotBox` and `candidate` are descriptive proposal names, not recovered historical identifiers. Signed coordinates follow the walker branches and `Rect`; payload signedness is represented as `int` by the matching `Event` type, although these routines copy/test the 16-bit representation. The mask's signedness is operationally immaterial to `test`, and `unsigned int` describes its bit-mask role. The exact 16-bit width is proved by the word access.

`src/root/m1FD2.c` calls the same bytes `struct Timer`, but its 18-byte instances are consumed by the same list API. In particular `g_603A` has the identical rectangle and callback, zero payload, and a different mask (`0x1F00` when its final two initializer bytes are read as one word); `f_1FD2_044F` copies it into list `fd_5071_0060` (`m1FD2.c:15-23, 55, 248-256`). This is strong evidence for a duplicated event-region record and shows why the C `Timer` spelling must not be treated as semantic proof. It does not make the two addresses aliases or identify the 60B0 record's use.

## Pointer and neighboring-object review

`_g_5484` describes the first three far lists and `_g_549A` points at `fd_5071_0728` (`m1B73.asm:122-149`). The event dispatcher walks the descriptor lists; the cursor/hot-box paths also call the same record walker over the 0728 list (`327-339, 1800-1879`). The add/append and remove/query APIs accept generic far record pointers. The current source calls pass only named objects: `&g_6016` to 0728, `&g_6004` to 03C4, and `&g_603A` to 0060 (`m1FD2.c:198-225, 230-256`). The `fn` argument to the 6016 wrapper is dynamic, but its record pointer is still `&g_6016`; it does not create an alias to 60B0. Source-wide search found no numeric 60B0/60BA operand and no call passing this candidate. The 60B0 record is not itself one of the far list arrays.

The approved original reference scan reports no direct DGROUP operand or immediate-address candidate for `60B0..60C1` across its 1,730 game functions. The independent full-image relocation review records zero relocated far pointers targeting that interval. Its one relocation is **outgoing** from `+10`, to callback segment `1B73`; it does not establish an inbound pointer. Those scans exclude static references in their stated scopes, not computed pointers or unowned callers.

Neighboring DGROUP placements are distinct and non-overlapping: root `1FD2` `_DATA` ends at `6089`, S10 `m35F5` occupies `608A..60AF`, this 18-byte span is `60B0..60C1`, and S20 `m39F1` begins at `60C2` (`work/data/s27_map.json`). `g_603A` at `603A..604B` is not an alias: it is elsewhere and its mask differs. Adjacency and the exact 18-byte stride support a complete record shape, but do not identify which original object emitted it or whether it was a standalone global versus an element of a larger contribution.

## Disposition and exact remaining gap

Answer: semantic type and initializer, yes; source-instance owner and live registration path, no. Reclassify the semantic shape as an **unregistered hot-box/event record with a real callback relocation**. The object has a concrete functional meaning, and every field can be represented naturally. Do not call it harmless or dead: the evidence does not show whether an unowned caller or computed pointer ever passes its address to `0AC3`/`0B00`, or otherwise exposes it to a walker. The missing proof is the producer/use chain for the first far-pointer argument to the generic registration routines (and any equivalent computed alias), plus the historical `_DATA` object boundary/owner. Until that is found, keep reachability and historical ownership unresolved and do not attach this record to `root:1FD2`, S10, or S20 based on shape/adjacency.

No search/probe/promotion was run; this review does not propose a codegen claim or a byte admission.

## Evidence pins

All SHA-256 values are for the exact files read for this review.

- `src/root/m1B73.asm`: `3097a6b03ff1d8bdfa7d573632d9905de88d754c8b1e047de4014c4f186cb848`
- `src/root/m1FD2.c`: `f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8`
- `src/S10/m35F5.c`: `69be1d6a9649e99102131c702e1920b6e84acc0c1b4cd737d2a047552f917ed5`
- `src/S20/m39F1.c`: `6fd0a02991a29325f214049a8a8961aaee4bc65fbf760b296e63a6ac8f6fbe7b`
- `work/data/s27_map.json`: `1567460fb893a26016e7b89feaed5454e505aeca0579635d0945be391e91fa40`
- `work/takeover/behavioral-oracle/data-debt-disposition-approved-v1.json`: `44ec036b5c7d5f0c98ba03ca8a4b7b96032d3dcabb1c2e6e63459a9ca67240c3`
- `work/takeover/behavioral-oracle/debt-audit/reference-scan.json`: `c395daab89fccd0d0c8220e9dcc5e32bf6a677209712f72b0f73dd959de7fbf2`
- `work/takeover/behavioral-oracle/debt-audit/code-span-followup.md`: `d1ebe2206b6a584e2b0dd3f50d40eeb4ddc11603ea1937f3cf03cb904b107abe`
- `layout/manifest.json`: `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`
- `layout/symbols.json`: `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`
