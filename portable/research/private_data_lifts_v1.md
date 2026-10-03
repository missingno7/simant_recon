# Source-owned private DATA lifts (diagnostic)

This audit identifies four initialized DOS words that have a real C storage
owner and are referenced through `fd_55B3_*` declarations in other modules.
It proposes a native source conversion that exposes or reuses that owner. It
does not change historical sources, OMF/layout records, or acceptance status.

| DOS address | C storage owner | Consumers | Initial DOS bytes | Basis |
|---|---|---|---|---|
| `55B3:2996` | `src/S12/m384C.c`, `static int g_2996 = 0` | `src/S04/m35F5.c` | `00 00` | Manifest `_DATA` offset +8, exact word matches initializer |
| `55B3:38A0` | `src/root/m19DC.c`, `int g_38A0 = 0` | `src/root/m15F8.c` | `00 00` | Manifest `_DATA` offset +4, existing external owner |
| `55B3:604C` | `src/root/m1FD2.c`, `int g_604C = 0` | `src/S10/m35F5.c` | `00 00` | Manifest `_DATA` offset +102, existing external owner |
| `55B3:610A` | `src/S20/m39F1.c`, `static int g_610A = -1` | `src/S15/m384C.c`, `src/root/m00DF.c` | `FF FF` | Manifest `_DATA` offset +72, exact word matches initializer |

The native adapter preserves both private owner initializers and makes those
two scalar definitions externally linkable. For already public owners it
reuses the existing definition. Consumer rewrites are token-aware and skip
comments and string/character literals. No duplicate zero storage is emitted.

The remaining nearby views were reviewed but not admitted to this scalar plan:

* `55B3:2A36` and `55B3:2A3A` are 32-bit DOS far-pointer values exposed as
  `long`/character-pointer views; native pointer width and aliasing need a
  typed conversion before they can share an owner.
* `55B3:2A42` is an array/`Point` view and needs a strict-alias-safe shared
  representation.
* `55B3:6054` has `MenuData *`, `char ***`, and `long *` views; these are
  incompatible pointer views and need a typed owner contract.
* `55B3:5AA0` has no source-owned initializer/placement relationship established
  by this pass. It remains unresolved.
* ASM-owned words, audio state, code-address entries, and the existing 43C
  pointer-table plan are outside this packet.

The probe at `portable/tests/whole_program/evidence/private_data_lifts_v1/`
records current source/layout/oracle pins and positive/negative controls. Its
claim is limited to source ownership and native conversion viability; it is
not a historical reconstruction or behavioral-equivalence claim.
