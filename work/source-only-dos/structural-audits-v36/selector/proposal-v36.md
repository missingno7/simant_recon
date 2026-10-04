# Critical-selector minimum source view proposal v36

**Recommendation for root review: accept only the mutable one-byte near storage view and CRT-zero startup contract, with a mandatory unresolved `critical-selector-computed-alias-layout` gate.** No production edit, admission, promotion or Git operation was performed by this worker. Historical TU/COMDEF ownership and original placement are not claimed.

The proposed source is `selector-view.c`: `char near g_8CCB;`. This is a minimal object view directly grounded by the original `1C62:06C8 MOV AL,[8CCB]` and following `CBW`, plus the existing selected whole-module declaration and fallback expression. It preserves a signed byte and allows later mutation. It does not make the selector constant, clamp its range or remove its read. The retained v18 original startup receipt establishes that `__astart` clears `[55B3:8B9E,55B3:94F0)` before `main`, including this byte. Fresh stock-CRT fixtures establish the corresponding uninitialized source object starts at zero under both real RTLinks.

This split follows the existing render-delay-word policy: that word has a source owner in the fresh 188-TU intake while `menu-table-cross-owner-layout` remains explicitly `UNRESOLVED`. The policy separates an access-size/type/startup object view from preservation or exclusion of original cross-object computed writes. The proposed byte has a weaker producer history than that delay word: there is no direct named game producer. Its one-byte extent is therefore explicitly the minimum proven read view, not a recovered defining aggregate, allocation capacity, lifetime proof or historical TU.

## Fresh controls

The worker freshly generated all 188 effective source TUs under `intake/`. The actual selected `U088.c` contains the registered behavior substitution for the dialog helper; it was compiled as a complete file in the current compiler/flags context. Its selector is exactly 54 bytes, matches the original SHA-256 `4f78c1abb0b4264afb395c29b5d8731a30874c54095d1af322f846dec72f2740`, and binds all six symbolic offset fixups with no unbound target and exact fixup order. This is the selector contribution gate, not acceptance of the entire historical TU.

The runtime fixture extracts the declaration/table/selector block immediately preceding the actual selected selector. The positive block is exact source extraction, linked with the natural data-only provider and pinned LLIBCR/LIBH. Other game helpers are absent; there are no game stubs. Runtime-stage original/asset access is denied, with zero denied-read attempts recorded.

| Case | RTLink 4.00 | RTLink 6.10 | Meaning |
|---|---|---|---|
| Signed-char BSS view | PASS | PASS | Startup zero; all 14 fallback entries; inclusive `sys_errlist` endpoints; byte promotion gives -128 for raw byte 80h without using it as an index. |
| Byte initialized to 1 | Expected FAIL `init=1` | Expected FAIL `init=1` | Challenges startup contract. |
| Two-byte `int near` view | Expected FAIL `width=2` | Expected FAIL `width=2` | Challenges minimal extent using a matched word declaration in the negative fixture. |
| Independent context storage before DGROUP data | PASS | PASS | Selector works after its source-owned offset moves. No historical address binding. |

The positive compiler object is a near communal of length 1 with no initialized payload or code. The word contrast has length 2, and the initialized contrast is initialized near data with no communal. An unsigned-char provider was compiled only as an equivalence diagnostic: it has the same length-1 near COMDEF as the signed provider. It is **not** a manufactured runtime negative with a still-signed consumer. Supplemental `/Zi` objects preserve source type metadata; the original `CBW` and fresh whole-TU match independently determine consumer signed promotion.

All eight links are clean under the production diagnostic classifier. Complete maps and stdout are retained and hash-bound, including `_g_8CCB`, `_errno`, `_sys_errlist`, `_sys_nerr` and `__astart`. The provider offset moves `0810 -> 0930` under 4.00 and `0A10 -> 0B30` under 6.10; the group frame also moves `0143 -> 0144`. The map parser was repaired to account for the different flag/member columns of the two RTLink versions, then all actual maps/output files were hash-verified and reparsed without rerunning unchanged binaries.

## Closed ordinary inbound question

No accepted symbolic indirect-target producer forms this selector's code address. In all 188 effective full TUs the function appears only as its definition, including an underscore-spelling check for assembly. There is no call, address registration, pointer initializer or callback argument naming it. Its byte appears only in declarations and its selector read.

