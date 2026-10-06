# Spider scratch extent: supported VGA owner

The supported shipped-default VGA8 lifetime fits a four-byte width/height prefix
plus 6272 pixel bytes. This establishes a source-functional owner of 6276 bytes;
it does not claim the historical defining TU, COMDEF capacity or link placement.

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

The current supported domain fixes `g_5A97` at 8 and uses HCEGANT, so the missing
MONONT/L256NT databases and LoadTiles modes 1/6 are outside this owner. InitSpider
sets direction zero; every ordinary producer assigns 0/4 or indexes the shipped
eight-by-eight TurnTab, preserving 0..7. Death mode initializes `Scycle` to zero
and changes it only to 1..3; other modes mask its raster use with `&7`. The common
domain already limits loads to valid nominal, source-produced saves, so raw or
corrupt saved indices are excluded.

The final viewport-tile blit can execute after PreDrawSpider returns early. A
stale positive 84/112 height is rejected because both vertical outcodes are
above the nonnegative screen clip. On first use, FAR_BSS zero initialization
gives dimensions and the rectangle left coordinate zero; clipping produces the
degenerate `[0,0,0,480]` piece. The original aligned VGA raw driver completes
without reading or writing the image arena. A synthetic `x=1` contrast does read
payload bytes and fails to return, proving that first-use zero alignment is a
necessary premise rather than a general zero-width rule. The clip control models
the exact source outcode leaf explicitly because stopping at that nested far
helper triggers a Unicorn resume artifact; the original clipper body and original
raw VGA driver are exercised separately and compose on the recorded rectangle.

The admitted owner is an uninitialized FAR_BSS `SpiderImage`: two 16-bit
dimensions followed by 6272 bytes. All consumers are synchronous. The raster
binder and screen/overlap callbacks retain no pointer beyond their calls. The
synthetic 112-by-112 negative remains outside the pinned HCEGANT resource set and
continues to guard the resource-dimension premise.
