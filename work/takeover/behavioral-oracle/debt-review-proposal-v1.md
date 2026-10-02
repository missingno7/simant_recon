# Freeze debt review proposal (not approved)

This packet proposes explicit checkpoint dispositions for the 316 code bytes outside the 29 known open-function extents and all 113 residual data/layout bytes. Every status is pending root review. It changes no source, extent, EXACT claim, behavior registration, or accepted-data count.

The code bundle at `code-gap-review-proposal-v1.json` accounts for 316 pairwise-disjoint bytes: seven unowned code-shaped/layout spans (54 bytes), 70 current-provenance `LINK_FILL` ranges inside root/overlay game-code regions (246 bytes), and the 16-byte root text-prefix candidate. The wrapper reproduction has 18 matching bounded cases, but three wrappers remain supplemental semantic evidence only; exact-target experiments that regress accepted peers did not become claims. The empty far-return candidates and code-shaped entries still lack established DOS call/address-taking paths, so the packet does not label them dead.

The data bundle at `data-debt-disposition-proposal-v1.json` inventories eight literal spans (110 bytes) plus the three-byte S27/common-tail overlap. The 2100 masks/look-up table and 68AC edge masks are meaningful graphics data whose historical defining owners remain unknown. The 5A96 span is partly typed shared UI state; 60B0 is a relocated timer-compatible record without an established registration path. Other zero-valued spans remain unknown or alignment/runtime candidates, never “harmless” based on their contents.

Each literal byte range was compared directly with `assets/SIMANT.EXE` SHA-256 `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`. One source pin in the existing data-debt audit is stale: its `build/link/provenance.json` hash is `658a3e6862a10ba43ddcc8a0df5c56668616d794a8d59c7d8e939356922a010a`, while the current provenance hash is `1e61bead20694234d10d1bd35b2a23eac8c55c65e546c362f1c679a42ab3a664`. Reconcile/regenerate that audit before a freeze decision.

The current `memory-final-20261002/failure-paths` producer/report/index hashes agree. Its seven probes are explicitly `SUPPLEMENTAL_DIAGNOSTIC_ONLY`: three returned differential controls, two real helper return comparisons, one paired terminal `Punt` boundary, and one omit-`Punt` sensitivity mutant. The bounded Punt observer stops before a return; it supplies no fabricated null result and does not change any accepted count.

## Pins

| Artifact | SHA-256 |
|---|---|
| `debt-review-proposal-v1.json` | `49f9480559485056966d27999070594c7eac01df1cbc6b9dca002d28319bed26` |
| `code-gap-review-proposal-v1.json` | `7430bf477d3ccc30e35d8b1cfad9cae37ba2d3f45908333a5b14f491da9520aa` |
| `data-debt-disposition-proposal-v1.json` | `f0880ce218973e414afd54818146d89bcae460a2051d8491d7da090a0b98e74c` |
| original code-gap scan | `6efb452497c63a31cb7258ba010288b311376de36e429059f71030c5de2a9a97` |
| supplemental wrapper report v2 | `3f8b87bb6bcfe7f980680b2fc7e4ce7d5c075bc9d5413a77650fc5819d6d798d` |
| memory failure-path report | `ad061b0780ee9fc05fadfe429cf66bf332fa8c8be54f9f34b1a592b6c1134c7e` |
| memory failure-path producer | `0ebfaeb824f65c6f94b89455686ab1185433b1cd41a2a7ac2ba5a93e6220feaa` |
| memory failure-path index | `9ec00bddb9bf37f2676a87b9525b971ca94f4e34ad3b0082c9495641398822a0` |

Root review must decide whether these dispositions are sufficient for the freeze packet. Nothing here asserts zero historical ownership debt.
