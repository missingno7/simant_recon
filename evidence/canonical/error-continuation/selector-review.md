# Critical selector alias review

## Result

There is a bounded path to the historical `g_8CCB` byte from two unchecked
computed stores, but neither path is reached by the existing shipped-default-VGA
successful lifetime. This is a domain conclusion, not a global zero/deadness
claim. Keep the one-byte signed owner and the exact error-string reader; do not
replace the read with a constant or claim that arbitrary aliases are impossible.

The current supported domain is important: the locked default configuration and
SHARED/HCEGANT/SOUND corpus, no replacement resources or `/s9`, successful
file/header/index operations, and valid nominal game/save state. This review
does not claim behavior for returning diagnostics, malformed/replacement files,
external calls, invalid IDs or corrupted memory/control flow.

## Exact selector owner and observer

`src/state/critical-selector-byte.c` owns only `char near g_8CCB;`, with static
duration and genuine CRT zero initialization. The complete current C/ASM token
census has four references: that definition, two declarations and one read in
`f_1C62_06A6`. The source has no assignment/address-taking of the selector, no
program alias names it, and the data symbol registry has no other symbol at its
address. The whole-original-function scan found exactly one direct absolute
DS:8CCB operand: `mov al,[8CCB]` at `root:1C62:06C8`, a read in the same
function. The source function table reports zero callers for `f_1C62_06A6`.

That helper uses the signed byte only when its `err` argument is below zero or
above `sys_nerr`; the ordinary in-range path indexes `sys_errlist`. No ordinary
source caller is known. The hard-error callback installed at startup is
`f_208F_058B`, which simply returns 3; it does not write this selector. The
evidence does not claim that external code can never call the public helper.

## Window-cache alias

The private `g_8CF2` cache is one 45-element array of four-byte far pointers in
`root:23AE`. Its source writes are initialization to zero, the cache update in
`f_23AE_0069`, and the clear in `win_UnlockWin`. The original stores use the
DS displacement for base offset 8CF2. Index `n = win >> 8 == -10` makes the
pointer span DS:8CCA..8CCD, so byte DS:8CCB is physically covered.

`f_23AE_0069` rejects `n<0` or `n>40` by calling `Punt`, then continues if that
diagnostic returns. `win_UnlockWin` has no independent index check. This is a
real counterexample for an invalid `win=F600..F6FF` plus a returning-Punt
continuation; it is not assumed away for arbitrary state. In the admitted
ordinary domain, the independent handle caller/alias proof bounds the high-byte
window IDs to 0..33 for all 1,033 calls into its 217 relevant functions. The
event-selected path requires its high byte to equal the valid stack top, while
resource/object paths preserve that byte. The K: FileSelect counterexample
produces a bad *low object index* (21) in valid window 22; it does not produce a
negative window index. Thus the still-open general object-index gate does not
reopen this particular `g_8CF2[-10]` alias.

## MIDI track-offset alias

The source-owned `g_8DD8` track-offset view starts at DGROUP:8DD8. Original
`f_284A_0199` stores `off+8` at `[2*i - 7228h]`, i.e. `(8DD8h + 2*i) mod
10000h`. `g_8CCB` is the high byte of the word starting at 8CCAh. The first
index that reaches it is `i=32633`, requiring signed-positive `count>=32634`;
this is not capped by the C loop itself.

The supported producer chain supplies the needed bound. `f_284A_0256` loads
`g_7566` from the selected SMF header and passes it to `f_284A_0199`. The
hash-pinned shipped-resource audit parses all 33 metadata records and 30 SMF
streams, expands all 36 source song callsites to present metadata IDs, and
finds declared/parsed track counts 2..10. The scheduler lifetime review shows
the count is assigned only during successful song load and read by the active
track loops; song change/stop/completion do not manufacture a new count. A
synthetic valid 19-track SMF is accepted by the parser, confirming that 10 is a
shipped-corpus bound rather than a generic file-format clamp; even 19 is far
below the alias threshold.

`selector_probe.py` runs the original unmodified `f_284A_0199` instructions
with zero test-owned song bytes and a separate fixture stack so that this
deliberately huge unsupported write walk does not corrupt its own return frame.
Counts 10 and 32633 leave a selector canary unchanged; count 32634 changes it.
This proves the arithmetic counterexample in the original instructions, not a
loaded song, a valid resource, or supported gameplay reachability. The separate
stack and chosen starting offset are explicit harness controls.

## Current-domain conclusion and limits

The known computed writers require either a negative window index (or a
returning `Punt` after that invalid ID) or an SMF track count at least 32634.
The existing default-domain window provenance excludes the former; the
independent complete shipped-song/resource and scheduler proof excludes the
latter. These two reviewed producers therefore cannot mutate the CRT-zero byte
in the supported domain. This is not a complete exclusion of unrelated physical
writes: any indirect effect of the still-open graphics-copy and viewport
contracts remains with those gates. The exact original reader is retained;
no helper activation/deadness, global preservation or arbitrary
corruption-immunity claim follows.

No ordinary semantic input can produce a valid `win>>8 == -10` or a shipped
SMF count near the store threshold. A broadened resource/API domain, a returned
fatal diagnostic, or corrupted pointers/counts reopens the old physical
aliases. Keep those counterexamples and scope limits attached to any proposed
gate reclassification.

## Reproduction and permanent controls

`python evidence/canonical/error-continuation/selector_probe.py` checks the
reviewed `selector-facts.json` without refreshing it. Whole-inventory and registry
pins bind the source audit, including unrelated numeric-address ingress. The
alias-aware C/ASM census, complete handle-ID proof, all shipped song streams and
calls, and all 307 save descriptors are rechecked. The original direct-operand
scan above is corroborating evidence only; it does not exclude computed writes.
`tests/test_supported_dispatch_domains.py` retains changed-writer, changed-count,
protected-save-range and original out-of-domain store controls.
