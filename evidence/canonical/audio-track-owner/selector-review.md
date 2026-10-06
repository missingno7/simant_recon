# Default sound-selector lifetime

`sound-selector-out-of-range-layout` is resolved only in the existing
`shipped-default-vga-successful-lifetime` domain. The detector index is 6;
completed setup uses 1 or 6; cleanup uses startup 0 or the completed value.
All fit the three existing nine-entry tables. No canonical game code, table
extent, hardware policy or `/s9` behavior changes.

The locked SIMANT.CFG contains Sound Mode 6. `IBMInitStuff` resets `g_610A`
to -1, calls `ReadConfig`, and then parses arguments. Successful reading stores
6; the already admitted empty argument list preserves it. The ordinary main
lifetime calls the sound shell once after this startup. Its initialization flag
prevents repeated setup. The source/alias census includes startup, shell,
selector and dispatch state and binds the complete canonical inventory.

`f_277E_0000(6,0)` tests detector 6. A false result changes its local mode to 1;
a true result leaves 6. The setup call uses that local value, and the sole
assignment to `fd_50F6_01F0[0]` stores it after setup. Other element assignments
are fixed indices 1..6. The seven-word canonical owner starts at zero by static
storage initialization. There is no escaping selector address or subsequent
writer. `fd_55B3_74FE` is the read-only-in-this-lifetime pointer view of the same
array; it supplies diagnostic arguments, not another selector producer.

Cleanup before setup matters: S15 tests the configuration word, whose startup
-1 and configured 6 are both true. It can therefore enter sound cleanup before
the final selector store. Element 0 is still zero then, and cleanup entry 0 is
valid. A cleanup during setup likewise observes zero until the final store.
The completed values 1 and 6 also select valid cleanup entries. No global
`Punt` noreturn assumption supplies this argument.

The probe binds all 195 sources, module contexts, program aliases and the full
symbol registry, with 150 relevant references. It reuses the database resource
and complete startup census. All 307 SaveRec descriptors match canonical source
and the original and avoid seven protected ranges: selector array, configuration
word, shell flag, pointer view and three dispatch tables. All 27 original table
targets match the reviewed canonical initializer identities. Song resources
write their separate song/channel state; they do not assign the selector.

Original-instruction controls execute both detector outcomes and the setup
selector store with hardware/setup helpers explicitly modeled. Separate S15
prefixes reach cleanup with selector zero and stop at the real exit call
boundary. Cleanup controls use actual table dispatch for values 0, 1 and 6,
with external helpers modeled. These are selector/dispatch observations, not
hardware initialization, full shutdown or audio acceptance.

The `/s9` contrast stops before the original indirect transfer. Index 9 reads
the adjacent pointer `50F6:01F0`; neither execution of that data nor its possible
return is claimed. The existing domain excludes `/s9`, autodetect configurations,
replacement resources and arbitrary corrupt state. No clamp or extra slot is
introduced. General sound and sample-free-list behavior remains open.

Run `python evidence/canonical/audio-track-owner/selector_probe.py` and
`python -m unittest discover -s tests -p test_supported_dispatch_domains.py`.
The runner strictly compares reviewed facts; permanent negative controls cover
new writers/callers, aliases, foreign configuration and overlapping save records.
