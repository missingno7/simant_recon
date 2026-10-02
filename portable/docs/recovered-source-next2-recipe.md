# Recreate the `recovered_source_next2` diagnostic profile

This recipe recreates the generated native source profile used by the next2
startup/tick investigations. It is a source-reuse diagnostic, not an accepted
behavior proof or production build. It does not alter the frozen historical
oracle.

## Inputs and command

The historical source anchor is `dos-semantic-oracle-v1`, commit
`66e85041ee54f59774ae0fd5a08b37ffbcf77172`, as recorded by
`portable/README.md`. Use its `src/` and `layout/symbols.json` contents. Use the
portable-branch generator at SHA-256
`c1fd7616c392d39ebe4574e6ccde85b4e7f79205d21afcfbcb7ead249d5ffc50`:
`portable/tools/recover_source.py`. The generator and shared input digests are:

| Input | SHA-256 |
|---|---|
| `portable/tools/recover_source.py` | `c1fd7616c392d39ebe4574e6ccde85b4e7f79205d21afcfbcb7ead249d5ffc50` |
| `layout/symbols.json` | `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125` |
| `src/data/d3D57.c` | `983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5` |
| `src/data/d3E1D.c` | `ab35eb29d30ac1bcf6390bf8a979c5d018f43f4cae45f9f0d9a1f00200611d05` |

The one reviewed body substitution is `LessonDone` in `root_m0E2E`. It replaces
only that named scaffold body with
`evidence/behavior/functions/LessonDone/contracts/host-service-v1/supplemental/tested-source-snapshot`
(SHA-256 `c611660dde4da7117c3232aa06e597871394cc4112466d46559705b235424359`).
The review packet is `evidence/behavior/functions/LessonDone/contracts/host-service-v1/run.json`
(SHA-256 `1930667ce288db35aec4227619534a06b3a6e4e990e4a460f6f247818db96b32`),
which pins oracle `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`
and manifest `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`.
The generated translation unit applies the pinned function aliases
`f_00F8_02BE -> MacTickCount` and `f_22BF_0A22 -> win_IsWinInFront`.

From the repository root, run:

```powershell
python portable/tools/recover_source.py --out build/workers/recovered_source_next2/generated --compile
```

The output directory is intentionally outside the checked-in recipe. The
generator writes 22 selected whole translation units, one selected
`MapToYard` function, recovered shared state and adapter source, then compiles
all generated translation units plus the shared state support with GCC.
The expected result is 23/23 translation-unit compile passes and a passing
support compile using GCC `12.2.0 (Rev10, MSYS2)` with `-std=c11 -Wall
-Wextra -Werror` and the historical-warning suppressions recorded per module
in provenance. Provenance status remains `DIAGNOSTIC_ONLY_NOT_PRODUCTION`.

The output path and compiler installation are recorded in `provenance.json`.
Those environment fields make that JSON file's own bytes path-dependent; do
not use its whole-file hash as the content reproducibility test. Compare the
content hashes below, check the source hashes in the generated provenance,
confirm all compile results, and confirm the reviewed-body row still names
only `LessonDone` with the exact review and source pins above.

## Expected shared output hashes

| Output | SHA-256 |
|---|---|
| `recovered_state.h` | `bb89c625bfb8bccbf827e1c701bd1490f57106276d81b6abcdf7aa8e7b42fec6` |
| `recovered_state.c` | `4d7527a1961b5792f8322366cbd51b70559e889b41e0b941b2f7e7477441095f` |
| `recovered_native_adapters.c` | `ce2206c52ba57034074403a4e3e267300cbce2898ddec1693923ea9e28edef4e` |

Each generated translation unit is pinned by its historical source hash and
generated-body hash. The order is the generator's selected-module order; the
last row is the selected `MapToYard` function extracted from `root/m00F8.c`.

