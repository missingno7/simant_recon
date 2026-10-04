# Event16 source-owned storage probe v22

**Result: PASS, candidate storage only.** This is a source-owned provider/runtime proof for two natural 16-byte FAR objects; it does not establish historical producer module, linker ordering, or original numeric placement.

The probe compiles with MSC 6.00AX `/AL /Os /Gs`, links with pinned RTLink 4.00 and 6.10, and runs under the pinned DOS CRT (`LLIBCR`/`LIBH`). The owner OMF contains exactly two far commons, 16 bytes each, and no initialized bytes or nonzero code/data contributions. The positive runtime checks 16-byte `sizeof`, every offset 0,2,4,6,8,10,12,14, all 32 startup-zero bytes, and a distinctive byte pattern copied through whole-struct assignment with first/last canaries.

| Case | RTLink 4.00 | RTLink 6.10 |
|---|---|---|
| Positive: two Event commons and whole-record copy | PASS; 011C0H 011DFH 00020H FAR_BSS                FAR_BSS | PASS; 011C0H 011DFH 00020H FAR_BSS                FAR_BSS |
| Positive after 32-byte common shifts layout | PASS; 011C0H 011FFH 00040H FAR_BSS                FAR_BSS | PASS; 011C0H 011FFH 00040H FAR_BSS                FAR_BSS |
| Wrong field width: `code` becomes long; Event is 18 bytes, xE +16 | REJECTED: wide code moved xE to +16; Event size is 18; 01190H 011B3H 00024H FAR_BSS                FAR_BSS | REJECTED: wide code moved xE to +16; Event size is 18; 01190H 011B3H 00024H FAR_BSS                FAR_BSS |
| Wrong field width: packed one-byte xE; Event is 15 bytes | REJECTED: narrow xE stays +14; packed Event size is 15; 01190H 011ADH 0001EH FAR_BSS                FAR_BSS | REJECTED: narrow xE stays +14; packed Event size is 15; 01190H 011AFH 00020H FAR_BSS                FAR_BSS |
| Nonzero initializer on previous Event | REJECTED: nonzero initialized Event at CRT entry; 011F0H 011FFH 00010H FAR_BSS                FAR_BSS | REJECTED: nonzero initialized Event at CRT entry; 011F0H 011FFH 00010H FAR_BSS                FAR_BSS |
| Bad base: current pointer +2 | REJECTED: symbolic base mismatch; 011C0H 011DFH 00020H FAR_BSS                FAR_BSS | REJECTED: symbolic base mismatch; 011C0H 011DFH 00020H FAR_BSS                FAR_BSS |
| Bad base: current points at previous Event | REJECTED: symbolic base mismatch; 011C0H 011DFH 00020H FAR_BSS                FAR_BSS | REJECTED: symbolic base mismatch; 011C0H 011DFH 00020H FAR_BSS                FAR_BSS |

The 18-byte and 15-byte controls change actual field width/extent and are rejected by runtime shape checks. Their individual OMF COMDEF lengths are pinned. RTLink 6.10 rounds the pair of 15-byte commons to a 32-byte FAR_BSS aggregate; that aggregate and the start-to-start map offsets are not used as per-object extent evidence. The exact per-object extents come from each OMF common and the runtime `sizeof`/field-offset observations.

The shifted case proves symbolic relocation: the independent 32-byte common moves both Event symbols under both linkers, while the initialized pointer table still resolves to each named object's actual linked base. The plus-two and other-symbol alias controls fail those same identity checks under both linkers.

The source audit pins 127 canonical TUs plus all 29 effective strict sources in `static-completeness/index-v1.json` (156 unique paths). The 23 direct name references are all in `src/root/m218D.c`; there are no exact numeric address aliases in the bounded set. Its eight-word dequeue writes the current record, `fd_50F6_4A0A = fd_50F6_49FA` copies the entire previous record, direct global field uses read `code`/`modifiers`, and only current `modifiers` is written in the dispatcher. The selected current-pointer path passes to `f_218D_0451`, `f_218D_023A`, `f_218D_000C`, then to the matching `f_23E6_0A53`, `win_ProcSliderEvent`, or `o26_39C7_040F` Event16 views. Other local `struct Event` layouts in unrelated TUs are not assumed to view these FAR objects; `win_GetEvent` outputs are caller-local, and the root:1FD2 input queue is a separate 112-byte near `Event[7]` owner.

Registry review leaves both Event names unresolved with zero accepted storage candidates. The only registered starts within the candidate spans are the two names themselves; the next registered start is `fd_50F6_4A1A`. The removed `fd_50F6_4A12` name is an interior alias record, not an independent owner. These registry observations do not supply the extents; the whole-record source operations and per-symbol OMF commons do.

The decoder/resource-height closure is independent and remains open: the resize path can reach `DrawSpider` and the selected S00/S01/S03 decoder, whose destination begins at 50F6:1F2A, 0x2ADC bytes before active `code` at 50F6:4A06. Positive height clamps, but zero/negative signed height still enters the DEC/JNZ row loop; the actual resource-domain bound is unknown, so a conditional event-state overwrite remains possible. No typical draw-size bound is used to exclude it.

Machine-readable source pins, object shapes, maps, runtime logs, tool hashes, and all 14 linker runs are in [receipt-v22.json](receipt-v22.json) and [source-audit.json](source-audit.json). No production or canonical source, layout, registry, journal, or Git state was changed.
