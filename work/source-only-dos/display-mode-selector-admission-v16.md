# Reviewed functional display selector owner

Root review admits `char near g_5A97;` as a one-byte source owner. The accepted
`main` calls `IBMInitStuff`, which calls `ReadConfig` before any selector read.
Every returning config-mode branch writes the byte; missing/invalid config
paths call the real C `exit`. Command-line display switches can overwrite it
afterward. The pre-config cache-hook registration only stores callbacks, and
the drive-reset helper has no selector access. No installed game interrupt
handler precedes this write. This source argument establishes first-write
dominance without assuming the original initializer.

The full canonical and strict-effective source inventory has no selector
address escape, indexed object access or fixed numeric alias. Signed plain-char
startup reads interpret `?` as -1. Unsigned consumers use byte equality or low
bits. The accepted source declarations and byte operations establish the
one-byte extent; compiler COMDEF shape alone cannot distinguish signedness.

The durable producer probe executes accepted ReadWord, SkipWords and ReadConfig
definitions against generated configuration files and the real MSC CRT. Both
RTLink profiles pass all 21 cases: eight modes from each of 00/FF entry bytes,
four invalid/missing-file exits, and one tentative-owner CRT-zero observation.
The latter concerns only the test owner. This fixture does not execute the
complete startup or its first database consumer; first-write dominance is the
static source conclusion, corroborated by the producer tests.

Only the selector byte at offset 1 of the 26-byte dgroup_5a96 debt is discharged
functionally. The other 25 bytes remain explicit debt, as do the fixed Rect
sentinel, computed-copy bounds and wider numeric-address audit. Historical
initial data, COMDEF TU/order, and original link placement are not claimed.
The generated provider must compile to exactly one near communal, with no
initialized bytes, code, extra storage, publics or fixups. Canonical files and
the historical 113-byte debt ledger remain unchanged.

The probe writes candidate packets into build/workers so rerunning it cannot
overwrite admitted packets. Its raw report and unreviewed source review remain
research provenance; the admitted binding and contract carry this root decision.
