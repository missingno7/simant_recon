# SimAnt reconstruction

The active repository contains the best reviewed reconstruction of the 1991 DOS
program. Published oracle checkpoints are immutable. Active reconstruction is
corrigible: corrected behavior, declarations and storage belong in canonical
source, rather than in later source overlays.

`src/program.json` is the single program inventory. It lists 127 historical
modules and 63 typed storage units. Both the DOS build and native conversion
consume these whole sources. [The source architecture](docs/canonical-source.md)
explains the admissions, views and remaining blockers.

```
                    src/
           canonical reconstructed program
                    |
          +---------+---------+
          |                   |
      dos/build.py       portable conversion
          |                   |
    period DOS runtime   native platform services
          |                   |
       DOS EXE              SDL3
```

The DOS preflight compiles all 190 translation units without original executable
fallback. Independent linking remains blocked by twelve unproved storage imports
and ten semantic address/layout gates. Forty-four functional data bytes remain
unresolved. This is not yet a runnable standalone DOS reconstruction.

The current SDL3 executable runs the converted original main and passes bounded
database, RNG, simulation, VGA, Save and Load checks. It remains a preview with
explicit storage and adjacent-memory contracts in `portable/platform.json`.
See the [consolidation report](docs/consolidation.md) for the changes, evidence,
retirements and limits. The [current source follow-up](docs/source-followup.md)
records proven symbolic DOS addresses, mechanical word-expression conversion
and the narrowed remaining ownership/layout premises.

Current historical validation distinguishes 1,235 byte-exact C functions,
367 genuine assembly functions, 29 strict semantic reconstructions, and nine
historically exact bodies whose rebuilt declaration context has reviewed
codegen differences. [Generated progress](docs/progress.md) retains historical
byte/debt accounting. Semantic evidence is in `evidence/canonical/`; old published
states, including `dos-semantic-oracle-v1`, remain reproducible through Git.

## Build and validation

Python 3.10+, Capstone 5.x, and the hash-pinned period toolchain in
`layout/toolchain.json` are required for historical verification. Original game
assets remain local and ignored in `assets/`, with identities in
`layout/oracle.lock.json`. Compiler binaries are local prerequisites under
`C:\tools`; none are included in Git.

```powershell
python tools/validate.py
python tools/canonical_behavior.py --count 16 --out build/behavior/current
python dos/build.py --jobs 8 --link
python portable/build.py --out build/portable-sdl3
build/portable-sdl3/simant-canonical.exe
```

The behavior runner compiles current canonical whole TUs and compares them with
original DOS execution in isolated VMs. It corroborates full static semantic
reviews; finite passing cases alone cannot establish semantic completeness.
See [behavioral validation](docs/behavioral-proof.md) for dependencies and scope.

Native build outputs must be fresh. See [portable commands and prerequisites](portable/README.md)
and the current suites under `portable/tests/`. The verified local executable for
the current source is `build/portable-callback-current/simant-canonical.exe`.

## Reconstruction work

```powershell
python tools/context.py FUNCTION
# Draft the complete module in build/workers/NAME/.
python tools/search.py FUNCTION build/workers/NAME/module.c
python tools/promote.py build/workers/NAME/module.c --module UNIT:SEG --claim FUNCTION --verify-only
python tools/promote.py build/workers/NAME/module.c --module UNIT:SEG --claim FUNCTION
python tools/validate.py
```

`promote.py` is the sole canonical writer. Exact acceptance checks full extents,
symbolic fixups, relocations, private data and accepted peers. Similarity is never
acceptance. Reviewed semantic publications additionally retain complete static
receipts and source mutation controls. Unknown storage and layout stay explicit.

The [compiler rules](docs/codegen-rules.md), [translation-unit evidence](docs/tu-evidence.md),
[toolchain fingerprint](docs/toolchain-fingerprint.md), [executable format](docs/exe-format.md)
and [cross-version naming policy](docs/cross-version.md) describe the historical
evidence. Build output and research drafts belong in ignored `build/`; Git history
preserves retired workflows.
