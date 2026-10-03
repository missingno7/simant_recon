# Whole-program state provenance correction v2

> Diagnostic only. No state owner is wired into the native program.

Input primitive-view plan SHA-256: `d50da60020111161531d3ea302a71d1fd05c1605e3e2c96123357dc2197fb106`.
Frozen manifest SHA-256: `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`.

## Classification

- Candidate groups: 497
- ASM initializer candidates: 13
- Exact-public alias candidates: 17
- Validated integer FAR_BSS owner candidates: 87 (1550 bytes)
- Previous partial-link unresolveds removed: 94
- Provenance regression controls: passed.

The prior 131-owner scratch-BSS count is withdrawn by this report. Only integer FAR_BSS common extents with matching registered gaps and source evidence are emitted. Initialized DATA and CODE addresses cannot create BSS owners. Pointers, incomplete arrays, conflicting names, and unverified sizes remain unresolved.

## Flagged regressions

| Address | Candidate | Result | Evidence |
|---|---|---|---|
| `55B3:3DB2` | `g_3DB2` | `initialized-asm-data-candidate` | exact accepted MASM OMF PUBLIC and manifest _DATA placement; source directive supplies a literal initializer |
| `55B3:3DB4` | `g_3DB4` | `initialized-asm-data-candidate` | exact accepted MASM OMF PUBLIC and manifest _DATA placement; source directive supplies a literal initializer |
| `55B3:3DDE` | `g_3DDE` | `initialized-asm-data-candidate` | exact accepted MASM OMF PUBLIC and manifest _DATA placement; source directive supplies a literal initializer |
| `1B73:0006` | `fd_1B73_0006` | `excluded-code-address` | candidate address lies inside an accepted code extent; no state storage may be emitted |
| `55B3:19BE` | `fd_55B3_19BE` | `exact-omf-public-alias-rename-candidate` | far registered view and near C PUBLIC resolve to the same placed address; exact OMF object hash and PUBLIC offset prove one initialized owner |

## Initialized ASM candidates

| Address | Name | Directive | Initializer |
|---|---|---|---|
| `55B3:3D20` | `g_3D20` | `db` (1 bytes) | `128 dup (0)` |
| `55B3:3DA0` | `g_3DA0` | `dw` (2 bytes) | `0` |
| `55B3:3DA4` | `g_3DA4` | `dd` (4 bytes) | `0` |
| `55B3:3DA8` | `g_3DA8` | `dw` (2 bytes) | `0` |
| `55B3:3DB2` | `g_3DB2` | `dw` (2 bytes) | `640` |
| `55B3:3DB4` | `g_3DB4` | `dw` (2 bytes) | `350` |
| `55B3:3DDC` | `g_3DDC` | `dw` (2 bytes) | `0` |
| `55B3:3DDE` | `g_3DDE` | `dw` (2 bytes) | `8` |
| `55B3:3DE0` | `g_3DE0` | `db` (1 bytes) | `0Fh` |
| `55B3:3DE2` | `g_3DE2` | `db` (1 bytes) | `0` |
| `55B3:3DE4` | `g_3DE4` | `db` (1 bytes) | `0` |
| `55B3:3DE6` | `fd_55B3_3DE6` | `dw` (2 bytes) | `0` |
| `55B3:3DE8` | `fd_55B3_3DE8` | `dw` (2 bytes) | `0` |

## Initialized pointer table aliases

| Address | Alias expression | Owner | Declaration handling |
|---|---|---|---|
| `55B3:1CD8` | `fd_55B3_1CD4[1]` | `fd_55B3_1CD4` | Remove standalone declaration of `fd_55B3_1CD8` |
| `55B3:1CDC` | `fd_55B3_1CD4[2]` | `fd_55B3_1CD4` | Remove standalone declaration of `fd_55B3_1CDC` |

## Pointer common debt

- Pointer groups reviewed and withheld from byte-owner emission: 34
- Groups with one scalar pointer view and a consistent four-byte FAR_BSS gap: 2
- No pointer variable is emitted by this scratch owner TU. The report retains source declarations, pointer-level consistency, and FAR_BSS gap evidence for owner-specific host-pointer and address-arithmetic review.


## Decision counts

- 10: `exact-omf-public-alias-rename-candidate`
- 1: `excluded-code-address`
- 13: `initialized-asm-data-candidate`
- 44: `initialized-data-address`
- 4: `initialized-data-address-needs-symbol-review`
- 2: `initialized-pointer-array-interior-alias-candidate`
- 18: `unresolved-no-historical-storage-provenance`
- 87: `validated-farbss-integer-common-owner-candidate`
- 318: `validated-farbss-range-owner-unresolved`

Exact OMF module/source/object identities, placements, candidate groups, and unresolved explanations are recorded in the JSON report. Scratch owner source: `build/workers/whole_program/unprovided_state_provenance_v2.c` (SHA-256 `2050e95967199dce5753666b8877ed3aa86475a1e683e7ab81d58e493b80e858`); it is not selected by the whole-program build. The previous plan and its scratch object are retained as historical diagnostics, not accepted owners.
