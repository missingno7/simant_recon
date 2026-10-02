# Native session integration check

`python portable/tests/run.py --suite session` builds the current portable
modules with strict C warnings and exercises the startup composition against
the repository's real `assets/` databases. The test opens the HCEGANT database
and registry as the host does, then verifies that `SimSession` borrows them,
loads the SHARED sine resource and HCEGANT tile set, obtains control dimensions
and rectangles from the bitmap decoder and registry, seeds both RNG streams
once from explicit TickCount values, and starts source-derived scenario 1.
It then renders an actual generated terrain cell through the tile renderer.

This is an integration test of native module composition, not an additional
DOS differential claim. The original-DOS RandWorld comparisons and their
bounded input domain are recorded separately under
`portable/tests/worldgen/evidence/`.
