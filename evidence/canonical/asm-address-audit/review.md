# Bounded current ASM literal/frame gate review

This review found and proved one missing binding: the fourteen private LZSS
decoder SS operands required DGROUP frames. Parent has promoted the natural
two-directive scope and published mandatory OMF guards. No further genuine
direct literal or named frame binding blocker was identified in the reviewed
current 29 ASM TUs. This is a bounded static relationship review, not a proof of
all whole-program integer, pointer, input, or memory domains.

The recommended gate disposition is to discharge
`remaining-assembly-address-audit` for the direct numeric and named frame
relationships in the current 29 ASM TUs under the accepted DOS/ISA/ABI contracts.
Monochrome ownership/extent, computed cross-owner effects, and source-triggered
returning-Punt relationships remain separately gated. This review supplies no
additional distinct unknown direct constant or named frame relationship to keep
as a generic blocker. Parent decides admission and gate wording; this worker
made no canonical or tooling writes.

## Evidence and limits of static completeness

The original lexical census lists 104 hits in six categories. Every listed hit
has been classified using the actual procedure or its callee, not its numeric
spelling alone. `classified-census.json` records those classifications and
corrects the register-tracking false positives below. The census excludes
computed addresses and cannot prove completeness by absence. The positive
review also covers named SS table consumers, current SS writers, code-offset
frame consumers, service-returned pointers, and the whole LZSS TU.

`current29_omf_frame_receipt.json` pins and parses complete current objects. All
29 source hashes match program inventory; after promotion there are no
segment-framed `_DATA` offset16 or group-framed own-CODE offset16 candidates.
That result is supplementary corroboration of two frame classes, not the basis
for clearing other address or execution domains. Existing 24 owned-code
references and their moved-link tests were read and retained without repeating
or expanding their byte proof.

The archived v35 numeric audit and the SS/local/code/ES frame contracts were
read from Git `a1938e6`. Source names once used for numeric SS candidates now
have symbolic owners. Their established runtime frames remain relevant; their
ownership does not establish unlimited indexed access. The old source
generators were not restored or executed.

## Direct constants and service relationships

| Actual relationship | Positive classification and authority |
|---|---|
| ES=0; 0417, 0449, 044A, 0463, 046C/046E, 0487 | Physical BDA bytes/words. The enclosing source establishes ES=0 before use. |
| ES=0040; 17, 1A/1C, 6C | The equivalent BDA frame, explicitly loaded before keyboard/tick/ring-head operations. |
| ES=0; CC/CE, 24/26, 8C/8E, 20/22 | IVT entries for INT33, INT09, INT23, INT08; source vector save/install/restore operations establish the frame. |
| S21 ES=F000 scan | ROM signature scan; SCASB and ES:DI comparison consume an explicitly selected physical ROM frame. |
| `_g_3DB0` A000/B000/B800; direct B000/B800 stores | Video ABI frames selected in source; no game source owner is implied. root:1F66 B000:0040 is its error marker. |
| Eight `_f_1B4E_015B` call literals | BIOS mode words 3, 0D, 10, 12, 13, 3, 9, 3. Callee loads its word parameter into AX and invokes INT10. |
| S01 40, S02 FFFF, S03 F rectangle-call words | Scalar drawing parameter consumed from BP+0E; the calls do not construct far addresses from these words. |
| S21 CX=4 around indirect test call | Preserved loop counter over four source-owned test records, not a numeric call pointer or argument. |
| LZSS `_open` 8000 | Scalar binary-open flag; the adjacent filename pointer comes from ES:BX. |
| Mouse FF0F through `_g_9128` | Scalar drawing/attribute parameter alongside two zero scalar parameters; the existing dispatch table supplies the far function identity. |
| Nine initializer hits | Null storage for runtime pointers/vector/stack fields, except the A000 video initializer. Reads/writes establish their later source/service/input provenance. Zero is not an invented absolute object. |
| EMS page-frame offset zero | The matching segment comes from INT67/AH41 BX. It is the service page-frame offset, not a linked source offset. |
| INT21/AH52 `[ES:BX+20]` | Field relative to the DOS-returned pointer; no fixed game frame. |
| `__psp`, command-tail 80 | Service process frame and its ABI command-tail field. |
| root:194D Tandy probe | Segment derived from `_g_91A2+_g_91A0-400h` paragraphs; hardware/top-of-memory arithmetic, not a source contribution origin. The checksum's segment-3 and SI+2 are a caller-relative header relationship. |

