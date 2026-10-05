# Parent review: source-owned code addresses

The active proof replaces the former S03-only packet. Published checkpoints and
previous receipts remain in Git. Current reproduction reads only canonical source;
no old worker source, generator or Git checkout is an input.

## Promoted callback relationships

Twelve drawing wrappers push their own code segment and the entry offset of the
same drawing body selected by their original conditional branch. The exact
rectangle clipper `f_1D8E_0384` invokes these callbacks synchronously for each
clipped piece. Both words must follow the linked code owner.

| Whole module | Callback replacements | Whole claims verified | Code bytes | Private data bytes |
|---|---:|---:|---:|---:|
| S00:31AD | 5 | 44 | 10,927 | 0 |
| S01:3126 | 1 | 40 | 5,770 | 132 |
| S02:3126 | 3 | 27 | 2,409 | 114 |
| S03:3126 | 3 | 33 including linebuf | 4,824 | 250 |

Parent verification independently reproduced all twelve source substitutions,
checked that each existing conditional branch names the exact callback target,
and compiled all four complete drafts against every historical claim and private
data placement. Normal `promote.py --verify-only` and promotion then passed.
The source edits only replace `mov ax, literal` with `mov ax, OFFSET label`.
All existing ordered fixups, declarations, public order, lengths and other bytes
remain identical; twelve ordinary offset fixups are added. No new label, storage,
procedure or source padding was introduced.

Eight targets have existing PUBDEFs. Four existing internal branch labels are
anchored at their wrapper PUBDEF plus 24 bytes. The inventory guards both these
anchors and each offset fixup at wrapper+12, plus its existing own-segment base16
fixup at wrapper+8. A one-byte code-entry extent in this metadata identifies the
entry address; it does not define or allocate an object. Complete historical
function/extent checks remain separate and unchanged.

S00's historical contribution starts at frame offset 4. Its symbolic targets
naturally acquire that origin through linking. The complete second S00 object
retains the same SEGDEF and follows with one zero alignment byte. S00's existing
cross-function relocation-order debt for `_f_1B4E_015B` remains explicit; this
promotion does not close it.

## Independent placement and negative controls

The installed runner was independently replayed by the parent from current
canonical source into `build/owned-code-addresses-current/`. It assembles all five
primary whole TUs and S00's unchanged second object. The twelve previous linebuf
and xlat_tabs LEAs share this proof with the twelve new callback offsets.
Both real RTLink versions and DOSBox-X pass all twelve expected fixture outcomes:

- Historical origins: all 24 old and current references pass.
- Zero origins: old literals fail eight LEAs and five callbacks; current passes.
- Moved origins: all 24 old literals fail; all 24 current references pass.

Maps independently identify the actual target publics and S00 concatenation.
The DOS checker reads linked operands and compares both callback words with the
actual target. Every callback segment field retains its MZ relocation. Complete
MZ relocation lists/order and all other linked image bytes are identical across
each old/current pair. No game procedure or test provider executes.

Repository controls additionally show that literal whole-TU negatives still pass
historical matching but fail the owned-reference contract. Wrong target anchors
and a wrong paired segment frame are rejected. This is proof of these 24 address
relationships, not external storage ownership, a complete numeric/frame audit,
a standalone DOS game link, game execution or human acceptance.
