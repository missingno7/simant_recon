# Point-state owner candidate review

Research candidate only; no source storage is admitted by this file. The provider covers five source-bounded point objects with natural signed `int x/y` fields. It does not claim the original owner module, COMMON order, padding, or initial values.

| Symbol | Registered 50F6 offset | SaveRec bytes | Source reset/write path |
| --- | ---: | ---: | --- |
| `fd_50F6_0508` | `50F6:0508` | [src/S09/m35F5.c:952] `{4,1,&fd_50F6_0508}` | RandWorld 0x40,0x20; map origin |
| `fd_50F6_0596` | `50F6:0596` | [src/S09/m35F5.c:942] `{4,1,&fd_50F6_0596}` | RandWorld defaults, then active MeLocX/MeLocY |
| `fd_50F6_06A6` | `50F6:06A6` | [src/S09/m35F5.c:943] `{4,1,&fd_50F6_06A6}` | RandWorld defaults, then active MeLocX/MeLocY |
| `fd_50F6_072E` | `50F6:072E` | [src/S09/m35F5.c:953] `{4,1,&fd_50F6_072E}` | RandWorld defaults, then active MeLocX/MeLocY |
| `fd_50F6_07BC` | `50F6:07BC` | [src/S09/m35F5.c:954] `{4,1,&fd_50F6_07BC}` | RandYard sets 11,8 before passing it to RandWorld |

`fd_50F6_0620` is excluded: canonical source declares `long far` and uses it as a balloon timer; it has no direct SaveRec row and no point-field footprint.

The full source audit scans every manifest module and every whole-module source registered by the strict 29-function index, including corrected DrawBalloons. Exact references, token/use classifications, hashes, registry aliases/interiors, SaveRec rows, lifecycle anchors and no-Zi OMF results are in the scratch receipt.

No-Zi provider OMF: five far commons, each `{"kind":"far","count":4,"element_size":1,"length":4}`. The compiler uses the same shape for `Point` and `unsigned char[4]`, so that record is not a type distinction. Array, doubled-extent, near and initialized controls are independently compiled. Both pinned linkers passed the exact SaveRec byte-view runtime case and the interior-pointer and initialized-data negative cases.

Lifecycle caveats: InitSimVars does not assign these points. RandYard sets 07BC before the RandWorld inputs; RandWorld writes the four plane points before returning; RandYard then replaces the active saved point with MeLocX/MeLocY. LoadGame calls the RandYard reset helper before its table read loop. A read error can leave a partial saved state and skips the successful-load path; the caller then takes NewGame on the recorded read-error state. No omitted values are inferred.

Probe result: **True**. Detailed audit: `build/workers/dos_point_state_owners/point-state-cm80dkf7/point-state-source-audit.json`. Candidate receipt: `build/workers/dos_point_state_owners/point-state-cm80dkf7/point-state-owner-candidate.json`.
