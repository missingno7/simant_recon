# Reviewed functional storage admission v21

The sound-record arrays are admitted as two complete source-owned uninitialized
objects: 56 six-byte Voice rows (336 bytes) and 33 six-byte Chan rows (198 bytes).
The complete reset/copy/cleanup loops, all 156 effective game source paths, field
views, caller-index census, registry names, address escapes and assembly/numeric
references were reviewed. Extents do not come from adjacent registered addresses.

Voice retains the signed word followed by a union of long and far-pointer views;
Chan retains six plain-char fields and its independently compiled unsigned-char
reader. MSC600AX produces only the two measured FAR COMDEFs. Both RTLink versions
confirm CRT-zero startup, typed views and all field offsets. Seven runtime cases
per linker retain wrong count, short extent, near-pointer stride/view, unsigned
word view and initialized-owner contrasts. The wrong-name control logs its exact
unresolved symbol and is never executed, although RTLink emits an executable.
Wrong extent controls that print LINKED are rejected by measured OMF shapes;
their runtime result is preserved without claiming that the linker rejected them.

The admission establishes these owners and views, not original object order or
physical placement, arbitrary resource validity, or full sound initialization and
cleanup safety. The initial channel sentinel and all Voice kind fields provide
the zero-state prerequisites for the separate pre-sound-init database proof;
that proof and post-init selector/layout dependencies remain separate reviews.
No canonical source, manifest, promotion journal or oracle lock is changed.
The independent game link and game execution remain gated by other explicit debt.

Executed research input identities and all sixteen raw outcomes are preserved.
Current evidence pins are independently verified; mutable tool/build/context
identities remain observations of their original execution, not repinned outputs.
