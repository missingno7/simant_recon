# DGROUP 60B0 hot-box investigation

Status: **compatible source experiment; parent reviewed; unaccepted; all 18 functional bytes remain debt**.
No canonical file, inventory, manifest, oracle lock or promotion journal was changed.

## Positive facts

1. Current accepted contributions bound the range on both sides: S10:35F5 `_DATA`
   starts at DGROUP:608A and has 38 bytes, ending at 60B0; S20:39F1 `_DATA`
   starts at 60C2. The intervening 18-byte range has one real far callback
   relocation at +10 to root:1B73:030F. It is neither unrelocated padding nor a
   guessed zero provider.
2. Original/canonical 1B73:0AC3 and 0B00 copy exactly nine words of an input
   argument into their queue. 1B73:0CEF advances by 18, compares the four signed
   rectangle words at +0,+2,+4,+6, tests the word at +16 against AX, and calls the
   far pointer at +8 with five words: +12, +14, AX, CX and DX. It tests callback
   AX afterward. This grounds the **generic** hot-box ABI independently of the
   misleading Timer spelling in m1FD2.c.
3. 1B73:030F reads all five words: its first pair is loaded into ES:BX, the third
   into AX, the fourth/fifth into CX/DX. It calls 036E, which stores BX and ES as
   the event code/extra word, AX as mouse state, and CX/DX as coordinates. 030F
   then returns AX=0. The minimum compatible callback type is therefore
   `int far fn(int code, int extra, unsigned mouse, int x, int y)`; the first
   two words are opaque event payload, not a pointer to dereference.
4. 0445 forms `_g_9120` as button byte | (event byte << 8). The generic hot-box
   match at 0CEF is `mouse_mask & mouse_word`, not a countdown comparison.
   0x0601 consequently selects button bit 0 or event bits 1/2. Source-defined
   records supply a repeated representation: g_603A has the same (0,0,639,16)
   rectangle, 030F callback, zero code and zero extra word, with mask 0x1F00.
   g_6004 uses 0x0A00; g_6016/g_6028 use 0xFF00. Those facts corroborate a hot-box
   interpretation but do not supply initializer provenance for the particular
   0x0601 object.

## Fresh experiments

Run `python evidence/canonical/hotbox-owner/replay.py --out build/hotbox-owner-current`.
The parent independently reran the canonical, trailing typed definition, separate
contribution and front-definition contrast. All seven checks passed. The current
`receipt.json` pins those inputs and records complete code/fixup/public projection
hashes, data checks and symbolic data fixups. No canonical source was promoted.
The broader worker experiment's full projections remain in ignored
`build/workers/hotbox_owner_current/receipt.json`; the extra declaration positions
are compatibility observations, not additional acceptance gates.

| Control | Result |
| --- | --- |
| Canonical S10 whole source | Four accepted exact peers, 38-byte `_DATA`, 10-byte CONST pass |
| Natural anonymous hot-box appended after S10's last function | Full 56-byte `_DATA`, including all 18 descriptor bytes and its symbolic callback fixup, exact; all four peers and CONST exact |
| Appended object with the grounded five-word, int-returning callback type | Same results; **complete 2,718-byte canonical compiled code and all ordered code fixups/publics unchanged**, including the unclaimed semantic menu body; semantic definition hash unchanged |
| Definition immediately before S10's last function | Same data/accepted-peer results, but complete code/fixup projection differs; do not use this as a full-context equivalent |
| Independent static data-only object at 60B0, after S10 | Complete 18-byte `_DATA`, one symbolic pointer32 fixup to 030F, no code or communal, exact; `near_link_after_reasons` empty |
| Same initialized definition at the beginning of current whole S20 | 151-byte `_DATA` fails bytes and relocation set at 60B0; compiler emits the first function's literals ahead of the queued definition (DATA-1) |

The data-only contrast uses `verify_module` as an investigation, not an admitted
historical object. `promote.py` demands independent origin evidence for a new
`data:55B3@60B0` contribution. No such evidence was asserted or invented.

The S10 `promote.py --verify-only` pass checks all four existing claims and both
private data contributions, then correctly refuses the changed registered
semantic declaration context. S10 is currently a partial historical module with
one BEHAVIOR_EXACT function; its full compiled code projection equality does not
establish a new historical complete-TU `--extent` claim.

## Missing fact and disposition

Appending the record to S10 and creating an independent data-only contribution
are both consistent with the same initialized range, symbolic fixup and accepted
neighboring contributions. Therefore contribution order, shape and callback
alone do not distinguish a defining TU. The generic hot-box consumer establishes
what these fields would mean **if** the object were registered, but does not
establish that this particular initialized range is a hot-box object or the
source authority for its mask value. Existing g_603A is a useful analogue, not an
alias or initializer owner for 60B0.

A source-owned computed registration/copy path designating this range, a linked
public/record anchor to its declaration, or independently grounded initializer
provenance would supply the missing positive bridge. No repeat broad no-inbound
scan was made. Absent literal references were not used to claim deadness.

A complete initialized object could in principle be admitted while retaining a
mandatory activation/escaped-alias gate; activation is not automatically a
prerequisite for storage ownership. **This investigation does not yet supply
sufficient independent authority for that admission.** Keep the whole-source
candidate as compatible and unaccepted, retain all 18 bytes as functional debt,
and retain the data-debt link refusal and unresolved activation/computed aliases.
