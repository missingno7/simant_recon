# Behavioral oracle checkpoint

**Snapshot date:** 2026-10-02. Historical inventory.json / inventory.md remains the unchanged 2026-10-01 baseline.

The separate behavior registry contains **29 BEHAVIOR_EXACT registrations and 0 UNRESOLVED functions**. The historical manifest retains **1,611 known EXACT game functions**. These counts represent different proof categories; behavioral closure does not confer byte ownership.

Registered behavioral contracts:

- f_0250_1018
- f_0250_129E
- DrawBalloons
- SpiderScan
- LessonDone
- f_171C_09CC
- f_171C_0ADC
- f_171C_0FBC
- f_171C_0CF4
- FindIndex
- f_1C62_0415
- f_1E57_038E
- f_20E8_0903
- win_UnlockWin
- f_23E6_0000
- f_2505_0453
- win_DrawBitMap
- f_2815_0165
- f_284A_0138
- f_29D6_000A
- o10_35F5_0384
- DrawMapCursor
- InvertPatch
- o15_384C_0239
- win_PrintStyleTextInRect
- DisplayCard
- drawHistGraph
- o25_3BA4_1035
- o25_3BA4_1686

Remaining behavioral targets:


The three prioritized simulation functions—SpiderScan, EnterNest (o25_3BA4_1035), and GetMyRandDirs (o25_3BA4_1686)—have registered oracle-backed contracts. Every claim is limited to its recorded input/state domain and observable boundary.

Historical code ownership debt remains **15,355 bytes**: 15,039 bytes in the 29 baseline target functions plus 316 bytes outside those extents. The separate gap audit does not infer dead code from missing references. Historical data debt remains **113 bytes**. See data-debt.md and debt-audit/ for values, references and explicit ownership limitations. The exact 16-byte low-nibble table promotion is independent of behavioral closure.

RTLink manager/linker debt remains **17,001 bytes**, a separate proof level. This tree is the dos-semantic-oracle-v1 checkpoint; portable development proceeds on codex/portable-sdl3.

Registry packets under evidence/behavior/functions/ are authoritative. Superseded, failed-gate and exploratory packets remain diagnostic even if their local schema contains a proposed status. A passing worker run alone grants no acceptance.

The approved formatter certificate and supplemental proof graph retain raw private cursor differences and bound their normalization to actual invocation-stack buffers. Historical EXACT sources and gates are unchanged.

[Freeze report](../../../docs/dos-semantic-oracle-v1.md) records the validation receipts and complete debt dispositions.
