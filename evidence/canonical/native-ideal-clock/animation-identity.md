# Yard animation identity observation

Owner-approved anim-id-pattern-v1,2026-11-14. This is an observer equivalence
rule, not a change to game state, allocation or animation code. It is enabled
only for the sound-off ideal-v1 check. All participating views remain game_state.

## Use audit before enabling the rule

The recursive source/include symbol census is retained at
`build/workers/ideal-check/identity/uses.json` (audit.py reproduces it).
All references to yardAnimHandle are in yard_window.c, its definition, and
view_dialog_helpers.c:34-41 (remove/render/free the whole set). No holder's
address escapes except the array initialization with _fmemset. No ID arithmetic,
numeric ordering, ID-dependent priority, serialization or comparison other
than equality and the -1 sentinel was found. SaveRec extents were also checked
by address against every holder on both original and canonical layouts, rather
than relying only on symbol-name searches.

The AnimObj/AnimSet and anim_last_added_object census also checks the internal
ID field, not just holders. Its only extra read is the raw debug print in
hanim_PrintSet (anim.c:96-98); there is no caller or address reference to that
routine in the source/include census. Raw diagnostic printing is outside this
gameplay observer equivalence and remains raw. Database-index `->id` ordering
belongs to a different type/resource ID and receives no rule.

`src/graphics/anim.c:180-187` finds an object by equality within the supplied
set. Lines214-217 generate a unique live ID: mask with7fff, increment nextId,
retry while the ID exists. Therefore live IDs are0..32767 and cannot equal-1.
Lines222-225 insert by priority, independently of ID. Lines416-417 preserve the
old identity when reinserting an object. MakeAnimSet leaves nextId untouched
(438-444); the earlier read-only DOS experiment starts the final yard set at4
and1025, producing the measured1021 offset. This is allocator residue.

`src/ui/yard_window.c` holds every ID from yardAnimHandle:

| Holder | Purpose | Complete use sites (declarations excluded) |
|---|---|---|
|g_2A2A|kid|300-303,519,538-540|
|g_2A2C|cat|415-418,522,530-532|
|g_2A2E|bird|384-387,521,552-554|
|g_2A30|dog|357-360,520|
|g_2A32|mower|463-465,486-489,523|
|g_2A34|for-sale sign|433-436,524|
|g_2A3E|kid balloon|306-308,325-328,525,542-544|
|g_2A40|yard message|526,584-586,596-598|
|yard_rain_anim_indices[15]|rain|516,562-564,618-621|
|yard_black_swarm_anim_indices[17]|black swarm|517,662-670|
|yard_red_swarm_anim_indices[17]|red swarm|518,687-695|

Every use stores a returned ID, tests -1, or passes it back to the same set's
move/remove operation. Coordinates, picture IDs, array indices and priorities
have arithmetic; the animation IDs do not. Other animation sets (for example
colony controls) receive no new rule.

The eight scalars were previously excluded because original_layout had no
global symbol for these file-local objects. This round adds them to sound-off
observation. `animation_identity.original_scalars` independently decodes each
holder's own exact original Draw function, checks both a direct word comparison
with-1 and the returned-AX store, and checks its DS offset lies within the
module's proven original _DATA contribution. Canonical addresses come from
CodeView plus link contributions; native addresses come from that executable's
DWARF. No layout inventory or source is edited. All eight extents are two bytes;
SaveRec overlap is rejected during schema extension on either DOS image.

## Pattern contract and raw diagnostics

The explicit11-holder allowlist and reason are in runtime_views.json and
animation_identity.py. For each holder and each entry, traverse its words in
slot order. Preserve-1. Assign each previously unseen live value the next
zero-based ordinal; repeated values get their first ordinal. For example,
`[37,-1,37,900,5,900]` becomes `[0,-1,0,1,2,1]`. Hash those16-bit little-endian
words with the existing FNV1a rule. A scalar thus records absent/present. Invalid
high-bit words other than-1 stay literal and cannot be renamed into a valid ID.
Ordinals restart for each holder on each entry; there is no temporal ID replay.

This is the owner's per-holder identity pattern: it observes sentinel position
and equality classes within each holder. It does not add a cross-holder or
temporal object-graph proof. Set uniqueness and consistent pass-back use are
established by the source audit; checkpoint scanout still compares fully.

Raw .hash and full checkpoint state dumps retain the original words. The new
.hash.ideal-state-v2 stream combines this rule with the unchanged narrow
keyboard-context-v1 projection. DOS .anim-ids and native .hash.anim-ids record
every raw holder word at every entry as `entry view-index word...` in hex.
Lane JSON reports each holder's raw difference count and first actual values,
not merely the hash. Other views use their existing full observation.

Reference receipts pin the view census, helper header, and all three reviewed
source files. References with the old raw-only schema cannot stand in for this
contract. New captures are under build/reference/sound-off-identity; the previous
sound-off references are retained. Test_animation_identity compiles the actual
helper in C and C++, exhausts all five-slot patterns over three identities and
-1, tests bijective renaming, broken-alias and sentinel negatives, invalid-word
preservation, unchanged input bytes, maximum17-slot width and original local
instruction bindings. No tape machinery is retired by this change.
