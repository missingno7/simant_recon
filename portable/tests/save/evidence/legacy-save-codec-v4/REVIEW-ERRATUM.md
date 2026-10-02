# V4 execution identity limitation

The V4 runner and original packet are preserved unchanged. Review found that
GCC/MSC toolchain snapshots occur after the original DOS probe, and that the
receipt's named before/after toolchain maps are recomputed at packet-write time.
The runner does compare saved compiler hashes across the later native runs,
but the reported snapshots do not establish tool identity across the earlier
DOS compilation. The README's blanket before/after claim must be read with
this limitation.

The 59 source/evaluator/resource inputs are recorded before the DOS probe and
after execution and remain identical. All five native variants have 11-file
GCC local dependency closures, including legacy_codec.h. The positive stream
comparisons and sensitivity failures remain finite diagnostic results, not
production save or complete execution-identity acceptance. A new V5 packet
will retain actual toolchain snapshots from before the entire experiment.
