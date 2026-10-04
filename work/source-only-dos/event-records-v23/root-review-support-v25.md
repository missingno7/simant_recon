# Event16 root-review support v25

Read-only independent verification of the v24 candidate wrapper and saved v22 final3 artifacts. This is review support only: `root_reviewed=false`, `admitted=false`; no probe or link was rerun.

Overall checks: **PASS**. Verified raw case files: 184; source pins: 156; strict receipts: 29; selected tool/input pins: 23.

| Linker | Case | RUN.LOG exact / marker | LINK.LOG full scan | Name/Value | owner OMF | bases OMF | FAR_BSS bytes |
|---|---|---|---|---|---|---|---:|
| rtlink400 | positive | yes / no | clean | match | match | match | 32 |
| rtlink610 | positive | yes / no | clean | match | match | match | 32 |
| rtlink400 | positive_shifted | yes / no | clean | match | match | match | 64 |
| rtlink610 | positive_shifted | yes / no | clean | match | match | match | 64 |
| rtlink400 | wrong_wide_field | yes / yes | clean | match | match | match | 36 |
| rtlink610 | wrong_wide_field | yes / yes | clean | match | match | match | 36 |
| rtlink400 | wrong_narrow_field | yes / yes | clean | match | match | match | 30 |
| rtlink610 | wrong_narrow_field | yes / yes | clean | match | match | match | 32 |
| rtlink400 | nonzero_initializer | yes / yes | clean | match | match | match | 16 |
| rtlink610 | nonzero_initializer | yes / yes | clean | match | match | match | 16 |
| rtlink400 | base_plus_two | yes / yes | clean | match | match | match | 32 |
| rtlink610 | base_plus_two | yes / yes | clean | match | match | match | 32 |
| rtlink400 | wrong_symbol_base | yes / yes | clean | match | match | match | 32 |
| rtlink610 | wrong_symbol_base | yes / yes | clean | match | match | match | 32 |

The two Event symbols are verified from independent 16-byte FAR commons and each case map's complete `Publics by Name` and `Publics by Value` sections. Extent comes from each OMF allocation, not from inter-symbol spacing. The positive shifted control uses its separate 32-byte PAD common; the 15-byte control preserves RTLink 4.00's 30-byte and RTLink 6.10's 32-byte map aggregate distinction.

The current Event source has eight `int` fields at byte offsets 0, 2, 4, 6, 8, 10, 12, 14; `OWNER.C` defines two separate far Event objects. The pinned dispatcher source and source-audit views point to exact field access and whole-record copy sites. The queue dequeue function loads eight words with `rep movsw` into its far destination. The runtime positive case tests `sizeof`, all field offsets, symbolic current/previous bases, CRT zeroing, the 16-byte whole-record copy, and endpoint canaries; it emits `PASS`.

This storage candidate does not establish `ev->code` stability. The decoder/resource-height frontier remains open: the source review records a signed DEC/JNZ height loop with the actual resource-domain bound unknown and a possible overwrite of the active Event code field. The support result does not treat normal draw-size bounds or uncalled generic routines as closure.

Toolchain scope: MSC 6.00AX `/AL /Os /Gs`, experimental RTLink/Plus 4.00 and 6.10, DOSBox-X, `llibcr.lib` and `libh.lib`, all checked against the recorded pins. Neither linker is asserted to be the historical SimAnt linker.

Machine receipt: `build/workers/dos_event16_root_review_support_v25/root-review-support-v25.json`. Re-run with `python build/workers/dos_event16_root_review_support_v25/review_saved.py`; the script refuses to overwrite its two receipt outputs.
