# Event record storage admission

Root review admits two separate `struct Event far` objects, each 16 bytes, with
the eight signed int fields and offsets declared in `src/root/m218D.c`. The input
dequeue fills the current record through eight words; whole-record assignment
copies it into the previous record. The source census covers all 156 canonical
and strict-effective sources and all 29 strict receipts. No conflicting owner,
registered interior, numeric alias or SaveRec view supplies an unexplained span.

The fresh `EVRECS` provider contains only the two 16-byte far commons. MSC controls
measure 18-byte wide and 15-byte packed records, and distinguish initialized
previous-record storage with xE=1 at offset 14. Both RTLinks pass full-record
zeroing, field offsets, patterned assignment and a separate 32-byte layout shift.
They reject changed widths, nonzero initialization, +2 current base and a current
pointer aimed at the previous symbol. Root rechecked all 184 preserved artifacts,
14 complete runtime/link/map pairs and the actual symbolic pointer32 fixups.
The admission tests additionally reject field order and signedness changes that
OMF allocation geometry alone cannot detect.

The preserved worker probe is copied verbatim as historical provenance. Its
original execution directory and hashes remain in the receipts; acceptance can
be rechecked with `verify-preserved.py` without running it. Neither ignored probe
objects nor executables are production source inputs.

This establishes source storage and compatible views. It does not establish
historical COMDEF producer, order, numeric placement or pre-CRT initialization.
The resource-height/decoder path that could overwrite the active event code
remains unresolved. The separate seven-record input queue is already owned and
is not merged with these records.