Two important corrections prevent incorrect conclusions from the census:

* root:1F66 does not load literal A3A5 into DS or ES. AX is rotated six times
  before MOV DS,AX and once more before MOV ES,AX. These are register-test
  patterns, never dereferenced on that path. The normal branch restores both
  registers. The failure branch explicitly selects B000 and invokes INT23;
  this register-test failure is not an established ordinary source/input path.
* Mouse `_f_1B73_0747` ES=0 at line 1139 is an event record segment field passed
  to `_f_1B73_036E`, which stores ES at record+0E without dereferencing it.
  That callee independently selects ES=40 before its BDA reads. ES=0 at line
  1111 is unused on its shift-state branch; line 1152 does select physical BDA.
  Zero alone was insufficient to call all three assignments a BIOS frame.

## Runtime frame authority

`ASSUME` controls OMF frame selection and supplies no runtime register proof.
The accepted stock CRT establishes SS=DGROUP before main. The current source
setter inventory has exactly twelve SS writes, in root:1B73 and root:28BC.
The mouse/keyboard dispatch routes load DGROUP before their private stack
switches; interrupt epilogues restore the interrupted SS. Timer private-stack
routes retain their save/restore authority. Archived SS contracts include
instruction-CFG dominance for the display-dispatch paths and both-linker
shifted/decoy controls for external and local table references. Ordinary C
callers inherit the CRT frame. This proves the named ordinary/dispatch frame
relationships; arbitrary corruption, unrestricted entry states, and global
fatal-state invariance are outside the proof.

The current named display relationships include the symbolic `_g_41D0` pattern
bank, `_g_6778`, `_g_68AC`, `_g_68B4`, `_g_2226`, and local SS tables. SS XLAT
consumers establish their BX table offset before DS becomes the input frame.
Their storage and indexing domains are distinct from the inherited SS frame.

Code-offset authority is also concrete: mouse installer ES:DX is paired with
PUSH CS/POP ES; DOS vector installer DS:DX is paired with PUSH CS/POP DS. Its
fifth near offset is stored for a same-CS near indirect call. The EMS device
name uses PUSH CS/POP DS before its LEA and DOS open. Keyboard atexit pairs a
symbolic code offset with a pushed CS; runtime DS need not equal CS to form
that stack pair. The reviewed mouse ES data-offset scope executes MOV SI,
DGROUP / MOV ES,SI before its three operands. Current clip production pairs
DGROUP with the symbolic DGROUP offset of `_g_5A9C`; the older mixed-frame
hypothesis is no longer the current source.

## LZSS result and reusable proof

The exact change is `ASSUME SS:DGROUP` after DS becomes input/ring and restoring
SS:nothing with DS:DGROUP after POP DS. It changes no instruction, table,
declaration, raw segment byte, ring operand, or source extent. Independent OMF
comparison found exactly fourteen `_DATA`-segment to DGROUP-group frame changes
among 61 ordered fixups; all other fixup fields and order remain equal.

All six procedure peers, LZSS_TEXT 557 bytes, private `_DATA` 288 bytes, and
LZSS_DATA 4113 bytes passed whole-TU search and `promote --verify-only`, with
exact private storage and complete ordered fixups. The initial per-site draft
and natural two-directive draft have identical full object projections.
`guard-proposal.json` supplies public-relative operand rows, target
displacements, exact fixup fields, access roles, and runtime authority.