The fresh original scan covers 1,730 function extents, 29 units, every unit relocation and all 136 RTLink vectors. It finds no external direct transfer, contiguous relocated far pointer or RTLink vector into `[1C62:06A6,1C62:06DC)`. All 149 relocated segment words referring to code frame `1C62` belong to immediate far transfers elsewhere, with no split segment-address materialization. A deliberately over-approximate scan at every byte offset in each original function of the same frame finds no external E8/E9/EB candidate into this interval. This avoids relying on linear decoding across switch tables.

The positive target control is the real `IBMInitStuff` registration: `MOV AX,058Bh; MOV DX,SEG 208F; PUSH DX; PUSH AX; CALL _harderr`. Its installed INT24 closure is exact: stock handler `29F4:2DAB -> callback [55B3:7DAC] -> f_208F_058B -> handler return -> IRET`. The callback is `MOV AX,3; RETF`. Fresh full-member binding matches all 87 code bytes and all six data bytes. The member owns callback `[7DAC,7DB0)` and `__oldsp` `[7DB0,7DB2)`, without communals. A negative placement that puts `__oldsp` at `8CCB` fails five code-operand fixup fields. This excludes CRT/INT24 saved-state attribution of the byte.

**No real path to the sole selector read after prospective alias writes is known.** The ordinary symbolic graph is closed as described. That is not a universal dead-function theorem over unchecked computed dispatch or memory-corrupted continuations. Such continuations are a different open integration/domain question; they are not attributed to ordinary named callback production.

## Mandatory separate unresolved gate

Suggested gate name: `critical-selector-computed-alias-layout`, status `UNRESOLVED`. Its storage acceptance must not resolve this gate or make standalone/full-game success claimable.

- Original window-pointer writes can overlap the byte: `g_8CF2[-10]` is `[55B3:8CCA,55B3:8CCE)`. The represented 72 unlock sites have prior same-expression locks, but invalid-lock completion still depends on full first-Punt termination through actual saved-selector/sound dispatch. The recursive Punt guard does not close that question.
- The `ev->code` reread can change between lock and unlock unless the selected decoder/resource-height domain prevents the conditional `50F6:1F2A -> Event.code at 50F6:4A06` overwrite. The old source census alone does not bound that memory reread. The independent `g_5702[0]` transitive-clobber review remains a separate premise.
- The fresh neighboring DS-store sweep records an additional arithmetic continuation: the uncapped song header count in `f_284A_0256 -> f_284A_0199` can address `(8DD8 + 2*32633) & FFFF = 8CCA`, whose word high byte covers `8CCB`. This is not an executed counterexample: earlier out-of-range stores change player/CRT and potentially stack state. The retained v35 census of intact supplied SOUND streams (all 30 have 2–10 tracks) excludes this threshold for those loads. Preserve the wider altered/corrupted-resource continuation as unclosed, not as a shipped-resource failure.
- No changed byte value has a known downstream selector-read path. To claim those physical aliases irrelevant for the entire program requires a complete computed-code/reachability domain proof, beyond the ordinary symbolic closure established here. To claim them preserved requires a source-relative alias/storage proof. Neither is supplied by placing the candidate elsewhere.

Thus the proposal preserves every known **nominal** source access and its startup state. It does not yet preserve or exclude every original computed physical alias; the explicit gate is the required separation. Historical owner provenance alone is not the reason to reject this view. The proposal is defensible as minimum view ownership with unresolved integration debt, and would be too strong if labeled a full physical owner, invariant-zero selector, unconditionally dead fallback or completed SOURCE_ONLY_DOS solution.

Artifacts: `receipt-v36.json` (read-only provenance/closure), `whole-tu-v36.json` (actual selected full-TU compilation and exact selector gate), `fixture-receipt-v36.json` (all compiler objects, link inputs, complete maps/stdout and eight outcomes), `selector-view.c` (proposal), `audit_v36.py` and `fixture_v36.py` (reproducers). Reproduce the source intake with `python tools/source_only_dos.py --out build/workers/dos_critical_selector_v36/intake`, then run both worker scripts. No validate/promote command was run.
