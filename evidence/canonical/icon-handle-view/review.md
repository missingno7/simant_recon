# Minimum mutable icon Handle slot

Canonical source owns one four-byte mutable slot, `fd_50F6_46D2`, with the
declaration `char far * far * far`. This admits the minimum source view required
by the original consumers. It does not recover a historical maximal allocation,
defining translation unit, master cell, bitmap, producer or lifetime.

Original `f_208F_027F` and `f_208F_02F0` load both words of the slot with `LES`,
then read a far pointer from the designated cell. Their payload arithmetic uses
byte stride `n << 5`. The original loaded slot contains four zero bytes with no
overlapping relocation. This is an initial representation, not permanent zero
or permission to dereference null.

The replay compiles current whole root:208F under its pinned profile. All 24
claims, private contributions, ordered fixups and the complete 1,415-byte extent
pass. Raw far-payload and near-cell contrasts fail only the two consumers and
shorten each by three and two bytes respectively. A word-payload contrast changes
one shift operand in each consumer. A one-element array spelling is an explicit
nondiscriminator: it reproduces the complete live OMF contribution. The evidence
therefore admits a slot view, not the original declaration spelling or capacity.

The canonical storage TU passes its inventory contract: one four-byte FAR COMDEF,
no material data, code, imports, publics or fixups. Raw-pointer storage has the
same OMF shape; near-cell and two-slot contrasts allocate two and eight bytes.
The consumer contrasts, rather than storage size alone, establish the typed view.

Eight stock-CRT fixtures run under RTLink 4.00 and 6.10 in DOSBox-X. Test-owned
cells and byte buffers verify initial zero, pointer-cell repointing, byte stride,
word ordering and raw zero reset. Prepending a real test contribution moves the
mapped slot while preserving these checks. Both typed placements have four
unrelocated on-disk zero bytes. Raw-pointer negatives distinguish the missing
indirection. An initialized-pointer negative retains its real pointer fixup and
fails the zero check before dereference. These are source-built test executables;
they neither link nor execute original game bytes.

No known nominal producer or ordinary incoming consumer edge is established.
That does not exclude computed writes, indirect activation or control-corrupted
continuations. Original menu-width indices 11/12 and x-position indices 21/22
intersect the slot's low/high words. Menu capacity and these physical effects
remain unresolved under independent placement. The cursor Handles are separate
objects and supply no icon referent.

The provider creates neither referent. The subsequent
[default VGA lifetime proof](vga-review.md) resolves the two icon gates in the
existing supported domain: mode 8 bypasses both pointer loads even if either
helper is activated. It does not admit deadness, safe-null, padding or a bitmap
lifetime in other modes. Native conversion widens this canonical pointer and
removes the former duplicate definition from the platform layer.

Reproduce with a fresh output directory strictly below repository `build/`:

```powershell
python evidence/canonical/icon-handle-view/replay.py --out build/scratch/icon-handle-view
```

The runner pins its current canonical sources, inventory, manifest, validation
inputs, tools, libraries and fixtures before execution, then rechecks them.
`receipt.json` records the independently rerun parent result. The separate
`publication.json` records sole-writer admission of the whole canonical program;
it is not an independent DOS game link or runtime claim.
