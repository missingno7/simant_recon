# Sound selector layout dependency v21

Root review confirms an unresolved executable/layout dependency, now explicit in
SOURCE_ONLY_DOS preflight. IBMInitStuff in S20 accepts a lowercase `/s` followed
by a digit, including 9; later valid switches override earlier/config values.
The detector, setup and cleanup tables each have nine entries, indexed 0–8.
After the sound DB open returns, explicit 9 reaches the unguarded detector lookup.
Automatic selection and explicit zero take distinct, accounted-for paths.

Detector[9] reads the next pointer object in the same accepted TU. Its symbolic
initializer targets the source-owned seven-word saved-state data. That proves
where the far call starts; it does not prove executable behavior or return from
data. The saved-state allocation and startup-zero contract cannot discharge it.
Conditional on a normal return, zero falls back to mode 1; nonzero retains 9 and
setup[9] aliases cleanup[0] within the accepted setup TU. Conditional on saving 9
and later cleanup, cleanup[9] reads data in another TU under the historical
manifest adjacency. Independent linking does not establish that adjacency or a
valid function target. These conditional paths are not assumed reachable beyond
the first unproved data-as-code call.

The worker receipt and context transcripts are preserved alongside this review.
The root JSON separates source pins from historical build observations, and
labels the worker's static contrast expectations as unexecuted. A copied metadata
error for root:277E was corrected against all actual source/object hashes before
this review. No canonical implementation or frozen semantic category changed.
No clamp, tenth table entry, guessed executable padding or original bytes were
introduced. Pre-init DB error-path closure remains a separate proof.
