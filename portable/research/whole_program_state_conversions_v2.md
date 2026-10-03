# Whole-program state conversion proposal v2

> Diagnostic conversion packet only. It does not edit frozen sources, alter the whole-program generator, or wire production state.

## Identity

- Provenance baseline: [whole_program_unprovided_owners_v2.json](whole_program_unprovided_owners_v2.json), SHA-256 `ff91c70e7d1458816e9a10d69945e2d87d0510fd5ebeb4bf8c391028f29229ae`.
- Converter: [unprovided_state_v2.py](../whole_program/conversions/unprovided_state_v2.py), SHA-256 `8b6a30ad94d00f912091a3d5f1132ad05725932326982bc39f5049af0ab8477e`.
- Typed owner TU (local scratch output): `build/workers/whole_program/conversion_v2/typed_owners.c`, SHA-256 `3edf7ac51e71da9c0f10ad538178416dfafe6ca14271bcc65ddb521c2005244d`.
- Conversion instructions: local scratch `build/workers/whole_program/conversion_v2/conversions.json`, SHA-256 `1ef7f703076b1bce0f33cd9d0e5789911d4313aa3001c0fcb258563b7e9c0d8c`.
- Frozen manifest SHA-256: `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`.
- Symbol inventory SHA-256: `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`.
- Current whole-program integration snapshot recorded by the latest independent compile probe: migration SHA-256 `5521f35d8ebf0f8b29b695e242a3196d8c9a1ad91913799256311e0f464b9c8f`; generator SHA-256 `2881c4f4b87f948cf944047a06bba757d27171055edabdc04956c50adcb40827`. The provenance report preserves its own earlier migration identity as documentary run input; source/layout/object pins are the fixed ownership evidence.

## Conversion inventory

- Seventeen symbol rename mappings: nine exact OMF/placement aliases for already compiled initialized-data owners, `fd_55B3_19BE` to the already initialized `g_19BE`, and seven same-address FAR_BSS aliases.
- The pointer-table owner is an initialized five-element `char far * far` array at `55B3:1CD4` in the exact `root:15F8` object. In `src/S20/m39F1.c`, the scalar owner declaration is removed and its use for the database name becomes `[0]`. The two interior aliases become `[1]` and `[2]`; their standalone scalar declarations are removed. The message printf calls retain their respective indexed entries.
- Eighty-seven zero-initialized typed integer owners cover 1,550 source-proven FAR_BSS bytes. Each emitted owner uses the report’s fixed-width source type and explicit source array shape. The emitter checks view-width agreement, shape agreement, literal dimension product, and exact equality to the candidate byte extent; unsupported types and shapes fail closed.
- Thirteen literal initialized ASM candidates are retained separately. They are not emitted as zeroed state. The explicit geometry values include `g_3DB2=640`, `g_3DB4=350`, and `g_3DDE=8`.
- The earlier exploratory 79-owner count was not preserved with its exact candidate list, so this packet does not claim which eight names changed. The current frozen provenance report individually records all 87 candidates and their evidence.

## Verification and limits

- Positive and negative converter controls pass. Identifier rewrites leave comments and string literals untouched. Pointer-table declarations are removed exactly; missing declarations fail closed. The real manifest-pinned consumer rewrite confirms both message lookups use `[1]`/`[2]` and `f_205F_0004` receives `[0]`.
- Independent actual-TU compile probe: [probe_source_table_compile_v2.py](../whole_program/conversions/probe_source_table_compile_v2.py) compiles the current generated S20:m39F1 consumer and root:m15F8 provider against typed `source_tables.h`; `nm` confirms the consumer references and the provider defines canonical `fd_55B3_1CD4`. The receipt validates all 18 immutable provenance input checks while treating migration identity as documentary. Receipt: `build/workers/whole_program/source_table_compile_v2/report.json`, SHA-256 `b75483b04948f21bd97696b0293c7a2d79c046ded5657f8621781a9d8832d09d` (local scratch output).
- The typed owner TU compiles with GCC `-std=c11 -fsigned-char -fno-builtin -fno-common -Wall -Werror`.
- The provenance scratch partial-link diagnostic reduced unresolved names from 717 to 623. This is an ownership/link diagnostic from its pinned baseline, not a rerun against the later integration migration and not behavior or production acceptance.
- The provenance inventory still leaves 318 FAR_BSS ranges unresolved, along with pointer/struct/runtime/extent ownership debt. This packet does not close those debts or select any production state.
