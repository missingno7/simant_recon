# DGROUP 55B3:5A28–5A29 owner audit (v32)

**Verdict: `OWNERSHIP_UNRESOLVED`**  
Review state: `root_review_pending`. This bounded static review does not authorize a source, manifest, provenance, or ownership change.

The two bytes are zero-initialized in the oracle (`S27` linear `0x5B558–0x5B559`; data-debt span SHA-256 `96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7`). The prior reference audit already found no game-function memory operand, address immediate, or relocation in the span. Its pinned scan covered 1,730 original game-function bodies; it explicitly does not model arbitrary dynamic pointer flow or runtime code. No computed alias to `5A28` is evidenced here, but the scan cannot exclude one.

The only grounded nearby source is `root:1F58`, [src/root/m1F58.asm](../../../src/root/m1F58.asm). Its accepted `_DATA` placement is `55B3:5A2A`, size 8 (`[5A2A,5A32)`), with four declared words: pending key, second pending key, saved INT 23h offset and segment. Original disassembly for `1F58:0038`, `1F58:005A`, `1F58:007F`, `1F58:00A1` and `1F58:00B8` uses those symbols at `5A2A–5A30`; it has no access at `5A28`. The next accepted contribution, `S20:39C7`, starts at `55B3:5A32`. These contribution boundaries establish the eight known bytes and the next contribution; they do not identify the producer of the two preceding bytes. The data-debt record and prior audit explicitly mark the ten-byte `root:1F58` owner extent as a heuristic overstatement, with no name or read/write evidence for its leading word.

The likely semantic neighborhood is the keyboard/INT 23h state handled by `root:1F58`, but no source declaration or typed view includes `5A28–5A29`. The previous object's end/PUBDEF boundary is not established, so assigning the bytes to `root:1F58`, its object, or a separate preceding contribution would be conjecture.

No Win16 cross-version pair names `1F58` or these offsets. Win16's `data_20_keyboard_latches` declares separate CapsLock/Command/Escape/Help/Home latches and gives no independent anchor for this DOS pending-key/vector block.

### Exact blockers

- No registered symbol or canonical declaration at `55B3:5A28`; the symbol registry starts this state at `5A2A`.
- No original direct operand, in-range immediate, or relocation for the two bytes. Existing bounded scan leaves computed pointer flow outside scope.
- No original preceding object/PUBDEF contribution boundary tying the bytes to a source owner; adjacency to `root:1F58` or `S20:39C7` is insufficient.
- No confirmed/high Win16 correspondence or two independent cross-version anchors.

### Pins

| Input | SHA-256 |
|---|---|
| `assets/SIMANT.EXE` | `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11` |
| `layout/manifest.json` | `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50` |
| `layout/symbols.json` | `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125` |
| `src/root/m1F58.asm` | `9f314c6e964bcb0955c1f3e976819bdbeddf048781c1bb257c30b2c0b25d49d2` |
| `work/takeover/behavioral-oracle/data-debt.json` | `2e4a87fedfcd10ffe239a93ab6201958cc50cfeb6a9679b01e49bd24f7b8a40a` |
| `build/workers/behavior_data_audit/reference-scan.json` | `c395daab89fccd0d0c8220e9dcc5e32bf6a677209712f72b0f73dd959de7fbf2` |
| `build/workers/behavior_data_audit/REPORT.md` | `e635df8da70bb5718b3108a58a3fdc4bf53571649b300f2e1f229a1dc754947c` |
| `evidence/cross_version/simantw_correspondence.json` | `57ca18670e67e2f2155625123980cbaefa316ac8c3f2d9986dc0d715943fe3a1` |
| `D:/Prog/simantw_recon/src/recovered/data_20_keyboard_latches-16d55c218f.c` | `16d55c218ff7a05dfa045bae65347b13994d6acdec300403fe6639358832cf3e` |

Static audit only. No compiler, matching search, acceptance gate, canonical file, or builder was changed.
