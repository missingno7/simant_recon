# DOS semantic-oracle checkpoint readiness

**Ready:** YES

| Proof category | Functions |
|---|---:|
| EXACT | 1611 |
| BEHAVIOR_EXACT | 29 |
| UNRESOLVED | 0 |

Historical EXACT detail: {'C_functions': 1244, 'ASM_functions': 367, 'C_bytes': 237521, 'ASM_bytes': 50441}; behavior cases: {'directed': 336944, 'randomized': 196441, 'total': 533385} across 14 suites.
Game function inventory: 1640; registry rows: 29.
Oracle/hybrid SHA-256: `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11` / `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`; equal: `True`.
Historical code debt: 15355 bytes (15039 in open function extents; 316 outside those extents, with 316 bytes in root-reviewed gap contracts). Data debt: 113 bytes in 8 explicit spans (110 literal bytes plus section-tail overlap 3).
RTLink debt: 17001 bytes, tracked separately.

## Residual proof debt

The report distinguishes historical code/data identity from behavioral closure. RTLink debt is a separate proof level and does not affect the game-semantic category counts.
