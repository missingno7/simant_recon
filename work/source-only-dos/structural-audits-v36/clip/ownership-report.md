# Clip Rect destination ownership, v36

Status: **UNRESOLVED; research only; root_reviewed=false.** No owner definition,
admission, production change, promotion, runtime demonstration or Git change is
proposed. All new artifacts are confined to this worker directory.

The missing fact is the defining capacity of `fd_50F6_3C14`. Its only canonical
declaration remains `extern struct Rect far fd_50F6_3C14[]` in
`src/root/m1E57.c:117`. The known eight-byte Rect layout and the buffer's copy
role identify a view, but neither an original array bound nor its owning COMDEF.
The 256-record allocations in the same module belong to different, dynamically
allocated objects. They cannot be transferred to this static destination.

The earlier computed-copy v1/v2 reviews predate the v29 screen-list admission.
`work/source-only-dos/storage-admission-v29/root-admission.md` and the current
`screen-clip-list` provider establish two near Rects with the full sentinel.
Thus the old missing-resident-terminator statement is superseded. This resolves
that particular screen-list fact, while leaving the destination capacity and
the computed-copy layout gate independent.

Ordinary source geometry and ownership are now separated explicitly:

| Source object or operation | Established fact | Does it establish 3C14 capacity? |
|---|---|---|
| Screen list `g_5A9C` | Admitted Rect[2], one screen Rect plus sentinel | No |
| `fd_50F6_3B60` | Admitted 45 four-byte Handles; 180-byte owner | No |
| Rebuilder `f_1E57_038E` | Allocates `tmprects` and `clipout` as 256*8 bytes, then allocates/resizes persistent lists by generated length | No |
| Helper `f_1D8E_003F` | Intersection emits at most one Rect; exclusion emits at most four; terminator is written at the returned endpoint | No |
| `f_1E57_08F5` null-clip route | Its ordinary caller supplies two Rects plus the third-record sentinel | No |
| `f_1E57_0FDC` | One input against the screen yields at most one Rect plus sentinel | No |
| Reset `f_1E57_0009` | Releases `g_5742`, clears active handle/pointer state; it does not define or size 3C14 | No |
| Push/pop | Saves and restores a length found by the `top == 0x8000` sentinel; no destination-capacity argument | No |

The strict-effective rebuilder body, rather than its canonical scaffold,
supports the dynamic-list facts. Its C097/C098/C099 tests precede persistence
of generated results. On ordinary successful branches with nonnegative counts
below 256, at most 255 data Rects plus a sentinel are copied, or 2,048 bytes.
That is a conditional payload bound, not a defining storage extent. The old
Punt candidate and sentinel-copy/layout reachability limitations are not
silently upgraded to closure here. Full standalone integration remains open.

Fresh whole-module MSC 6.00AX controls use the manifest flags
`/AL /Os /Oe /Og /Gs /Zi`, original function order, and the unchanged canonical
scaffold. Only the extern destination dimension changes: unsized, 1, 256, 512.
All four preserve the **entire live OMF contribution**: 4,089 code bytes, 806
DATA bytes, six CONST bytes, 35 publics, 374 ordered fixups, 44 external names
and scopes, and no communals. The destination stays an EXTDEF in every case.
The compiler cannot distinguish those capacities in this consumer's live
output. `extent-controls.json` pins each whole TU, object, complete projection,
compiler log, toolchain and source input. The source-only guard records zero
denied oracle reads; the controls read no original executable.

No further negative address scan was performed. No next-public gap is used.
The remaining declaration/layout fact must come from a defining source/object
with a measured COMDEF, a source operation whose size depends on the actual
array bound, or an independently grounded original owner declaration. A bound
chosen from the largest conditional copy would invent storage information.
Investigation stops at this concrete residual; neither the missing import nor
`graphics-computed-copy-layout` is discharged.