| Generated unit | Frozen source SHA-256 | Generated body SHA-256 |
|---|---|---|
| `root_m0894` | `57b40ad0a9ee74c501fbcb0d521b86b8158f206f44f4867e960bcb800b5e7484` | `8000355cca9c7f1814f11b73c72f02aed03676a04feb3dbffdf27858ae25fffa` |
| `root_m0F3F` | `f1c903c7f29e4fbb64fd82c2de5390c00df4f7cf35c9c836007dfa07c56612e8` | `f0382dacf476a439af29b5a8ca08dd90efa4ff5bb8aeebdb29f6e9c7693803d4` |
| `S25_m39C7` | `90a2cf12a9e527d1836099c92e5327d47342eac0a8403639d66471ecbc859ba6` | `95df541f35ce4b7e01bf1d583203fc43321c0d6b6ff90954a5a5e008920af22e` |
| `S25_m3BA4` | `d2937c80fe0ef4f2bd30c4c3ebe344ce4f993870f08515e7436c60d30cacdec4` | `871db4aa4b919341e34251187521718e3f8cb1ed26d482deed4c10c6740e9ecc` |
| `root_m0EC1` | `516121f3568fffaa6a6f17a0a87da5696dbb1e4db02cbcfa93ad5ad4497454cc` | `10de1fc088946b21bb6c760a2748714643b18193a20851b4e3d8f4a76037aa6a` |
| `root_m1496` | `2b158a9367c89c7acf496efe4ff8490865fda03c5c88cfd70343264d1e2d15de` | `bfc8c897634becde810147feecdc47b8d06ddda10458f8ad24bfb1e18f5c9d84` |
| `root_m1383` | `489ee7d47f0ee27942bf6bea11fff7a8bbb90acd2c75fe4653d18a3e9efa5389` | `d4cec849bab3bbf95057d6ead03ff150e5e2345a70fcba1acb219142ed783094` |
| `root_m10F7` | `a4cc271d57a4a80dd255953554a886026297b0560453c4b2c7b302b5878fff88` | `fd7a6a41c4115aca2c2b94fc42741bca1992854008ae52ba13ab0cf516416c85` |
| `root_m0AD9` | `726585ecdb17d969b478bf5a55b726736614dbaa2d5f6477b8f6907c86f73d0b` | `e049506f7eb33921e63606902566324852f733f7666c355078653c657395a42c` |
| `root_m0CDB` | `ae615fe56d075de2a59449b444709c79a847e4f4fb5806e58a50b5c59418c033` | `764dbc4e41e6aee5d2884e442f0f5b943ddb924e1dc6c37313db70b173437c1f` |
| `S06_m35F5` | `db35a96a492a6d36f6580222c17daca015aa9373b457b8758c751d3a70844a86` | `f46684e0b7f5fcf1977e7f54009b8b30e1cda17915b268c8205b09c0cb3ee9e1` |
| `S08_m35F5` | `ef6eea405f6497cb5a6648ef258cc1afeab308f995ded573794465d831e3501f` | `db773ccddd3034784d226ce0978166a750ca87a8b21fae28c02082af4a3bbe73` |
| `S24_m39C7` | `3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240` | `edb38e05189f5d742df8390ebbeb75733697e5ea99551b377104ae071e5e424c` |
| `root_m0BE8` | `42664e07331fbba4cc257f1e49e03dff5e93deddb764d33101ad0f454a9377d7` | `8402948d80ebaad3c67f1c6eb26e84744e75ecfcf4dab86689853495e102af6f` |
| `root_m14EE` | `a9947226c73c4502f00e2b319b3cd7abc7f2acbc8ca9ef72448b31e55c6bdb59` | `1c2b31368d114fb087c7f48c7b7d560e5d5743f155c6a59c4d422e469266f505` |
| `root_m0DEF` | `4325b570055de5daf8b96fe529d53f316b1a8a046daf845672672bd376d08142` | `11767de4ba6262975d8113a4557a67352bb5e9346ccbe1ee33de5b3fc0e3680c` |
| `root_m015B` | `67f5c32deda5a49ab56243d50fba33647db7897c850706378fe2a8488277fa8f` | `6baf14044316ccaa6469af4626fad04a41af969d6eb0a3df40f2cc3170370df8` |
| `S18_m384C` | `78a0f63aa99b2c2346e799b4e63f5d94256ab62b17f88d301bb986112aeed8d3` | `c217e9582b77f238f5aa71fe4c7afdb94bba523712d759f4bfdb3496767c62ce` |
| `root_m0E2E` | `9325b3426ef87771150912ce8f7cfaacc13380634505313417978b80974d10ed` | `1f219384cffbb44077dde74fa2ef4e542ba9174878c73fe47ad45ec8fbed444b` |
| `S11_m35F5` | `39b6df453387ee12a16dd07313e12cbe29a598eb1441011c03c6d33cba576ec8` | `b5a015b09c41cf9857463bcc8404c72d5409bad6a174612c55901c4017fa8196` |
| `S22_m39C7` | `e9add4ebd445bd943f24a65764be2a79581f2fc26c349741fdfe8efae3b7030d` | `0782e86525464cf879f61300d064de33efeb1773e3341eadd64a0a0e427faeb7` |
| `S22_m3BBD` | `22ed7dc5dbf4687dc3e971e6845bf28ce1934f771c81ae551dd30bc782753da2` | `d93231daee300a7674a69af25c4aba1c1183c26b3fee4db1d2f2ffee3b3cb90c` |
| `root_m00F8_MapToYard` | `4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a` | `98e7d158376b1ce112785e849924db74c8539875f0084ba1903477d0638d8933` |

These expected hashes are for generated file contents, not object files. A
different compiler or warning environment may change compile receipts and
object hashes while leaving the generated source unchanged.