The reusable whole-source replay links stock CRT and test-owned fixtures with
16- and 80-byte preceding DGROUP contributions using RTLink 4.00 and 6.10.
It independently checks maps/MZ operands and asserts runtime DS=SS=DGROUP.
All four positive cases pass all fourteen operands and a real valid-data
decoder call (one literal followed by a back-reference, yielding five As).
All four old-frame negatives fail all fourteen operand checks before decoder
execution. Paired relocation sets/order and all non-operand image bytes remain
equal. No original game executable/resource input, object patch, fixed origin,
padding, or original-byte build fallback is used.

Parent retained the canonical replay at
`evidence/canonical/lzss-data-frame/replay.py`, replayed the current admitted
source, and owns final tooling/acceptance validation. Worker proof artifacts
remain in this scratch directory.

## Register-test error path: exact scope

In `_f_1F66_0107` the prologue saves ES, DS and six general registers. At source
line 185 AX=A3A5; successive ROR AX,1 values are D1D2, 68E9, B474, 5A3A,
2D1D, 968E, 4B47. SI/DI/BX/CX/DX receive the first five, DS receives 968E
at line 202, and ES receives 4B47 at line 205. AX remains 4B47. L0156 compares
the unchanged original A3A5 stack word with each general/segment test register,
then loops by decrementing stack counters. Under standard x86 semantics and
preserving asynchronous interrupt ABI, every comparison is unequal, and the
normal epilogue restores all saved registers including DS/ES at lines 240/241.
No ordinary input controls a compared test value.

Only a failing comparison enters L019A (line 245), which selects ES=B000,
writes byte B000:0040=21 at line 248, and executes INT23 at line 249. If it
returned, MOV SP,BP / POP BP / RETF would skip the saved-register restores;
DS would retain its test value absent handler changes, ES its selected video
frame. This conditional fact does not manufacture a new layout blocker from a
hypothetical register/CPU/platform failure. The exact branch is retained.

No current direct inbound source call to `_f_1F66_0107` was found. The available
`_f_1F58_00B8` is a generic caller-supplied INT23 vector installer: LES BX from
BP+6, save DX=ES, exchange the two IVT words at ES=0, save the previous vector,
and register `_f_1F58_00A1` with atexit. `_f_1F58_00A1` restores the prior IVT
words and RETFs; it is not the INT23 handler. No current direct inbound call to
that installer was found either. This review did not inspect/admit a default
DOS/CRT INT23 handler termination contract and claims no blanket termination.
Neither indirect activation nor arbitrary corruption is excluded by the
negative inbound scan. The positive ordinary-path ISA/ABI analysis, rather
than termination or lack of callers, is what prevents treating the register
self-test branch as a new direct address/frame defect.

## Still open: precise next relationships

| Relationship | Why this review does not discharge it |
|---|---|
| S01:328E `_g_8ED8` monochrome pattern bank | Four procedures import its byte base, add phase/index terms, and read through SS while DS is input. DGROUP SS authority is established; defining owner and complete indexed extent are not. This is storage/extent work, not another frame correction. |
| `ctype-out-of-range-index-layout` | Signed byte indices can read preceding CRT storage without a direct numeric operand. Full table ownership and correct frame do not preserve the prefix or heap pointer values after independent placement. |
| `sound-selector-out-of-range-layout` | `/s9` can select data as code and later overread setup/cleanup storage. Symbolic table identities do not exclude those computed indices or establish return/effects. |
| `graphics-computed-copy-layout`, `window-index-resource-cross-owner-layout`, menu/critical/icon alias gates | Counts, signed indices, and physical overlaps can cross separately owned objects. This review establishes no whole-program bounds or alias exclusion. |
| Returning-Punt continuations | Existing database/graphics/window gates have actual source triggers and still require return/effect/bounds proofs. Correct direct frames supply no global noreturn or fatal-state invariance. The hardware register self-test above does not supply an additional source-triggered blocker. |

The old root:0093 C GetRRandSeed absolute 046C:0000 read is outside the 29 ASM
scope and must not be misclassified as physical BIOS tick 0000:046C. No claim
about that separate relationship follows here.

No new ownership, widened storage, input clamp, global noreturn assertion, or
arbitrary execution-domain claim is proposed. The task stops at this bounded
result. `receipt.json` records exact inputs, scopes, and proof artifacts.
