# RandWorld state projection

This table records the source-to-native fields used by the current
`sim_worldgen_rand_world` implementation. It is an implementation map, not a
claim of DOS differential closure. The source is `src/S08/m35F5.c`, chiefly
`RandWorld`, `PlaceBlackQueen`, `PlaceRedQueen`, `InitYelloAnt`, and `AddFood`.

| DOS source state / operation | Native projection | Notes |
| --- | --- | --- |
| `SetSRandSeed(seed)` | `SimRng.s_state` | C runtime `rand` stream is preserved. |
| `InitSpider` | `SimSpiderState` | Called before `MakeMap`; InitSpider-owned fields only. |
| `MakeMap(mapWidth,mapKind)` | `SimGameWorld.tiles.surface`, ant-lion/pillar/sow and overlay fields | `sim_terrain_build`; resource intent is data, not a host callback. |
| `MapA/B/R` | `tiles.surface/nest_b/nest_r` | x-major logical indexing. |
| `ExitMapB/R` | `exit_b/exit_r` | Includes the initial outer-wall marker. |
| `LifeA/B/R` | `life_a/life_b/life_r` | Surface life distribution is generated before list reconstruction. |
| `PherMapA/BN/BT/RN/RT`, `fd_3E1D_D89F` | `pheromone_a/b_nest/b_trail/r_nest/r_trail/aux` | Explicitly cleared in RandWorld. |
| `HoleMapB/R` | `hole_b/hole_r` | Cleared before source MakeNewHole calls. |
| `SRand*` calls during distributions and queen placement | `SimRng.s_state` | Order is preserved by direct calls to the native RNG and nest helpers. |
| `DigTileB/R`, `MakeNewHoleB/R`, `DigMyTile` | `SimNestRuntime`, nest maps/life/exit maps, `SimNestTrace` | Uses the shared source-derived operations from `nest.c`. |
| `fd_50F6_1068`, `1082`, `0224`, `10B2`, `10C0` | `nest_runtime.dug_b_x_sum/dug_b_y_sum/dug_b_count/dug_b_x_average/dug_b_y_average` | Reset after starting-hole creation; optional DigOut accumulates after reset. |
| `fd_50F6_108E`, `10A2`, `TilesDugR`, `0200`, `020E` | `nest_runtime.dug_r_x_sum/dug_r_y_sum/dug_r_count/dug_r_x_average/dug_r_y_average` | Same reset boundary as black excavation state. |
| `fd_50F6_0242` | `source_counter_0242` | Reset to `0x40` before optional excavation. |
| `fd_50F6_035E`, `fd_50F6_036C` | `queens_black`, `queens_red` | Reset after holes; queen helpers increment them. |
| RandYard assignments `fd_50F6_105E`, `0214`, `0204`, `0228`, `0478`, `0504`, `fd_3D57_0C44`, `0C18`, `0C16`, `0C14` | `player_update_code`, `source_state_0214/0204/0228/0478/0504/0c44/0c18`, `health_force_full`, `source_state_0c14` | Reset to the exact source values before seed-table generation; `105E` is -1, the rest zero. `health_force_full` retains the source word width. |
| `InitYelloAnt`: `fd_50F6_049A=0`, `fd_3D57_0C22=0xfd`, conditional `fd_50F6_104E=0` and `fd_3D57_07BE=-1` | `source_state_049a/0c22/104e/07be` | Conditional reset and preserved nonzero branch are represented in the native snapshot fixture. |
| `BuildAntListA`, `ClearListB/R`, queen `AddAntTo*List` | `ants_a/b/r` | Surface list is rebuilt from LifeA; B/R lists are reset before queens. |
| `MePlane/MeLocX/MeLocY/fd_50F6_0496/fd_50F6_04C2` | `current_ant_plane`, `me_x/y/direction/type` | `fd_50F6_0496` is direction. `fd_50F6_04C4` is an unrelated preserved word and is tracked raw. `SetMyLife` handles normal placement. |
| `o22_39C7_07FD(plane,x,y)` | `SIM_WORLDGEN_PLAYER_SELECTION` event | Host/UI consumes this ordered request. |
| `FoodB/FoodR` | `food_black/food_red` | Reset at new world creation. |
| `fd_50F6_1040` | `food_added_terrain` | Number of accepted surface-food tile modifications, not FoodB. |
| `HealthB/HealthR` | `health_black/health_red` | Set to 100 after player and food setup. |
| `Cycle` | `cycle` | Reset to zero. |
| `ClearHistory(0)` | `SimSetupState` | Applied before population counting. |
| `CountAnts()` | `ants_by_type`, black/red population bins and totals, `SimPopulationEffects` | Native `population.c` emits music/report requests and reproduces conditional RNG use. |
| `InvalEuMap(0,0,screenWidth,screenHeight)` | `dirty_map` plus `SIM_WORLDGEN_MAP_INVALIDATE` | Native bounds are logical map tiles (128×64), not DOS pixel dimensions. |
| `fd_50F6_0508`, `fd_50F6_0596`, `fd_50F6_06A6`, `fd_50F6_072E` | `map_view_x/y`, `map_focus[0..2]` | RandWorld defaults A=(64,32), B=(32,1), R=(32,1); RandYard then centers the active plane on the player. |
| `fd_50F6_0472`, `fd_50F6_09FA`, `fd_50F6_0A00` | `source_counter_0472`, `source_counter_09fa`, `source_counter_0a00` | Reset to zero after food/health setup; widths follow declarations in S08 source. |

## Differential status and limits

The direct original-DOS `RandWorld` comparison is retained under
`portable/tests/worldgen/evidence/`. Twelve fresh oracle/native invocations
passed for scenarios 0 and 1, seeds `5a31`, `534d`, `7121`, `1990`, `8000`,
and `ffff`, with black/red size 1/1, terrain selector 0, and map arguments
11/8. The compared projection includes all listed map/life/exit/pheromone
planes, nest holes, active and inactive ant-list storage, population bins,
food/health/cycle values, camera positions, terrain/lion/sow/pillar state,
the InitYelloAnt globals, callback order and arguments, and the exact
post-call private S-RNG state read by the original `GetSRandSeed` function.

The caller prestate is the default RandYard path after `ClrArrays` and the
RandYard scalar assignments, with preserved inactive ant-list coordinates and
the conditional InitYelloAnt globals initialized to exercise their nonzero
branch. The original sine table is supplied through a test-owned far arena and
the real DOS far pointer. The player-selection request and map invalidation are
explicit host boundaries. This is bounded evidence for the listed domain, not
a universal proof across nest sizes, terrain selectors, scenarios, or resource
providers.

`SimNestRuntime` counters outside the serialized excavation aggregate and
non-default nest-size DigOut paths still require separate mapping/differential
coverage. `sim_worldgen_start_new_game_native` requires actual resource-size
and object-rectangle services for `initControls`; absent services return
unsupported.

