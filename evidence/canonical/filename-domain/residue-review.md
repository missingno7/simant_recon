# FileSelect capacity: filesystem premises and the uninitialized name

Result: **the gate stays open.** The filesystem part can be scoped by explicit
directory premises; the incoming uninitialized `name` cannot be bounded by any
admitted proof or premise. No source change is justified or made.

## Filesystem part (SUPPORTED_DOMAIN sub-obligation)

Let `L` be the selected drive's current directory length including `X:\`.
FileSelect stores `X:\` plus the AH=47h result in `path[67]`, then appends a
separator. Real MS-DOS keeps at most a 66-character current path (67-byte CDS
field); `L=66` needs 68 bytes after the append, one beyond `path[67]` and the
later `lastDir[67]` copy. FileSelect's own listing descent cannot reach that
depth on valid search results: its `*.*` filespec exceeds the 64-character
pathname limit beyond `L=62`, so descent stops at `L=64`. Only an inherited
66-character directory reaches the overrun. The host-mounted DOSBox-X control
in `review.md` exceeds real-DOS limits and stays a negative control.

A declined OVERWRITE returns to the selector with the previous full path as
`name`; the concatenation needs `L+D+F+3` bytes (`D` the previous directory,
`F` the leaf). For the same directory and an 8.3 leaf this is `2L+15`: 79
bytes at `L=32`, 81 at `L=33` (beyond `buf[80]`), 101 at `L=43` (beyond
`name[100]`). A valid navigable `L=53` witness needs 121 bytes. So directory
lengths of at most 32 characters and valid 8.3 names bound the retry; real
DOS alone does not.

## Incoming uninitialized name (LAYOUT_SENSITIVE)

`LoadGame` and `SaveGame(0)` pass an automatic `char name[100]` that is never
initialized. Before anything else, FileSelect does
`if (*name) { sprintf(buf /*80*/, "%s%s", path, name); _fstrcpy(name, buf); }`
and only later clears `*name` at `redraw:`. Deterministic DOSBox-X runs
(`residue-receipt.json`) captured the string at FileSelect entry on every
ordinary chain in the original and the canonical-only diagnostic build:

| Chain | Original length | Reconstructed length |
| --- | ---: | ---: |
| Save As (keys / mouse menu) | 9 | 11 |
| File menu Load (Don't Save) | 13 | 15 |
| Select-a-Game Load | 15 | 15 |
| Save prompt before Load, Quit save prompt | 0 | 1 |
| Declined-overwrite retry | 8 (`C:\a.ant`) | 8 |

The bytes include DGROUP pointer values and their last writers differ between
builds (display driver, geometry and overlay-manager frames). Visible
behaviour and saved games matched in every run, because these short strings
only feed the discarded concatenation.

No source guarantees a terminator early enough. In an intact caller frame the
first guaranteed zero is LoadGame's `ok` at `name+103` or SaveGame's stack home
at `name+104`, outside `name[100]` and too late: safety needs
`P+len(S)+1 <= 80` (`len(S) <= 46` at `L=32`). A longer string would overrun
`buf[80]` into `list`/`path` (rebuilt later), and the copy-back would overrun
`name[100]` into the caller's `fd`, `ok`, saved BP and return address before
`redraw` clears the name. For example, a 71-character string at `L=32` sets
LoadGame's `ok`, so a cancelled Load would report success. This is derived from
the original instructions, not an observed ordinary execution; no ordinary
long-string history has been demonstrated either.

## Residual claim

For ordinary initial FileSelect calls from LoadGame and SaveGame(0), no
admitted proof or execution-domain premise guarantees a readable terminator
with `P+len(S)+1 <= 80`. Captured 0..15-byte strings and matching visible
behaviour do not establish it for all prior execution and interrupt histories.
Separately, directory lengths of at most 32 characters and valid 8.3 leaves
bound the retry, while the inherited `L=66` separator overrun and `L>=33`
full-leaf retry overrun remain excluded only by those explicit filesystem
premises.
