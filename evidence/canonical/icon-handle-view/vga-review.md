# Icon pointer-load exclusion in the default VGA lifetime

The existing `shipped-default-vga-successful-lifetime` domain excludes both icon
slot dereferences. This resolves `icon-handle-computed-alias-and-activation` and
`icon-handle-cell-and-payload-lifetime` in that domain, and the matching native
limitation. It admits no bitmap, master cell, maximal slot extent, dead helper,
permanent null value or behavior in another display mode. Canonical C is unchanged.

## Lifetime invariant

The [database lifetime proof](../database-domain/review.md) already fixes the
locked resources, one ordinary main lifetime, empty launch arguments, successful
resource operations and no alternate setup or external language/display package.
`ReadConfig`, called by `IBMInitStuff` before argument parsing, reads `V` from the
locked SIMANT.CFG and stores 8 in `g_5A97`. Empty arguments exclude `/d` changes.
The adapter selector in root:205F changes the global only for incoming -1 or
the compatibility flag `g_6298`; its case-1 rewrite is also inapplicable to 8.
The latter flag is initialized to zero and has no subsequent source writer or
address escape. Thus the selector preserves mode 8.

The complete current C/ASM inventory and alias census contains 139 relevant
identifier occurrences across 24 source files. All mode writers are in those
startup/configuration functions. No address escape or later configuration caller
is present. The sole assembly mode reference is a comparison. Existing startup
caller/loop closure excludes reentry; the new census includes `ReadConfig`
explicitly. Whole-file reviewed pins preserve the conditions surrounding every
reference, including changes that retain the same identifier counts. Inventory
discovery detects added files, and aliases are resolved through chains and
physical offsets into the protected state. Aggregate pins bind every canonical
source, module context, program alias and symbol-registry entry, including TUs
with no protected identifier. A synthetic numeric-address write with an updated
inventory hash is a rejected negative control; future unsymbolized ingress
therefore also requires fresh review. The 307 original SaveRec descriptors
match canonical source and intersect neither mode, compatibility flag nor icon
slot. Ordinary save/load therefore cannot rewrite them.

This induction uses valid nominal game/save state, as the published domain does.
It is not an immunity claim for arbitrary overwrites, forged control flow,
returning failure continuations or unproved whole-game memory safety.

## Consumer consequence and controls

In `f_208F_027F`, mode 8 clears both tested bits (1 and 2); in `f_208F_02F0`, it
clears bit 1 and differs from modes 6 and 2. Both therefore call `g_917C` without
reading `fd_50F6_46D2`. This holds for every selector value and even if a caller
activates either helper indirectly. Slot contents and historical menu overlap
cannot affect that excluded read. It does not resolve arbitrary renderer
arguments or the independent window/graphics gates.

Twenty-four original-instruction prefix controls cover both helpers, modes 8
and 2, selectors 0/1/65535, and null versus test-owned nonnull slot contents.
Every VGA control performs zero slot reads and selects `g_917C`; each mode-2
contrast reads both slot words and selects `g_914C`. The rectangle query is an
explicit callback fixture. Execution stops at renderer entry: no renderer,
full helper return ABI or gameplay result is claimed by this probe.

`tests/test_icon_vga_domain.py` also rejects new C/ASM writers, address escapes,
configuration callers, macro escapes, alias chains/interior offsets, changed
startup conditions, overlapping save records and a non-VGA configuration. The
probe compares with reviewed `vga-facts.json`; it never refreshes acceptance
facts automatically. Run `python evidence/canonical/icon-handle-view/vga_probe.py`
and `python -m unittest discover -s tests -p test_icon_vga_domain.py`.

## Integration and retirement

The program inventory moves the two gates to resolved domain contracts through
`promote.py`, preserving their original conditional findings. The graph replaces
the speculative menu/window/sound prerequisites with the existing default-startup
proof. The native limitation and unused platform icon declaration are removed;
the canonical slot and mechanical native pointer widening remain. Exploratory
packets are retired with `tools/workspace.py`. Other display modes still need a
separate producer/lifetime proof before this contract could cover them.
