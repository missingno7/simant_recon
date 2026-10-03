# Unprovided whole-program primitive state plan

> Scratch lane only. It does not establish source behavior or production state admission.

Migration SHA-256: `cbe81f3ed0fea207dd48050c5bf51d774cd0e8ab9caac8e0352e87921f0f4345`; frozen symbols SHA-256: `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`.

## Results

- Unprovided global-state names: 514
- Address groups: 497
- Safe registered alias rename candidates: 16 names
- Scratch BSS owner candidates: 147
- Unresolved groups/names: 341
- Planner controls: positive and negative controls passed.

Registered aliases point to an already compiled owner, so they produce a lexical rename proposal rather than a duplicate object. Scratch BSS allocations contain no initializer because initial values are not established by declarations; C zero initialization is an unavoidable implementation property, not an oracle claim. Existing provider names are never emitted again.

## Alias rename candidates

| Address | Missing alias | Existing owner | Extent bytes | Width |
|---|---|---|---:|---:|
| `3D57:0000` | `fd_3D57_0000` | `Dx8` | 8 | 1 |
| `3D57:0008` | `fd_3D57_0008` | `Dy8` | 8 | 1 |
| `3D57:0224` | `fd_3D57_0224` | `HoleMapB` | 64 | 1 |
| `3D57:0264` | `fd_3D57_0264` | `HoleMapR` | 64 | 1 |
| `3E1D:0180` | `fd_3E1D_0180` | `MapA` | 8192 | 1 |
| `3E1D:2180` | `fd_3E1D_2180` | `MapB` | 4096 | 1 |
| `3E1D:4180` | `fd_3E1D_4180` | `ExitMapB` | 4096 | 1 |
| `3E1D:8180` | `fd_3E1D_8180` | `LifeB` | 4096 | 1 |
| `3E1D:D09F` | `fd_3E1D_D09F` | `PherMapA` | 2048 | 1 |

## Scratch BSS candidates

