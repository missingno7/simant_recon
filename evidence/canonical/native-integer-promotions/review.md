# Native integer promotion boundary

Classification: **SEMANTIC / PORT-BLOCKING**. This is a bounded static conversion
limit, with no runtime failure witness and no new experiments.

`scalar.py` lexically maps scalar declarations, signatures and existing casts to
fixed-width types. It leaves numeric literals and expression operators intact.
Current GCC promotes both `int16_t` and `uint16_t` to its 32-bit `int`; DOS used
16-bit `int`/`unsigned int`. A later assignment narrowing does not establish equal
intermediate multiplication, division, shifts or comparisons. Unsuffixed `0x8000`
also selects different integer types on the two targets.

Two current anchors illustrate the remaining scope:

- `FindIndex`, canonical `src/root/m1986.c:87`, generated
  `build/portable-checkpoint/root_1986.c:75`: `mid = (fd_50F6_3956 + top) / 2;`.
  Native addition precedes division in 32-bit `int`. Shipped counts 120/271/449
  provide no overflow witness. ISO C signed overflow is undefined; this receipt
  does not assume a universal DOS signed-wrap contract.
- `GetTriLatDist`, canonical `src/root/m0798.c:477`, generated
  `build/portable-checkpoint/root_0798.c:481`: `(unsigned)dy > triHeight - 2`
  becomes `(uint16_t)dy > triHeight - 2`. `triHeight` is unsigned in the canonical
  declaration. DOS subtracts in unsigned 16-bit arithmetic; native promotes to
  signed 32-bit arithmetic. The comparison agrees when `triHeight >= 2`; the
  below-two boundary has no established shipped-domain reachability witness.

Dedicated RNG word narrowing and already explicit canonical sentinel casts are
examples of locally preserved semantics. Existing RNG, movement and database
receipts support their bounded tested domains. They do not establish every
expression or every reachable input domain across the program.

`receipt.json` pins the current canonical inventory, cited TUs, converter, build
report and existing test receipts. No canonical or platform files were changed.
Checkpoint claim: **fixed scalar storage/cast widths plus bounded validated
adapters; global DOS 16-bit intermediate expression semantics remain unproved.**


The active conversion is now the declaration-driven frontend documented in
[../native-integer-expressions/README.md](../native-integer-expressions/README.md).
This older packet is historical context, not a receipt for the current pass.
