# DrawColonyBars acceptance

The 490-byte S13:384C DrawColonyBars body is accepted in natural C. The strict
search and promotion gate prove all bytes, 23 fixups and five relocations, with
grouped relocation order. All 22 earlier claims and CONST (114 bytes) / DATA
(206 bytes) remain exact. InvertPatch remains scaffolded; this is a partial TU.

The first high-resolution branch starts with the unadjusted rectangle left
coordinate, subtracts the row displacement from that field, and derives its
right coordinate from the field. Both low-resolution branches assign bottom
before left. The last high-resolution branch uses a real baseLeft intermediate;
every local is used, and no padding, folded reads or assembly were introduced.
The earlier local-coordinate negative differs in 20 instructions / 42 bytes.

Full validation passed the tests (two skips) and all 45 compiler probes. A fresh
hybrid build passed with original SHA-256
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`.
Manifest hash:
`3235d9b8161d865ceb0954ef0ef90fc69731c13255a75a20091747d112dac1b9`.
The remaining game debt is 17,144 code bytes and 129 data bytes; linker debt
remains 17,001 bytes. Hybrid equality is oracle-assisted and is not historical
closure or proof of an independent link.
