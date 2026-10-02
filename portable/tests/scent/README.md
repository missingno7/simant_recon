# Pheromone child operations

`portable/game/simulation/scent.c` ports the five pure pheromone loops from
`src/root/m1496.c`: `ColonySmellBN`, `ColonySmellRN`, `ColonySmellBT`,
`ColonySmellRT`, and `SmoothAlarm`. The implementation retains the source's
x-major outer loop and y-major inner loop, byte-valued reads/writes, and the
strict `< 8` trail cutoff.

The source arrays map as follows:

| DOS array | Native state |
| --- | --- |
| `PherMapA` | `SimGameWorld.pheromone_a` |
| `PherMapBN` / `PherMapBT` | `pheromone_b_nest` / `pheromone_b_trail` |
| `PherMapRN` / `PherMapRT` | `pheromone_r_nest` / `pheromone_r_trail` |
| `fd_3E1D_C89F` (`SmoothAlarm` scratch) | `SimScentState.smooth_alarm_work` |
| `fd_3E1D_D89F` | `SimGameWorld.pheromone_aux`, preserved by these operations |

The original `DoSmells` dispatcher also compacts ant lists, calls `FullCount`,
updates history data, and may draw the history window. This suite covers the
five direct pheromone child functions only; it makes no full-dispatch claim.
Run `python portable/tests/scent/run_dos_diff.py` for the pinned original-DOS
differential. The retained 360-case report, runner, and harness inputs are in
`evidence/`.
