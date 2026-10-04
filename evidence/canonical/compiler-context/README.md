# Current canonical context residue review

Nine historically EXACT C bodies remain token-identical after registered aliases, but their rebuilt machine bodies are byte inexact. Each change is classified below and in `review.json`. The full static relation is `static-receipts.json`; full extents and symbolic instructions are in `machine-evidence.json`. Historical bytes, extents, fixups and relocation failures remain visible. No new BEHAVIOR_EXACT claim is made.

| Function | Original/current bytes | Changed regions | Relation |
|---|---:|---:|---|
| PopUpInfoWindow | 724/724 | 2 | reassociated word arithmetic, commuted addition and subtraction |
| DrawCurBalloons | 1680/1680 | 5 | paired comparison reversal |
| DrawSpider | 1433/1433 | 2 | commuted word additions, paired comparison reversal |
| f_1E57_0F8E | 78/83 | 1 | reversed rectangle comparison with segment reload |
| f_23E6_0392 | 390/390 | 1 | commuted word addition |
| PrevListLine | 381/381 | 1 | commuted word addition |
| win_Recalc | 372/371 | 4 | equivalent table address calculation, paired signed loop-test reversal, folded table displacements |
| f_2505_0831 | 185/185 | 1 | commuted word addition |
| f_2505_08EA | 164/164 | 1 | commuted word addition |

**All nine full machine bodies:** zero unexplained instruction differences; unchanged instruction pairs, all branch successors, call symbols, memory widths, argument words and caller-preserved state are accounted for. The compiler-record relocation ordering failure in DrawCurBalloons and shifted relocation sites in win_Recalc are retained as historical proof debt.

**win_Recalc:** its 372/371-byte relation contains four reviewed regions: three equivalent ways to form/fold `w.offset + 4*i + 0x2C` and one paired signed loop-test reversal. The object initialization writes four words at offsets 6, 2, 4, 0; the iterative pass calls the same coordinate helper for k=0..3, updates the same coordinate/counter words and advances p by two; the normalization pass passes the same far pointers; exactly four MOVSW instructions copy eight bytes to the window header; the same handle is released. The claimed 298-byte positional diff is caused mainly by shifted addresses, not 298 distinct semantic changes.

**Rectangle f_1E57_0F8E:** all first three comparisons are unchanged; the fourth reads the same signed words in reverse order and changes JG to JL. The complete current extent is 83 bytes, including both calls and the epilogue. The historical 78-byte matcher clips the second fixup, explaining its extent-crossing diagnostic; this review never trims the new tail.

**Bounded corroboration:** 416 rectangle cases (160 directed, 256 random, seed 0x1E570F8E) and 110 win_Recalc cases (46 directed, 64 random, seed 0x2505ECAC) passed with zero mismatches and zero execution errors. Original Ralloc/window/coordinate/normalization/autosize helpers run from immutable EXE bytes; there are no modeled handlers or arbitrary memory exclusions. The window fixture uses n=1..6, modes0..5, convergent type0 autosize, full signed coordinate/sentinel controls and explicit n=0,-1,-32768 machine diagnostics. Negative counts are diagnostic inputs, not a claim about ordinary gameplay.

The fixture-only negative control changes current-side clip.right from equality10 to9 and is detected by helper choice and clip state. It validates observation sensitivity. It is explicitly not a source-based negative control and cannot satisfy BEHAVIOR_EXACT registration.

A first exploratory window fixture omitted the already-locked entry precondition, and a first type0 autosize fixture had nonzero left/top origins that need not converge. Both hit budgets in the original executable; the final recorded corpus specifies the locked entry precondition and convergent autosize domain. No compiler/source variant or executable mutation was used.

Reproduction in this scratch directory: `python extract.py`, `python static_review.py`, `python execute.py`, `python index.py` while the historical/current source inputs still have their pinned hashes. Source and current-object snapshots preserve all required review inputs. Production integration should rebuild those same contexts rather than use this research adapter as an acceptance gate.
