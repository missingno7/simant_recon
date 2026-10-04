# Unlock clobber review v19

**Disposition:** the 72-site lock/unlock identity and pairing census is accepted at callsite level. The 70 ordinary constant/by-value pairs are accepted under the caller-domain receipt. The two memory re-read closures below are **REVIEW_PENDING** because transitive callback effects were not closed. `g_8CCB` admission remains **BLOCKED** by the unresolved saved-selector owner; this review does not assume `Punt` is nonreturning.

## Caller identity and pair coverage

The v18 source review records 72 unique DOS C callsites: 63 spelled win_UnlockWin and 9 spelled f_23AE_01DB; the latter is an alias of the same root:23AE:01DB code identity in layout/symbols.json. The paired lock alias f_23AE_0377 is likewise win_LockWin at root:23AE:0377. V18's 72 caller rows all carry equal lock and unlock argument expressions. The caller-domain receipt enumerates every site and its preceding lock. The 29-record strict index reports 23 duplicate sites and no unique additions; its assembly alias-reference list is empty. For the 70 ordinary rows, the closure receipt identifies constants or by-value scalar locals/parameters, with no interval assignment or address escape. The two memory re-reads below were checked independently; expression equality alone is not used as evidence.

## Re-read 1: ev->code

src/root/m218D.c:38,82 pairs win_LockWin(ev->code) with win_UnlockWin(ev->code). Its only source caller is f_218D_02D5 at line 186, passing &fd_50F6_49FA after f_1B73_032E fills that event at line 148. The adjacent saved event fd_50F6_4A0A is a distinct symbol 16 bytes later (confirmed in layout/symbols.json). Between lock and unlock, lines 68–80 update the event's modifier bits and copy fd_50F6_49FA to fd_50F6_4A0A; they do not assign fd_50F6_49FA.code.

The case-4 and slider handlers receive the same event pointer. Their strict whole-module source is evidence/behavior/functions/f_23E6_0000/revisions/ss-ds-20261002/module.c (registered by work/source-only-dos/static-completeness/f_23E6_0000.json); canonical counterparts are src/root/m23E6.c:401–424,429–471. Both read event fields, with no direct store through `ev` in those reviewed bodies. The slider's wait helpers are f_1F80_0081 (timer wait, m1F80.c:54–64) and StillDown / f_1FD2_0542 (keyboard-state polling, m1FD2.c:294–305), not the event queue.

The type-12/18 branch also calls o26_39C7_040F(ev) (m218D.c:48–52). That canonical handler reads `ev->h/v` and invokes `g_62EC` at src/S26/m39C7.c:281 before returning to the outer unlock. Startup src/root/m00BA.c:57,90–105 registers f_00BA_01C3 through f_20E8_08DB (m20E8.c:376–378). Its first-level body includes f_22BF_0E83 (m22BF.c:705–719), `win_CasteControlChanged` and `win_ModeControlChanged` (m0798.c:78–95), f_0250_0E15 (m0250.c:594–602), and map/yard helpers (m00F8.c:29–56). This establishes a real callback route, but not transitive `ev->code` stability. **REVIEW_PENDING:** closure was not performed through `f_22BF_0E83 -> win_Recalc`, Caste/Mode changed-to-Closed callbacks, `f_0250_05CB`/`f_0250_0F2C`, or `win_YardClosed -> hanim_RenderAnimSet` and their allocator/render callbacks. The `f_00F8_00A4` / `f_00F8_0002` names map to `win_MapChanged` / `win_YardClosed` in layout/symbols.json; S12/S13 cursor-erasure helpers and renderer callbacks are also outside this bounded closure. No claim is made that `ev->code` survives these downstream effects. The event reread therefore remains **REVIEW_PENDING**, notwithstanding the absence of a direct `.code` store in the reviewed outer body and strict case/slider handlers.

## Re-read 2: g_5702[0]

src/root/m218D.c:118–126 pairs `win_LockWin(g_5702[0])` and `win_UnlockWin(g_5702[0])`, with reads between. The hit-test f_1B73_0BFF at src/root/m1B73.asm:1705–1739 only reads the mouse point and candidate rectangles, returns an object id, and makes no call. `_win_SetProxItem` (m218D.c:99–109) changes `g_6368` and calls `win_ObjInv`; that function (m22BF.c:227–235) locks an object, invalidates its rectangle, and unlocks it. The observed `g_5702` stores are in window-order helpers in m1E57.c:59–90,100–110. However, the invalidation path calls `f_1CE2_0430` (m1CE2.c:140–143), which invokes the `g_913C` graphics callback. **REVIEW_PENDING:** the callback/render/allocator effects beyond this edge have not been traced to rule out a write to `g_5702[0]`. The source occurrence check and absence of direct stores in the hit-test or `win_ObjInv` body are insufficient to establish reread stability.

