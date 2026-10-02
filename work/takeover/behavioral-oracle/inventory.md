# Behavioral debt inventory (diagnostic only)

This report does not claim any function EXACT or BEHAVIOR_EXACT. All 29 remain UNRESOLVED until the required proof is recorded.

Source main: `54cb824d19c2f897ab17c8b163a954121d4e4843`; manifest SHA-256 `c2850fb5d252bd490bb9d0d2994e1463b25a5e6a4f187ed4f4730dcf91e2f4fd`.
Known function target bytes: 15039; unresolved game code: 15355; unresolved game data: 129.
The additional 316 code-span bytes are outside the known open functions and remain separate historical debt.

| Function | Category | Target/candidate | Skeleton / CFG | Residue reading | Proposed closure |
|---|---|---:|---|---|---|
| f_0250_1018 | rendering | 646/648 | MISMATCH / MATCH | mixed / unlocalized | BEHAVIOR_EXACT after contract-specific differential pass |
| f_0250_129E | rendering | 264/265 | MATCH / MATCH | apparently register-allocation residue | BEHAVIOR_EXACT after contract-specific differential pass |
| DrawBalloons | rendering | 1060/1053 | MISMATCH / MATCH | mixed / unlocalized | BEHAVIOR_EXACT after contract-specific differential pass |
| SpiderScan | core simulation | 392/389 | MISMATCH / MATCH | apparently local/dead initialization residue | BEHAVIOR_EXACT after differential pass |
| LessonDone | tutorial/support | 723/727 | MISMATCH / MISMATCH | structural / shared-tail residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_171C_09CC | memory infrastructure | 144/146 | MISMATCH / MATCH | mixed / dataflow residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_171C_0ADC | memory infrastructure | 262/260 | MISMATCH / MATCH | mixed / dataflow residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_171C_0FBC | memory infrastructure | 566/568 | MISMATCH / MISMATCH | width/type and control residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_171C_0CF4 | memory infrastructure | 490/490 | MATCH / MATCH | apparently stack-home allocation residue | BEHAVIOR_EXACT after contract-specific differential pass |
| FindIndex | database/resource infrastructure | 267/267 | MISMATCH / MISMATCH | control-flow/source lowering residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_1C62_0415 | UI | 649/653 | MISMATCH / MATCH | mixed / compare operand lowering | BEHAVIOR_EXACT after contract-specific differential pass |
| f_1E57_038E | clipping | 997/985 | MISMATCH / MISMATCH | structural / dataflow residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_20E8_0903 | windowing | 286/280 | MISMATCH / MATCH | apparently expression/addressing lowering | BEHAVIOR_EXACT after contract-specific differential pass |
| win_UnlockWin | windowing | 386/390 | MISMATCH / MATCH | apparently expression/addressing lowering | BEHAVIOR_EXACT after contract-specific differential pass |
| f_23E6_0000 | UI | 159/156 | MISMATCH / MATCH | unknown local lifetime/CSE residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_2505_0453 | windowing | 132/124 | MISMATCH / MATCH | width/type and home residue | BEHAVIOR_EXACT after contract-specific differential pass |
| win_DrawBitMap | rendering | 663/675 | MISMATCH / MISMATCH | structural / call-flow residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_2815_0165 | audio | 232/246 | MISMATCH / MATCH | width/type and pointer-lowering residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_284A_0138 | audio | 25/25 | MISMATCH / MATCH | expression/byte-lane residue | BEHAVIOR_EXACT after contract-specific differential pass |
| f_29D6_000A | audio | 120/116 | MISMATCH / MATCH | expression/CSE residue | BEHAVIOR_EXACT after contract-specific differential pass |
| o10_35F5_0384 | UI | 1759/1746 | MISMATCH / MISMATCH | structural menu-lowering residue | BEHAVIOR_EXACT after contract-specific differential pass |
| DrawMapCursor | rendering | 205/210 | MISMATCH / MATCH | expression evaluation-order residue | BEHAVIOR_EXACT after contract-specific differential pass |
| InvertPatch | rendering | 261/260 | MISMATCH / MATCH | expression evaluation-order residue | BEHAVIOR_EXACT after contract-specific differential pass |
| o15_384C_0239 | UI | 326/326 | MATCH / MATCH | apparently stack-home allocation residue | BEHAVIOR_EXACT after contract-specific differential pass |
| win_PrintStyleTextInRect | rendering | 1039/1035 | MISMATCH / MATCH | apparently stack-home allocation residue | BEHAVIOR_EXACT after contract-specific differential pass |
| DisplayCard | UI | 1457/1457 | MISMATCH / MATCH | apparently compare lowering residue | BEHAVIOR_EXACT after contract-specific differential pass |
| drawHistGraph | rendering | 732/714 | MISMATCH / MISMATCH | structural plus stack-home residue | BEHAVIOR_EXACT after contract-specific differential pass |
| o25_3BA4_1035 | gameplay support | 281/281 | MATCH / MATCH | apparently compiler register/home residue | BEHAVIOR_EXACT after differential pass |
| o25_3BA4_1686 | core simulation | 516/520 | MISMATCH / MISMATCH | mixed / source-control-flow residue | BEHAVIOR_EXACT only after source reconciliation and exhaustive differential pass |

## Simulation oracle boundaries

The JSON contains explicit contracts for SpiderScan, o25_3BA4_1035, and o25_3BA4_1686. Each has zero recorded oracle invocations and remains UNRESOLVED. A normalized instruction match or source review is not behavioral proof.

## Evidence limits

The normalized CFG and residue are diagnostic readings from the retained hard-tail report. Exact-name Win16 evidence is joined only when present; absence of a pair is reported as such and is not interpreted as semantic disagreement. Negative-search references are retained from the seed catalog without deleting or reclassifying them.
