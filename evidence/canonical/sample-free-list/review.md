# Sample free-list owner

`root:0000` is the only source consumer of `fd_50F6_0150`.  Its
`f_0000_0149` helper checks `g_181C > 38` before storing one far `Sample *` at
`fd_50F6_0150[g_181C]`, then increments the count.  Original-instruction
controls retain the boundary: incoming counts 0 and 38 store at indices 0 and
38; incoming count 39 reaches `Punt` before the store.  A separate returning
`Punt` contrast stores index 39 and is excluded from this successful-domain
owner, consistently with the repository's explicit exceptional-continuation
policy.

The canonical owner is therefore 39 four-byte far pointers (156 bytes),
zero-initialized by MSC's far communal storage.  This is functional ownership
for the supported lifetime through the first free-list fatal boundary.  It
does not claim the original producer translation unit, communal order,
historical placement, adjacent bytes, or behavior after a returning fatal
diagnostic.

The locked Sound Mode 6 setup has two DAC channels and eight FM channels.  A
complete parse of all 33 shipped song metadata records and 30 MIDI streams
retains an additional corpus control: those streams issue no DAC note in the
mode-6 instrument table.  Concurrent sound effects still use the list, so this
fact is not used as a deadness claim.

`replay.py` pins the complete canonical source inventory, consumer/callee
census, original oracle, and shipped sound database.  It verifies the
canonical OMF shape and repeats the original boundary controls.  The retained
negative controls reject a 38-entry owner, a changed consumer guard/order, a
changed corpus, and treating returning `Punt` as an admitted store.

```powershell
python evidence/canonical/sample-free-list/replay.py
python -m unittest tests.test_sample_free_list_domain
```
