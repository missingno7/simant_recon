# FAR_BSS track-array ownership receipt (v35)

**Decision:** Keep `fd_50F6_4B30` and `fd_50F6_4B42` as unsized imports with storage/capacity excluded. The accepted `g_8DD8[18]` declaration and the original track loop make 18 a strong structural hypothesis, but do not establish either FAR_BSS array's exact source extent or an 18-track runtime limit. No source, provider, canonical manifest, or Git files were changed; this receipt is scratch evidence only.

## Evidence

| Pin | Finding |
|---|---|
| `src/root/m284A.c` SHA-256 `bad7d3701a853ba2de166e4f875ba3043f33ca136b7d0dcff41db8e5459f9fa5`; lines 36–37, 120, 146–147, 155–161, 172, 202–217, 275, 303–312 | `g_8DD8` is `static int[18]`; `g_8DFC` follows. Both FAR_BSS names are unsized externs. `f_284A_0256` uses the shared count `g_7566` for writes to the offset table and the imported arrays; `f_284A_038F` scans the same count and retargets status/offset pointers. No `g_7566 <= 18` guard is present. |
| Original code: `root:284A:0199` (60 bytes), `root:284A:0256` (142 bytes), `root:284A:038F` (314 bytes) | At `019F` the offset loop starts at zero; `01B9–01BD` scales the index by two and writes at `8DD8 + 2*i`, then compares against the caller-supplied count at `01CB`. In `0256`, header count comes from offset 10 (`0269`); loop code uses `8DD8 + 2*i`, time base `4B42` with four-byte entries (`02B7–02BC`), and status base `4B30` with byte entries (`02D3`); its loop ends by comparing with `7566` (`02D9`). `038F` also scans to `7566` and uses both arrays via selected-track pointers. |
| `layout/symbols.json` SHA-256 `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125` | Registered FAR_BSS starts are frame `0x50F6`, offsets `0x4B30` and `0x4B42`. The next registered symbol is at `0x4B8A`, yielding gaps of 18 bytes and 72 bytes (18 longs). These are address distances only. |
| `layout/manifest.json` SHA-256 `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50` | Accepted module placement for `root:284A` is `_BSS`, segment `0x55B3`, offset `0x8DD8`, size 46. The module lists scaffold `f_284A_0138` and has no `extent`; it is not a complete TU storage proof. |
| Candidate `build/source-only-dos-v35/objects/U117.OBJ`, SHA-256 `552054d34def7f644872f5af19fca5c4cacbb05f00144e3b8c345a5b4ccd601`; candidate source `build/source-only-dos-v35/sources/U117.c`, SHA-256 `c6d2df7fe13f9e6de73ebdf2fa010f30bf3c68e02b5c2350a8ce7b02130cd100` | OMF parse: `_BSS` SEGDEF length 46, `COMMUNALS=[]`; both FAR_BSS spellings are externals. This is a current candidate object, not an original defining object or COMDEF pin. The candidate retains the partial-TU limitation. |
| `work/source-only-dos/current-intake.json`, SHA-256 `4106d47aefa7e2da91172440424cc1e65152b4f7aef5b6c0fad6bb5d76e82c37` | Both imports remain unresolved with `accepted_storage_candidates: []`; intake records unsized `unsigned char far []` and `long far []` declarations. |

## Existing exclusion and positive control

The reviewed v27 exclusion is `work/source-only-dos/storage-admission-v27/sound/root-acceptance.json`, SHA-256 `5e814fc341cab7f24061df1a8f8aa0132b8f88518eb17c81d85dbfaf10227f6f`. Its `source_extent_basis` (line 87) admits neighboring `4B8A`, `4B8E[14]`, and `4BAA[14]` from independent producer/count/type contracts plus complete OMF/runtime controls, while explicitly leaving unsized `4B30` and `4B42` excluded/open. Other listed neighboring communals include `4B28`, `4B2C`, and `4B2E`; their proximity does not transfer an extent to these arrays.

The comparison packet `work/source-only-dos/history-storage-bindings-v1.json`, SHA-256 `9de05b5bf7b34c168581189d4f4749a53b37576600205be32f0500e14b17c80a`, explicitly scopes reviewed ownership to ten bounded arrays in generated S24 and disclaims neighbor-gap sizing. It anchors 64 signed words (128 bytes) with the S24 owner, `ClearHistory i < 64`, `HistUpdate` ring index masked to 63, and S09 `{2,64,&array}` serialization. The related runtime contract `work/source-only-dos/history-storage-contract-v1.json` has SHA-256 `7fc4c0f32f70521f8d730121fd75e9bccab0c4e87a7611e25c48f5dd7b8470bf`.

Source pins cited by that packet:

- `src/S24/m39C7.c`, SHA-256 `3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240` — typed `[64]` owner and ring operations.
- `src/S09/m35F5.c`, SHA-256 `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a` — `{2,64,&array}` byte-view records.
- `src/data/d3D57.c`, SHA-256 `983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5` — initialized typed pointer graph views.
- `src/S14/m384C.c`, SHA-256 `245f8c01d5a330c571048b8cd1b134cf544394af84f7b502a153c73adbd91020` — additional score reads cited by the packet.

That history proof has an explicit owner, indexed bounds, serialization shape, and cross-module controls. The track arrays presently have unsized imports, count-driven unguarded indexing, only next-symbol geometry, and no accepted full-TU/COMDEF extent pin. These are not equivalent evidence.

## Rejected extent and limit inferences

- `g_8DD8[18]` is a convincing paired-index clue: the assembly scales its index by two and the accepted object places following local symbols at offsets consistent with a 36-byte table. It owns the offset table only; it does not name or size either FAR_BSS array.
- The 18-byte and 72-byte neighbor gaps agree with 18 statuses and 18 longs, but the FAR_BSS evidence rules require independent source or COMDEF extent evidence. Geometry alone is insufficient.
- The same unguarded count drives all three structures. It establishes shared indexing behavior, not a validated maximum. The supplied shipped-resource census has counts 2–10 and establishes observed content only, not a bound of 18.
- No exact original COMDEF/defining OMF record for either symbol or accepted complete source TU with explicit owned arrays is pinned here. The current OMF is candidate-only.

**Disposition:** retain the source/type views as recognized references; keep both capacity and storage admission excluded. If reconsidered later, the evidence gate is an original defining COMDEF/OMF extent or an accepted complete source TU with explicit ownership and the required build/layout controls. Do not add a `maxtrack18` claim from this evidence.
