# 316-byte unresolved-code reconciliation

Read-only classification against the frozen-at-audit input pins in the
behavioral inventory and current `build/link/provenance.json`. No extents,
claims, or provenance labels were changed.

## Reconciliation

The 316 bytes outside the 29 known open function extents split exactly as:

| Source of residual | Bytes | Classification |
|---|---:|---|
| `debt:game_code` / `debt:overlay_code` not covered by any known function extent | 54 | Unowned code spans; six root spans and one S04 span have no direct entry from catalogued functions. |
| `LINK_FILL` inside counted root/overlay game-code regions | 246 | Linker gap bytes classified by the current placement model as fill. They are not game-function bodies, though their historical linker mechanism is separate proof debt. |
| `debt:text_prefix16` | 16 | Zero bytes before the root text contribution; candidate null-area prefix, not proven filler by the current evidence. |
| **Total** | **316** | Matches `inventory.json`. |

The 54 code bytes are these exact file/linear spans:

| Unit | File range | Code linear range | Bytes | Finding |
|---|---|---|---|---|
| root | `012611..012612` | `0EC11..0EC12` | `00` | Between `LessonDone` and `CompactListA`; no direct known-code branch/call enters it. Zero byte alone does not prove padding. |
| root | `0206BE..0206C6` | `1CCBE..1CCC6` | `0E E8 EE F9 B8 01 00 CB` | Executable-looking far-call stub ending in `retf`; no direct known-code branch/call enters it. Possible indirect/unowned helper. |
| root | `021F78..021F79` | `1E578..1E579` | `CB` | Lone `retf`; no direct known-code branch/call enters it. The raw bytes are not enough to assign it as a tail. |
| root | `022E20..022E29` | `1F420..1F429` | `0E E8 F6 FE 0E E8 AA F4 CB` | Two `push cs; call near` sequences followed by `retf`; no direct known-code branch/call enters it. Possible indirect/unowned helper. |
| root | `02785E..027860` | `23E5E..23E60` | `CB 00` | Immediately after `win_LockWin` and before `f_23E6_0000`; no direct target into the gap. Could be an omitted terminal/shared return plus a byte, but the extent evidence does not decide. |
| root | `02BFD7..02BFD8` | `285D7..285D8` | `CB` | Immediately after `StopSong` and before `f_284A_0138`; no direct target into the gap. A possible missing terminal/shared return remains unproven. |
| S04 | `03F730..03F750` | `368D0..368F0` | 32 | First 24 bytes are executable-shaped and end in two `retf`; final 8 bytes are zero. No direct same-unit known-function branch/call enters this span. See below. |

The S04 stream is `xor ax,ax; lcall 29F4:02CC; cmp [2338],0; je; push cs; call; retf; push cs; call; retf; 8 zero bytes`. A first cross-unit branch scan appeared to find incoming references, but those targets were ordinary intra-function branches in other overlay units: overlay units reuse/alias segment frames, so comparing their linear addresses to S04's file location is invalid. The corrected scan compares near-branch targets in their originating unit and finds no direct branch/call entry into the S04 span. This is **unowned code-shaped historical content**, not established live game behavior. No inference that it is dead, padding, or semantically irrelevant follows from the lack of direct catalogued incoming edges; indirect calls, data-driven entry, or omitted callers remain possible.

The same full-image relocation scan found no relocated far pointer targeting any of the seven unowned code spans. Together with the corrected same-unit branch scan, this establishes no direct branch/call or statically relocated far-pointer entry from the 1,730 known function extents into these gaps. It does not exclude computed pointers or unowned callers.

## Timer-shaped data reachability audit (`55B3:60B0..60C1`)

An exhaustive original MZ/overlay relocation-site scan covered 9,075 loader
relocations (3,683 root plus 5,392 across sections). At every site, the
preceding word was inspected as the offset half of a far pointer. There were
zero pointers whose offset targeted `60B0..60C1`, and zero whose offset landed
in the wider neighboring timer-state window `5FF0..60D0`.

The 1,730 catalogued function extents were independently decoded for direct
DGROUP operands. The only references in `5FF0..60D0` are to known timer
manager words at `5FF0..5FFE`, known timer records at `6004..6046`, menu state
at `604C..6056`, and S10 state at `608A`; none access `60B0..60C1`. The fixed
immediate/address operand scan also found no reference into `60B0..60C1`.
The prior bounded scan's limitation remains: these checks do not prove the
absence of arbitrary computed pointers or an unowned caller.

The neighboring timer machinery does not establish traversal through this
record. `src/root/m1FD2.c` declares and registers five explicit 18-byte Timer
objects at `5FF2`, `6004`, `6016`, `6028`, and `603A`; they end at `604C`, where
other globals begin. The registration wrappers pass only `g_6016`, `g_6004`,
and `g_603A` to `1B73:0B00`/`0AC3`. The timer slot arrays are the distinct far
objects `5071:0060`, `5071:03C4`, and `5071:0728`; `1B73` copies nine words
between those slot arrays and the explicit Timer argument. No source or
symbol path connects those objects to `60B0`. The table/relocation scan found
no statically linked Timer pointer to the candidate.

Thus the bytes remain an **unreferenced relocated Timer-compatible record**:
the callback relocation at `60BA` is real, but an owner, registration path,
and runtime reachability are not established. This is not grounds to call it
harmless or omit it from historical debt. Its need in the portable semantic
core is unproven; a freeze reviewer should require either an owner/use chain
or an explicit unresolved historical artifact plus evidence that the frozen
game-code/call graph has no path to it.

## Freeze implication

The fill/prefix categories are layout questions, not evidence of extra game
functions, but remain separate from the known-function byte count. The 54
unowned bytes include several code-shaped returns/stubs whose no-direct-reference finding
does not exclude function-pointer calls or unowned call sites. Do not convert
any of these gaps into padding, shrink adjacent extents, or claim zero semantic debt
without additional evidence.
