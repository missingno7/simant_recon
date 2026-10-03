# Candidate local SS frame receipt

**Status:** review evidence only; no source admission or historical-image claim. Regenerate the ignored candidate with `python work/source-only-dos/driver-local-frame-probe.py`.

The runner starts from the pinned `source-bindings-v1.json` (`c7fed5e7…f52bc4`), applies the pinned root-reviewed `driver-ss-frame-bindings-v1.json` (`c3820edb…a46f24`), and only then adds these ten local scopes. It regenerates the SS/static source audit from tracked inputs; no ignored audit report/object or original executable is a prerequisite. Its generated machine receipt and full controls are under `build/workers/dos_driver_local_frames/`.

The fresh SS receipt establishes CRT `SS=DGROUP` before the far call to `main`; all four normal driver TUs are far-entry and contain no `MOV SS`, `POP SS`, or `LSS`, so their CFG paths preserve inherited SS. The source scan covers 127 canonical files, 29 registered behavior whole-module sources, and corrected DrawBalloons as a separate module; 25 inline-ASM constructs contain no SS setter. Display callback/interrupt paths switch to DGROUP before dispatch and restore interrupted SS:SP. The timer sound ISR’s saved stack selector is initialized to DGROUP and its stack storage is in `_DATA`/DGROUP.

| Module/source line | Existing instruction | OMF site | Local label | `_DATA` offset/extent | Existing fixup |
| --- | --- | --- | --- | --- | --- |
| S01:3126 / 793 | `mov byte ptr ss:_g_2118, bh` | `S01A_TEXT:05AD` | `_g_2118` | `0000h / 1` | OFFSET16, SEGDEF `_DATA`, displacement `0000h`, addend `0000h`, frame `_DATA` |
| S01:3126 / 853 | `mov bh, byte ptr ss:_g_2118` | `S01A_TEXT:063B` | `_g_2118` | `0000h / 1` | same |
| S03:3126 / 1568 | `mov word ptr ss:_g_222C, ax` | `S03A_TEXT:0DD4` | `_g_222C` | `001Eh / 10` | OFFSET16, SEGDEF `_DATA`, displacement `001Eh`, addend `0000h`, frame `_DATA` |
| S03:3126 / 1574 | `mov cx, word ptr ss:_g_222A` | `S03A_TEXT:0DE1` | `_g_222A` | `001Ch / 2` | OFFSET16, SEGDEF `_DATA`, displacement `001Ch`, addend `0000h`, frame `_DATA` |
| S03:3126 / 1619 | `add si, word ptr ss:_g_222C` | `S03A_TEXT:0E48` | `_g_222C` | `001Eh / 10` | same as `_g_222C` |
| S03:3126 / 1699 | `mov cx, word ptr ss:_g_222A` | `S03A_TEXT:0EF4` | `_g_222A` | `001Ch / 2` | same as `_g_222A` |
| S03:3126 / 1744 | `add si, word ptr ss:_g_222C` | `S03A_TEXT:0F5B` | `_g_222C` | `001Eh / 10` | same as `_g_222C` |
| S03:3126 / 1833 | `and al, byte ptr ss:_g_22E4` | `S03A_TEXT:100E` | `_g_22E4` | `00D6h / 4` | OFFSET16, SEGDEF `_DATA`, displacement `00D6h`, addend `0000h`, frame `_DATA` |
| S03:3126 / 1845 | `and al, byte ptr ss:_g_22E4` | `S03A_TEXT:1029` | `_g_22E4` | `00D6h / 4` | same as `_g_22E4` |
| S03:3126 / 1857 | `and al, byte ptr ss:_g_22E4` | `S03A_TEXT:1044` | `_g_22E4` | `00D6h / 4` | same as `_g_22E4` |

Each label is a private source-local `_DATA` label, not an OMF PUBDEF. The source declarations and next-label bounds close their extents; the local references target the `_DATA` SEGDEF with displacement exactly equal to the label offset. Candidate edits scope `ASSUME SS:DGROUP` to each instruction and restore `ASSUME SS:NOTHING` immediately.

The site tuple hash for `[module, segment, offset, target]` is `b8e422bd4d87100f070a7f228c8ee2e54b502f38835aff590bfb2267b6fcf5eb`. Fresh whole-module controls preserve segment bytes/extents, definitions, publics, groups, externals, and ordered fixup identities across the existing 128-site packet and the added ten local frame-only changes.

The test-owned shifted-DGROUP fixture places a 16-byte prefix before `_DATA`. Both RTLink 4.00 and 6.10 map `_DATA` at group offset `0132h` but normalize its segment frame to `0130h` (2-byte skew). Under canonical `_DATA` frames the fixture reads decoys and reports `FAIL` (`A5 AA BB CC DD EE 00`); under DGROUP frames it reads its owned values and reports `PASS` (`34 78 56 BC 9A DE 00`). The wrapper verifies `DS=SS=DGROUP` before the operands in each run.

`_g_5A9C` remains a separate unresolved SEG/OFF gate: external-owner segment/extent and group membership, plus the receiving ES:offset path, are not established by this local family. The three `S00 SS:[SI+41D0h]` numeric literals remain outside this candidate.
