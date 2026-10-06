# Punt guard and database exhaustion prefix

The current exact `root:1C62` source gives `Punt` two contracts. With the private
word `g_54F8` equal to zero, it sets that word to one, formats the message, invokes
the graphics callback and text renderer, and calls `o15_384C_0152`. With any
nonzero word, it immediately returns. The diagnostic's fatal wording does not
override this branch. `o15_384C_0152` attempts cleanup and `exit(0)`, but entry
into that helper is not guaranteed by the `Punt` name or prototype.

`replay.py` runs unchanged original instructions from the locked DOS oracle in
the pinned isolated Unicorn runner. Guards 1, 2 and FFFF return without entering
a formatting/rendering dependency. The zero-guard negative contrast sets the
word to one and stops at the first `vsprintf` entry. Original `DosPunt` with
guard one returns after one `Punt` call for errno 2 and two calls for errno 24.

The database controls execute original `GetFreeHandle`, `OpenDB`, `Punt`,
`CopyRootName` and its real string helpers. Occupancies zero through three copy
the fixture name into their valid 124-byte records. Four occupied names return
minus one; with incoming guard one, `Punt` returns and the real copy writes the
name at `50F6:38DC` and its terminating byte at `50F6:392B`. This lies before
the admitted four-record owner. Execution stops immediately after the copy,
before the first DOS call; no syscall or returning-Punt callback is substituted.

These incoming guard/occupancy values are explicit test fixtures. They do not
prove ordinary startup reaches that combined state. The separate
`graphics-index-failure` witness shows why completed fatal-state invariance
cannot be assumed, but also does not establish this combined state. This probe
is a permanent regression of the exact conditional contract, not authoritative
DOSBox-X whole-game acceptance.

The source and oracle identities are checked before replay. Source mutations
and a changed oracle identity fail before execution; guard zero and occupancies
zero through three are negative controls for the returning/preceding-owner
conclusions. All published results contain scalar observations and pins only.
No code bytes, raw memory dump, extra record, padding or new owner is published.

```powershell
python evidence/canonical/error-continuation/replay.py --out build/scratch/error-continuation
python -m unittest discover -s tests -p test_error_continuation.py
```

The returning guard behavior is `SOURCE_REQUIRED`. The database exhaustion
alias cannot become `HISTORICAL_LAYOUT` solely because a normally initialized
fatal path aims at `exit`. A separately verified successful resource/caller
domain can classify the minus-one and fifth-slot accesses `SUPPORTED_DOMAIN`
within that domain; failure and externally supplied resource configurations
remain outside that exclusion.
