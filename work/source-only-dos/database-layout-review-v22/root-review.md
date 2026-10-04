# Database layout review, v22

Root review retains `database-open-minus-one-record` and
`database-handle-plus-four` as unresolved. The copied worker receipt is research,
and its separate continuation addendum supersedes the earlier implication that
an ordinary return from the first null callback makes the first `Punt` return.

The source continuation is explicit: `Punt` sets its private guard, prints the
fatal message, calls `g_9128`, calls `f_1CE2_01C3`, then calls
`o15_384C_0152`. An ordinary far return resumes the next statement. With ordinary
ABI and control-state returns from both early source-zero callbacks (`g_9128`
and the raster text path's `g_9154`) and intervening helpers, every cleanup
switch branch reaches unconditional `exit(0)`. The standalone CRT exit control
supports that final operation; it did not execute this game integration path.

The missing contract is execution of the invalid zero targets before display
setup. No early-return counterexample or arbitrary corruption was observed.
Successful predecessor opens and no earlier fatal call are premises of the
bounded fifth-open argument, not proof of every earlier error continuation.
No callback initializer, no-return annotation, record before the table, fifth
handle, or historical adjacency is introduced to close these gates.

All 17 direct addendum pins were independently rechecked. Original receipts and
captured build-report observations are preserved. This review changes wording
and retains the two gate statuses; it freezes no storage or layout assumption.