| Address | Owner | Extent bytes | Width | Source views |
|---|---|---:|---:|---|
| `1B73:0006` | `fd_1B73_0006` | 2 | 2 | 1 modules |
| `50F6:0204` | `fd_50F6_0204` | 4 | 4 | 3 modules |
| `50F6:0214` | `fd_50F6_0214` | 4 | 4 | 3 modules |
| `50F6:0354` | `fd_50F6_0354` | 2 | 2 | 4 modules |
| `50F6:0364` | `fd_50F6_0364` | 2 | 2 | 1 modules |
| `50F6:036E` | `fd_50F6_036E` | 2 | 2 | 1 modules |
| `50F6:037A` | `fd_50F6_037A` | 2 | 2 | 1 modules |
| `50F6:0402` | `fd_50F6_0402` | 2 | 2 | 1 modules |
| `50F6:0472` | `fd_50F6_0472` | 4 | 4 | 3 modules |
| `50F6:047C` | `MeLocX` | 2 | 2 | 14 modules |
| `50F6:048A` | `MeLocY` | 2 | 2 | 13 modules |
| `50F6:048C` | `MePlane` | 2 | 2 | 16 modules |
| `50F6:048E` | `fd_50F6_048E` | 2 | 2 | 1 modules |
| `50F6:0496` | `fd_50F6_0496` | 2 | 2 | 9 modules |
| `50F6:04C0` | `fd_50F6_04C0` | 2 | 2 | 1 modules |
| `50F6:04C2` | `fd_50F6_04C2` | 2 | 2 | 14 modules |
| `50F6:050C` | `fd_50F6_050C` | 4 | 4 | 1 modules |
| `50F6:059A` | `fd_50F6_059A` | 4 | 4 | 1 modules |
| `50F6:0620` | `fd_50F6_0620` | 4 | 4 | 1 modules |
| `50F6:0732` | `fd_50F6_0732` | 4 | 4 | 1 modules |
| `50F6:07C4` | `fd_50F6_07C4` | 4 | 4 | 1 modules |
| `50F6:09FC` | `fd_50F6_09FC` | 4 | 2 | 1 modules |
| `50F6:0A06` | `fd_50F6_0A06` | 2 | 2 | 12 modules |
| `50F6:0A9C` | `fd_50F6_0A9C` | 2 | 2 | 2 modules |
| `50F6:0AA6` | `fd_50F6_0AA6` | 2 | 2 | 2 modules |
| `50F6:0ACA` | `fd_50F6_0ACA` | 2 | 2 | 1 modules |
| `50F6:0AD8` | `fd_50F6_0AD8` | 2 | 2 | 1 modules |
| `50F6:0AEA` | `fd_50F6_0AEA` | 2 | 2 | 1 modules |
| `50F6:0B06` | `fd_50F6_0B06` | 2 | 2 | 1 modules |
| `50F6:0B08` | `fd_50F6_0B08` | 2 | 2 | 1 modules |
| `50F6:0B20` | `fd_50F6_0B20` | 2 | 2 | 1 modules |
| `50F6:0C3A` | `fd_50F6_0C3A` | 2 | 2 | 1 modules |
| `50F6:0D68` | `fd_50F6_0D68` | 2 | 2 | 1 modules |
| `50F6:0D6A` | `ListIndexA` | 2 | 2 | 12 modules |
| `50F6:0D6E` | `fd_50F6_0D6E` | 2 | 2 | 1 modules |
| `50F6:0D9A` | `fd_50F6_0D9A` | 2 | 2 | 1 modules |
| `50F6:0DA8` | `ListIndexB` | 2 | 2 | 9 modules |
| `50F6:0EAA` | `ListIndexR` | 2 | 2 | 9 modules |
| `50F6:0EAC` | `fd_50F6_0EAC` | 2 | 2 | 17 modules |
| `50F6:0EB4` | `fd_50F6_0EB4` | 2 | 2 | 1 modules |
| `50F6:0EB6` | `fd_50F6_0EB6` | 64 | 2 | 1 modules |
| `50F6:0EF6` | `fd_50F6_0EF6` | 2 | 2 | 2 modules |
| `50F6:0F06` | `fd_50F6_0F06` | 2 | 2 | 2 modules |
| `50F6:0F10` | `fd_50F6_0F10` | 2 | 2 | 2 modules |
| `50F6:0F18` | `Tindex` | 2 | 2 | 5 modules |
| `50F6:0F24` | `TERRAINset` | 2 | 2 | 13 modules |
| `50F6:0F2E` | `fd_50F6_0F2E` | 2 | 2 | 2 modules |
| `50F6:0F36` | `fd_50F6_0F36` | 2 | 2 | 2 modules |
| `50F6:0F38` | `fd_50F6_0F38` | 2 | 2 | 1 modules |
| `50F6:0F3A` | `DROPdir` | 2 | 2 | 2 modules |
| `50F6:0F3C` | `fd_50F6_0F3C` | 2 | 2 | 1 modules |
| `50F6:0F7A` | `fd_50F6_0F7A` | 2 | 2 | 1 modules |
| `50F6:0FB6` | `fd_50F6_0FB6` | 2 | 2 | 4 modules |
| `50F6:0FC0` | `fd_50F6_0FC0` | 2 | 2 | 1 modules |
| `50F6:0FF8` | `fd_50F6_0FF8` | 2 | 2 | 1 modules |
| `50F6:0FFA` | `fd_50F6_0FFA` | 2 | 2 | 4 modules |
| `50F6:103A` | `fd_50F6_103A` | 2 | 2 | 1 modules |
| `50F6:1046` | `fd_50F6_1046` | 2 | 2 | 1 modules |
| `50F6:104A` | `fd_50F6_104A` | 2 | 2 | 1 modules |
| `50F6:1062` | `fd_50F6_1062` | 2 | 2 | 1 modules |
| `50F6:1064` | `fd_50F6_1064` | 2 | 2 | 1 modules |
| `50F6:106C` | `fd_50F6_106C` | 1 | 1 | 1 modules |
| `50F6:107C` | `fd_50F6_107C` | 2 | 2 | 1 modules |
| `50F6:1092` | `fd_50F6_1092` | 2 | 2 | 1 modules |
| `50F6:10D0` | `fd_50F6_10D0` | 2 | 2 | 2 modules |
| `50F6:10DE` | `fd_50F6_10DE` | 2 | 2 | 5 modules |
| `50F6:10E0` | `fd_50F6_10E0` | 2 | 2 | 5 modules |
| `50F6:1102` | `fd_50F6_1102` | 2 | 2 | 1 modules |
| `50F6:1114` | `fd_50F6_1114` | 1200 | 1 | 1 modules |
| `50F6:15C4` | `fd_50F6_15C4` | 2400 | 2 | 1 modules |
| `50F6:37D2` | `fd_50F6_37D2` | 2 | 2 | 1 modules |
| `50F6:37D4` | `fd_50F6_37D4` | 2 | 2 | 1 modules |
| `50F6:37FA` | `fd_50F6_37FA` | 2 | 2 | 1 modules |
| `50F6:37FC` | `fd_50F6_37FC` | 2 | 2 | 1 modules |
| `50F6:380E` | `triHeight` | 2 | 2 | 1 modules |
| `50F6:3810` | `triWidthL` | 2 | 2 | 1 modules |
| `50F6:3812` | `triWidthR` | 2 | 2 | 1 modules |
| `50F6:3814` | `triWidth` | 2 | 2 | 1 modules |
| `50F6:382E` | `fd_50F6_382E` | 4 | 4 | 1 modules |
| `50F6:383A` | `fd_50F6_383A` | 4 | 4 | 2 modules |
| `50F6:3852` | `fd_50F6_3852` | 2 | 2 | 1 modules |
| `50F6:3854` | `fd_50F6_3854` | 2 | 2 | 2 modules |
| `50F6:3856` | `fd_50F6_3856` | 2 | 2 | 4 modules |
| `50F6:3858` | `fd_50F6_3858` | 2 | 2 | 4 modules |
| `50F6:38B6` | `fd_50F6_38B6` | 2 | 2 | 2 modules |
| `50F6:38C0` | `fd_50F6_38C0` | 2 | 2 | 1 modules |
| `50F6:38CA` | `fd_50F6_38CA` | 30 | 2 | 1 modules |
| `50F6:38E8` | `fd_50F6_38E8` | 34 | 2 | 1 modules |
| `50F6:390A` | `fd_50F6_390A` | 34 | 2 | 1 modules |
| `50F6:3944` | `fd_50F6_3944` | 4 | 4 | 2 modules |
| `50F6:46D0` | `fd_50F6_46D0` | 2 | 2 | 1 modules |
| `50F6:47D4` | `win_numOfGroups` | 2 | 2 | 1 modules |
| `50F6:47D6` | `win_numOfColors` | 2 | 2 | 1 modules |
| `50F6:47D8` | `win_numOfWindows` | 2 | 2 | 2 modules |
| `50F6:4A46` | `fd_50F6_4A46` | 2 | 2 | 1 modules |
| `50F6:4A48` | `fd_50F6_4A48` | 2 | 2 | 1 modules |
| `50F6:4A4A` | `fd_50F6_4A4A` | 2 | 2 | 1 modules |
| `50F6:4A4C` | `fd_50F6_4A4C` | 2 | 2 | 1 modules |
| `50F6:4B14` | `fd_50F6_4B14` | 2 | 2 | 3 modules |
| `50F6:4B16` | `fd_50F6_4B16` | 2 | 2 | 2 modules |
| `50F6:4B2C` | `fd_50F6_4B2C` | 2 | 2 | 1 modules |
| `50F6:4B2E` | `fd_50F6_4B2E` | 2 | 2 | 1 modules |
| `50F6:4B8A` | `fd_50F6_4B8A` | 4 | 4 | 1 modules |
| `55B3:19BE` | `fd_55B3_19BE` | 2 | 2 | 4 modules |
| `55B3:19C0` | `fd_55B3_19C0` | 2 | 2 | 4 modules |
| `55B3:19CA` | `fd_55B3_19CA` | 4 | 4 | 1 modules |
| `55B3:19CE` | `fd_55B3_19CE` | 2 | 2 | 1 modules |
| `55B3:21A4` | `g_21A4` | 1 | 1 | 1 modules |
| `55B3:2996` | `fd_55B3_2996` | 2 | 2 | 1 modules |
| `55B3:360C` | `fd_55B3_360C` | 1 | 1 | 3 modules |
| `55B3:3612` | `fd_55B3_3612` | 2 | 2 | 3 modules |
| `55B3:3614` | `fd_55B3_3614` | 2 | 2 | 1 modules |
| `55B3:38A0` | `fd_55B3_38A0` | 2 | 2 | 1 modules |
| `55B3:3DB2` | `g_3DB2` | 2 | 2 | 22 modules |
| `55B3:3DB4` | `g_3DB4` | 2 | 2 | 8 modules |
| `55B3:3DDC` | `g_3DDC` | 1 | 1 | 7 modules |
| `55B3:3DDE` | `g_3DDE` | 1 | 1 | 9 modules |
| `55B3:3DE6` | `fd_55B3_3DE6` | 2 | 2 | 1 modules |
| `55B3:3DE8` | `fd_55B3_3DE8` | 2 | 2 | 1 modules |
| `55B3:432A` | `g_432A` | 1 | 1 | 1 modules |
| `55B3:4366` | `g_4366` | 1 | 1 | 1 modules |
| `55B3:5A97` | `g_5A97` | 1 | 1 | 21 modules |
| `55B3:604C` | `fd_55B3_604C` | 2 | 2 | 1 modules |
| `55B3:610A` | `fd_55B3_610A` | 2 | 2 | 2 modules |
| `55B3:6770` | `fd_55B3_6770` | 2 | 2 | 1 modules |
| `55B3:6772` | `fd_55B3_6772` | 2 | 2 | 1 modules |
| `55B3:693C` | `g_693C` | 2 | 2 | 1 modules |
| `55B3:6B42` | `fd_55B3_6B42` | 2 | 2 | 1 modules |
| `55B3:6B4A` | `fd_55B3_6B4A` | 2 | 2 | 1 modules |
| `55B3:6B9C` | `fd_55B3_6B9C` | 2 | 2 | 1 modules |
| `55B3:6B9E` | `fd_55B3_6B9E` | 2 | 2 | 1 modules |
| `55B3:6BA0` | `fd_55B3_6BA0` | 2 | 2 | 1 modules |
| `55B3:74AD` | `fd_55B3_74AD` | 2 | 2 | 1 modules |
| `55B3:74AF` | `fd_55B3_74AF` | 2 | 2 | 1 modules |
| `55B3:74B1` | `fd_55B3_74B1` | 2 | 2 | 1 modules |
| `55B3:74B3` | `fd_55B3_74B3` | 2 | 2 | 1 modules |
| `55B3:74B5` | `fd_55B3_74B5` | 2 | 2 | 1 modules |
| `55B3:74B7` | `fd_55B3_74B7` | 2 | 2 | 1 modules |
| `55B3:74B9` | `fd_55B3_74B9` | 2 | 2 | 1 modules |
| `55B3:8BD2` | `g_8BD2` | 2 | 2 | 1 modules |
| `55B3:8BD4` | `g_8BD4` | 2 | 2 | 1 modules |
| `55B3:8CCB` | `g_8CCB` | 1 | 1 | 1 modules |
| `55B3:9120` | `g_9120` | 1 | 1 | 1 modules |
| `55B3:9122` | `g_9122` | 2 | 2 | 3 modules |
| `55B3:9124` | `g_9124` | 2 | 2 | 3 modules |
| `55B3:9126` | `g_9126` | 2 | 2 | 1 modules |
| `55B3:94E4` | `g_94E4` | 1 | 1 | 1 modules |

## Debt

Every rejected group retains its views and a machine-readable reason in the JSON. Incomplete unowned arrays, conflicting DOS widths/extents, nonprimitive types, provider collisions, and ranges containing distinct registered addresses remain unresolved. The emitter creates no pointers, structures, callable stubs, capacity guesses, or duplicate provider names.

Reason counts:

- 1: address group already has a compiled owner but no safe registered primitive alias mapping was proven
- 195: conflicting-DOS-element-widths
- 3: frozen symbol grounding identifies runtime-owned storage; do not create an application BSS owner
- 37: incomplete declaration extent lacks a registered complete owner
- 1: incomplete-multidimensional-array-view
- 101: pointer-struct-or-nonscalar-view
- 3: proposed owner extent contains distinct registered symbol addresses; possible interior fields/aliases require review

Regenerate with `python portable/whole_program/unprovided_state_plan.py`. For a local scratch C candidate, add `--emit build/workers/whole_program/unprovided_state.c`.
