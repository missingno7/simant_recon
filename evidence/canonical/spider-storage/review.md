# Spider scratch extent: positive bound and missing premises

The HCEGANT domain fits a four-byte width/height prefix plus 6272 pixel bytes.
This is a conditional access bound, not admission of the full historical owner.
`_fd_50F6_1F26` remains unresolved.

Reproduce with a fresh output directory:

```
python evidence/canonical/spider-storage/probe.py --out build/workers/spider-proof/run-001
```

The probe enumerates 256 placements for each of the 12 present spider pictures,
including the high byte of word read/modify/write accesses. It executes the
original decoder at each picture's greatest-access placement. The maximum is
owner offset 5883. Original last-pixel raster controls reach offsets 6275, 3531
and 1571 for planar, packed and mono images. Planar/mono raw screen-reader
controls reach their corresponding limits. These are typed entry-state controls,
not full startup or caller execution.

A grammar-valid synthetic 112-by-112 picture at the real source-produced
placement `(21,23)` makes the original planar decoder touch offsets 6276–6278.
This proves a resource-dimension premise is necessary. It is neither a shipped
spill witness nor authority to enlarge the buffer. Missing MONONT/L256NT resource
sets and the plain-picture callback family are not discharged by HCEGANT controls.

Other source obligations remain. LoadTiles modes 1/6 do not establish the tile
kind used to set DrawSpider's skip local. LoadGame restores direction/death-cycle
and other spider state without local range guards. The final viewport-tile blit
can execute after PreDrawSpider returns with its offscreen sentinel. A stale
positive height clips out under the tested signed clip contract; zero height has
a `bottom-1` wrap and requires separate raw-renderer/caller analysis. The clip
control models the exact source outcode leaf explicitly; it does not execute
the complete screen wrapper. The exploratory Tandy raw-screen fixture did not
pass and grants no claim.

No source owner, initializer, padding, game algorithm or native exception was
changed. The remaining lifetime/geometry/resource premises are semantic work.
