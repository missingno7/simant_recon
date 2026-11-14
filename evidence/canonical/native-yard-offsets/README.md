# Yard sprite position-table adjacency

The dog uses the same picture/frame in the observed DOS/native PNG triples.
The difference was the signed-byte offset added to the sprite position.

`src/ui/yard_window.c` (`S13:384C`, whole exact module) declares five adjacent
tables at original DS:2A56, 2A62, 2A8E, 2A9A, 2AA2. Their declared byte
extents are 12, 44, 12, 8, 40. Original `DrawSimKid` reads at 04AF/04B6,
04C5/04CC and 04DC/04E3; `DrawDog` at 0703/070A and 0713/071A. The MOV AL
loads are followed by CBW. Thus the index can cross the declaration boundary:

* Standing human frame 20 reads kidX[24], which is kidY[12] = 4.
* Mowing human frame 103 reads kidX[35], which is kidY[23] = 1.
* Dog frame 100 reads kidX[80], which is catOfs[4] = 2.
* Dog frame 102 reads kidX[82], which is catOfs[6] = 2.
* Walking dog frame 9 reads dogWalkY[9], which is catOfs[1] = 1.

The complete 116 bytes extracted from canonical initializers match the read-only
original and canonical DOS first-megabyte captures. The SHA256 is
`f44220b74012c3a287580cd0ef0f97e63ffb5d0d1f8e99bcf02ace3da472284c`.
The original address is runtime_base + 55B3:2A56; the canonical independently
loaded occurrence is recorded in proof.json. No captured byte is emitted as
native source. The original disassemblies are retained in the worker result.

The baseline native PE/DWARF places these arrays at offsets 0, 24, 72, 88,
120 relative to kidX, versus DOS 0, 12, 56, 68, 76. This is observed alignment
padding, not a proposed timing cause. For example human frame 23 reads native
kidY[3] = 3 instead of DOS kidY[15] = 6, shifting human/balloon x by -3.
Frame 20 reads native kidY[0] = 2 instead of DOS kidY[12] = 4, shifting x by -2.

`yard_offsets.py`, called from the existing S13 font/layout adapter, groups the
canonical declarations in that order and accesses them through a signed-char
view of the enclosing object. Accessing a member-array pointer beyond its end
would still be undefined C, even in a packed group. This projection avoids that
mistake. Initializers come only from canonical C. No game algorithm changes.
The supported normal producer domain is human frames 0..11, 20..23, 100..111
and >=200 (no offset read), dog 0..11 and 100..103, and the shipped cat frames.
This is not a general emulation of arbitrary invalid frame values or DOS memory.

`DoSimYard` increments YardCycle. `SimKidOutside` derives motion/picture from
direction, YardCycle and canonical RNG; `SimKidInside` uses the source node
scripts. `SimDog` uses direction, YardCycle and SRand1/SRand2. BoyX/BoyY,
DogX/DogY, frames, YardCycle and map_viewport_rect are already verdict state and
equal through every baseline entry. DrawSimKid/DrawDog add the table offset and
the viewport origin. The VGA balloon reuses the human's adjusted x plus four;
its y uses BoyY and bitmap height. No draw counter or additional clock supplies
these position offsets. MacTickCount in DrawSimKid only expires BoyMessOn and is
already taped. No additional host-time sample is required for the Yard repair.

Reproduce the compiled position/unchanged-picture regression and deliberately
broken cross-table x-read control:

```
python -m unittest portable.tests.acceptance.test_yard_positions
```

Full-game negative: the fresh baseline without this projection reproduces the
four reported first pixel differences. With it, all 152 requested checkpoint
pictures are exactly equal (pixels, DAC, attributes), in all 18 lanes. The old
game-state verdict is equal for every requested entry in those runs. The later
audio policy tightening is independent and does not change any picture or tape.
