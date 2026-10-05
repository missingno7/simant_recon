# LZSS private-state frames

Canonical `src/root/m1B05.asm` now declares SS:DGROUP for the region in which DS
holds input or ring-buffer segments, then restores the assembler assumptions
when the saved DS is popped. The directive supplies linker framing; actual SS
comes from the accepted CRT and preserved caller/interrupt stack relationships.

Fourteen private-state offset fixups formerly used `_DATA` as their frame.
Historical binding still reproduced the original bytes, but independently linked
SS accesses require offsets from DGROUP. The correction changes only those
fourteen frame identities among 61 ordered fixups. All raw segment bytes,
publics, groups, declarations, other fixups and their order remain identical.
All six claims, complete 557-byte code extent, 288-byte private data and 4113-byte
ring storage remain exact. Root independently checked both whole TUs.

The canonical inventory requires every corrected site. Promotion, historical
validation and DOS preflight reject the previous frames, missing references,
wrong targets/displacements and altered bindings. Four tests retain the important
negative: the former source passes historical equality and fails the independent
frame contract.

`replay.py` reads the current canonical whole source, derives its former-frame
negative, and links both with stock CRT and test-owned data. Both RTLink 4.00 and
6.10 pass the 14actual operands with 16- and 80-byte preceding contributions.
DOSBox-X establishes DS=SS=DGROUP and the positive decoder produces `AAAAA`
from one literal and a propagating backreference. All four negatives fail all 14
operands before decoder execution. Paired MZ relocation order/set and every
other linked byte remain equal. No original game executable or resource is a
fixture build input. This is a bounded decoder/frame proof, not full game startup.

```powershell
python evidence/canonical/lzss-data-frame/replay.py --out build/scratch/lzss-frame-proof
```

`receipt.json` records the current canonical replay. `root-independent.json`
records the separate whole-TU comparison and site contract. The broader bounded
ASM disposition is in `../asm-address-audit/`; computed owners, capacities and
returning-Punt effects retain their own open gates.
