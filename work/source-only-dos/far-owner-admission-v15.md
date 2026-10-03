# Reviewed functional FAR_BSS owners, v15

Root review admits seven data-only source providers containing 33 objects and
278 bytes of typed storage. This establishes functional source ownership,
types, extents and bounded registered views. It does not identify historical
COMDEF-producing translation units, communal order, padding or link placement.
Canonical sources, the layout manifest and historical debt remain unchanged.

| Provider | Objects | Source ownership anchors |
|---|---:|---|
| ant-list-counts | 3 | Signed count consumers; three direct 2-by-1 SaveRec rows; exact-base aliases |
| colony-simulation-words | 8 | Signed simulation operations; eight direct 2-by-1 SaveRec rows |
| player-locations | 6 | Signed coordinate/plane reads and writes; six 2-by-1 SaveRec rows; three player aliases |
| ant-counters-timer | 3 | Two 32-bit counter consumers and 4-by-1 SaveRec rows; signed long timer comparison/update |
| language-string-list-pointers | 5 | PrepareStrings and LoadStringAnt establish far-stored pointers to rows of far string pointers |
| dead-ant-coordinate-rings | 2 | DeadAntHere's unsigned 100-byte declarations and two 1-by-100 SaveRec rows |
| ant-player-state | 6 | Signed state consumers; six 2-by-1 SaveRec rows; three exact-base aliases |

Each complete provider contains natural C definitions only. Fresh MSC 6.00AX
objects must contain exactly the reviewed far communals, with no code, live
initialized data, public definitions, relocations or additional allocations.
Registry guards check the 33 historical anchor identities and all exact-base
names; neighboring names are not used to infer extents. Canonical declarations
and operations, not COMDEF encoding alone, establish source types. In
particular, signed/unsigned words and some byte-array/pointer views can have
the same object shape.

The final durable probes run actual MSC startup and test-owned consumers under
RTLink 4.00 and 6.10. The required matrix has 112 rows: 24 list-count, 6 colony,
14 location, 16 counter/timer, 16 language-pointer, 12 coordinate-ring and
24 ant/player controls. Raw result classes are preserved, including
FAIL_PTR, FAIL_ZERO, FAIL_ALIAS and UNSIGNED_CONTRAST. Two location long-width
measurements pass and stay outside that matrix. Both counter two-byte-owner
overrun diagnostics also pass despite a measured wrong extent; their expected
FAIL/actual PASS outcomes remain non-gating and cannot prove an extent.

The final provider basename is ANTSTATE, eight DOS characters. The earlier
ANTPSTATE proposal failed the independent compiler check; all seven durable
probes were refreshed after the artifact-name correction. No old run is
represented as having used the final tools. Language pointers emit far COMDEF
count=4, element_size=1, length=4; earlier count=1/element_size=4 prose was
corrected from the measured OMF records.

The dead-ant admission uses a separate typed provider. The experimental
root:0894 definition candidate is excluded: its fresh control hash differs
from the manifest object, and external ordering differs. The canonical TU
retains its extern declarations.

The reset review joins source spellings through registry code addresses and
dos.identifier_aliases. RandWorld calls BuildAntListA, ClearListB and
ClearListR through f_0EC1_0719, f_0EC1_07C1 and f_0EC1_07D4. RandWorld and
RandYard call ClearHistory through o24_39C7_01B8. The earlier exact-name-only
caller lists do not establish absence. initControls and GetStrategy likewise
have real alias-resolved calls. Successful LoadGame's o11_ aliases resolve
to SetMenuEntries and PauseGame. Ordinary simulation assigns StrategicModeB
in GetStrategy before the traced mode-table consumers.

These conclusions do not close unchecked restored counts/coordinates,
partial SaveRec writes, wider backing-array extents, timer wrap, language
resource counts/index domains or resource-payload lifetime. They remain
integration and layout questions. The canonical and strict effective
SpiderScan bodies are inventoried separately. Initial-state ownership of
the near UI region and clip sentinel remains open.

Per-family source reviews and probes are the durable *-owner-review-v1.md and
*-owner-probe.py files beside this receipt. Their admitted contracts preserve
the exact fresh report, input and tool hashes; root validation checks every
flattened input pin, fresh production-shaped objects, and both selected
linker/runtime gates before admission.
