# Database reader fixture assets

The tests read the repository's original ignored `assets/` files directly. They do
not copy or modify those files. SHA-256 pins and sizes used during implementation:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `HCEGANT.NDX` | 2444 | `077d8aecdad5e816f0828204f7ca500a68b3a4a3288740ac75e73e44eaa8efc4` |
| `HCEGANT.DAT` | 629438 | `9c98c0f110e901a2c2db65944e4ebdf6b26392181e9415a34eb7b29617eaa899` |
| `SHARED.NDX` | 3868 | `e172f030c11f417af4b5be34dacbda9a63f157820827b40d62c08ca2c6ea7477` |
| `SHARED.DAT` | 96117 | `aa0d2342510f99abf57a685ea93178d9dd8d2d5be1e65b556c9b27f974012750` |
| `SOUND.NDX` | 1236 | `4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80` |
| `SOUND.DAT` | 111470 | `6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629` |

These pins identify the test inputs; they are not resource bytes embedded in the
portable source tree.

Selected HCEGANT kind-9 payloads used to confirm the tile record extents:

| Object | Bytes | SHA-256 |
| ---: | ---: | --- |
| 9 | 32768 | `a63efdcc9931373e3cd2ea27add3e7261fcebecb8bcb59f74a9c4bb96531c5b7` |
| 10 | 32768 | `07b09f333f0497fc69a8c07ab1ba195192c26f112c245be2b35fd4b3dd3c1d6b` |
| 15 | 20480 | `714587684cbb2cf8c46633ed4059113641e1cb5024978829def6d3bae4af67d8` |
| 16 | 20480 | `5bb90fa025544597460801c4aa5851f6fd39c618d5fe7f23e1997ff56428400b` |
| 17 | 20480 | `e6da2b666f4a8f13d77b2bc13e15218576fbb418448f5cf692aed77eda114649` |
| 18 | 20480 | `c615e6a4cce81c8af780ac61b3440c5299ec1bc89e69ecc0ba1d9d7ad7daa424` |
| 19 | 20480 | `fd24714f2f71471068121402b42ad244929bf7275b66e3e88b0d9a4ae64fee31` |
| 20 | 20480 | `79bc14093efe73df5e4910dde24f6b1a739ffb198d35ec905f689ed327c55a78` |
