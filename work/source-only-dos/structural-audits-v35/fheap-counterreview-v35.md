# Counter-review: dgroup_79f0 / __fheap

**Decision:** keep the 14 bytes in the functional unresolved_data inventory. The pinned runtime evidence supports a narrow __fheap owner attribution, but does not yet discharge this data debt. Keep all 14 bytes in historical debt as well.

tools/source_only_dos.py copies approved spans into both unresolved_data and historical_data_debt. The current report has 46 unresolved functional bytes and 113 historical bytes; dgroup_79f0 is among the 46. There is no fheap resolution path in the tool. A future disposition can remove the span from the functional gate while retaining it in historical debt, but must establish that source-only behavior is accounted for.

The shared tools/source_only_dos.py changed after this review read it. The gate description above refers to the version observed at hash 407fc746…; the receipt records the later current hash and the build report's older pinned hash separately.

The v36 packet proves that pinned LLIBCR.LIB(fdata.asm) uniquely defines a word-aligned, 14-byte __fheap contribution with the expected bytes and descriptor shape. Isolated controls execute the real allocator API and typed observer. This establishes an available runtime owner. It does not map the original 79F0 interval to that member or show that the complete source-only application selects or uses it. The v39 links remain incomplete with 15 unresolved symbols; RTLink 6.10 selects fdata.asm without fmalloc.asm and marks the public unused.

The root-reviewed original-operand census strengthens the negative evidence: 1,730 registered function extents plus 90 accepted runtime extents, 129,044 decoded instructions, zero immediate or memory-displacement operands in 79F0–79FD, and no incomplete decodes. Its own scope excludes unregistered code, embedded data, computed aliases, segment provenance, and indirect references; it explicitly says absence of literals discharges no debt.

**Pending observation from the parent:** a signed-char ctype lookup of the form (_ctype + 1)[buf[start]] in win_PrintStyleTextInRect and menu code may reach 79FC for input byte -35 (0xDD). A focused worker is validating the alias. Treat it as a lead, not established evidence or proof that the original span belongs to either ctype or __fheap. If confirmed, it is a concrete conditional read into the candidate interval and further defeats an owner-only discharge until the alias is accounted for.

Minimum closure evidence is either (a) a complete source-only link/map and object binding that show the relevant runtime owner and all applicable source references resolve symbolically, plus resolution of any ctype alias; or (b) a bounded original reference audit that accounts for all direct and computed reads, relocation-backed pointer tables, and possible unregistered code. The existing census covers only literal operands, so its zero count alone is insufficient.

No canonical source, provider, tool, ledger, layout, promotion journal, or Git state was changed. This review writes only to its assigned worker directory.