## Remaining blocker

The 72-site identity/pair inventory and 70 ordinary by-value arguments do not close either memory re-read path. In src/root/m23AE.c:44–59, the range-error `Punt` call has no nonreturn contract, and the function continues into indexed work. V18 remains blocked on the `/s9` saved-selector owner/value used by `Punt` cleanup. Until that path is closed, do not infer that a bad lock cannot return and do not admit `g_8CCB`.

## Evidence pins

SHA-256 values pin this bounded review's inputs and source definitions:

- work/source-only-dos/critical-error-selector-source-review-v18.json: d2192f9581551f8bd6af6a8904cd911642a6e4e905a84da3ada1b4e5381d6b92
- work/source-only-dos/critical-error-selector-source-review-v18.md: 2d10f737bc2dd1dc18131f532327d63ff6e032a93b185d67f77cf1a8c04c6e1e
- build/workers/dos_critical_error_byte_owner/unlock-caller-domain-closure-v1.md: bee8d49c20232c2356a692777f6de7a7e399e685e7993876ff8e9ee0691a2d9b
- work/source-only-dos/static-completeness/index-v1.json: 092b3a15aaaf99737020c0c00e2a4340514dda3f0e2ff45369d1fa0a316d9a3a
- layout/symbols.json: 0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125
- src/root/m218D.c: 3ccc2dedf58831dc2f853beb3133847e7f1f8c1883c445379fd5584b3255112e
- src/root/m23E6.c: 6992614db2546bf039d6e9fb3be17df0a48607dfa3b3e3faba05ed5e5e938bec
- evidence/behavior/functions/f_23E6_0000/revisions/ss-ds-20261002/module.c: 867a7f15631db0ef33079daedea99f99e7ddc75b57f04b15bafca036f14c5ee7
- src/S26/m39C7.c: fb4938daa334a8e9f929b44a542392f47fc7c1a654ca87f303ee80528b34c4c4
- src/root/m00BA.c: d72629d827e2bccd7557566b725f652862d2b1199f40390361179c61cc9ff5dc
- src/root/m00F8.c: 4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a
- src/root/m20E8.c: c2ec2474010ef9821fd46cdf72e50f164c850446b6f4b051a91d474b53dd5ae2
- src/root/m1B73.asm: 3097a6b03ff1d8bdfa7d573632d9905de88d754c8b1e047de4014c4f186cb848
- src/root/m1FD2.c: f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8
- src/root/m22BF.c: f5b617067cdc711593e94dbb725ae9ceaeb12b890f198af0d66c1973e15133a0
- src/root/m1E57.c: 812e8ec90bcf25c56adf073e753bf72f8f6a3bc108055e112c43f894e9d8d0c3
- src/root/m23AE.c: 531c983e47c1f39b6be2d94bb9fa0ccc1fa557ca9ec35542178a566f4d48076c
- src/root/m1F80.c: 8832c414385ec5b69a1805c9271196e17cb0b91961ef4db0ca83aaff04a3bc34
- src/root/m0798.c: ecf807dc3159f583f6ee3ea8a9f5422650a64bb557d4551e9c97b5dcc7b6a1b8
- src/root/m0250.c: bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b
- src/root/m2505.c: 22a03f15e95fff376d27211426c4f9e3395e16e5decd92ef501fbfe3c1aba623
- src/root/m1CE2.c: e5c2cb4b8dbe7af6d263072002a49e012b290c1082f0fc877b479728b75bacd3
- src/S12/m384C.c: 584bf940832e3f8e975afdf85ed398fc82b6470e4a5c3ec46c1b4fcd15240002
- src/S13/m384C.c: fb6785e93f5c2ea1110f64b5eb200d7f4e346263c43ac521c0434629d9f5839a
- evidence/behavior/functions/win_UnlockWin/contracts/window-valid-v1/module.c: 23aa124a97a2f213fcf99d0f3e9790e2a35813ee5e62d338f7ef205c5b03acc0

No production/canonical file, Git state, binary match, or fixture was changed or created.
