# Spider simulation port

`spider.c` implements the native scan and `InitSpider` state initialization.
The scan accepts the game world, LFSR state, and Spider-local state explicitly;
it emits a logical laser event instead of calling the renderer. Its sine table
comes from the loaded shared resource, supplied in native Q15 word form.

`run_dos_diff.py` compares the native function against the retained original
16-bit DOS `SpiderScan` entry. It reads the 64 sine words from shared object
`0x3e8/type 9`, applies the word swap performed by `f_0244_0022`, and installs
that table through the original far-pointer global. The scan's RNG, sine,
ant lookup, and corpse helpers execute from the original DOS image;
`DoLaserFire` is recorded as a logical rendering boundary. The native side
compares the return value, LFSR seed, life and surface maps, ant types, corpse
history, corpse ring index, and laser arguments.

Run the full 10,146-case check with:

```powershell
python portable/tests/spider/run_dos_diff.py
```

The pinned run report, resource/source hashes, and helper boundary list are in
[`evidence`](evidence/manifest.json). The report is supplementary native-port
evidence; it does not alter or extend the frozen historical behavior claims.
