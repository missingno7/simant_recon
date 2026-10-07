# SDL3 port repair method

The closed DOS oracle (`functional-source-oracle-v1`) defines correct behavior.
Every native defect is handled by the same pipeline; a symptom fix without a root
cause is not accepted.

1. **Detect.** A divergence comes from the native-vs-DOS differential tool
   (`portable/tests/acceptance/`), a regression or a human playtest. Record the
   reproducer (scenario, input timeline, checkpoint/step).
2. **Attribute.** Compare original `SIMANT.EXE`, the canonical DOS build and native:
   ORIGINAL (preserve, never "fix"), RECONSTRUCTION_INTRODUCED, PORT_INTRODUCED or
   UNATTRIBUTED with the deciding experiment.
3. **Localize.** Find the first canonical function that computes a different value
   (native GDB vs DOS observation runner) and look up its proof level. A divergence
   originating in byte-exact canonical code cannot be a reconstruction defect; it
   is a port or input/timing defect. Reconstruction defects can only originate in
   non-byte-exact code or data.
4. **Root cause.** Name the mechanism, not the symptom: which conversion rule,
   platform contract or hand-written component produced the value, and why the
   mechanical process allowed it. Assign a defect class.
5. **Census.** Enumerate every sibling of that class across the whole port with a
   reproducible tool, not by inspection. Each sibling is fixed, proven
   non-observable or left open with a named experiment.
6. **Fix the class.** Fix the generator, conversion rule or platform contract.
   Prefer a line-traceable projection of canonical source/ASM over a hand-written
   reimplementation. Never change canonical game algorithms in native code.
7. **Prove.** Add a regression with a negative control that fails on the old
   behavior; rerun the differential tool and confirm the divergence moved later or
   disappeared, with no new earlier divergence.
8. **Record.** Update the single behavior ledger
   (`evidence/canonical/behavior-attribution/`): attribution, origin function and
   proof level, root cause, class, sibling census, fix commit, regression.

Defect classes found so far: host-injected inputs; hand-written replacement of
canonical ASM; partial ASM reimplementation omitting side effects; DOS object
adjacency broken by native layout; hard-coded wrapper extents; interrupt-driven
updates not delivered inside source wait loops; 16-bit integer semantics.
