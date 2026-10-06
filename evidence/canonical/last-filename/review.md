# Last selected filename: bounded owner and retained path gate

The canonical last-filename state has one 100-byte, zero-initialized far owner.
This closes `_fd_50F6_3862` only for executions in which the original fixed
automatic objects remain valid C strings. It does not repair or waive the
independent `FileSelect` path overflow demonstrated by the DOSBox-X control.

The complete canonical source census finds every direct access in S09:35F5.
`LoadGame` and `SaveGame` each use a 100-byte automatic `name`. The only whole
string stores to the global are `_fstrcpy` calls from that object; the other
writes clear byte zero. The only whole string read copies the global back into
the same 100-byte object. Therefore an initially empty 100-byte global remains
a valid string of at most 99 characters plus its terminator after every
defined, terminating copy. The owner needs 100 bytes and no initializer.

The selector has separate `path[67]`, `lastDir[67]`, `buf[80]`, and caller
`name[100]` objects. The existing real DOS helper control reaches a valid path
requiring 69 bytes after separator append, so `path[67]` and the later
`lastDir` copy can overflow before the global store. A path which fits those
objects needs at most 67 bytes including its terminator before the selected
leaf is appended. The reviewed extension helper adds at most twelve leaf
characters, so the returned name needs at most 79 bytes including its
terminator and fits both the caller and the new global owner. The 69-byte path
negative remains a live `filename-selector-local-capacity` semantic gate.

The owner claims no historical defining translation unit, placement, or
behavior for already-overflowing locals. The S09 functions remain unchanged
and byte-exact. The native duplicate is retired because canonical source now
supplies the same 100-byte object on the host.

Run `python evidence/canonical/last-filename/replay.py` to recheck the source
census, fixed-object invariants, existing DOS path contrast, and canonical
storage contract.
