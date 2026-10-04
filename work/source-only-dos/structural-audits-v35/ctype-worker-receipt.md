# DOS ctype out-of-range index/layout receipt (v35)

Scope: read-only source/disassembly/evidence audit. No canonical source, registration, layout, promotion journal, or test data changed. The strict function registrations remain untouched; algorithm completeness is separate from the memory layout available to that algorithm.

## Disposition

Recommend keeping the newly added unresolved `ctype-out-of-range-index-layout` source-only integration gate. The generic fixed-literal/assembly address audit does not cover computed C indices. This is a layout/dependency gate, not a claim that every out-of-table read changes output or that supplied game resources contain high-bit text. The S23 branch has no source-level high-byte guard; a parent-run conditional original-vs-candidate VM probe demonstrates a state-changing witness under an explicitly synthetic catalogue state. No shipped-resource or runtime reachability is established.

## S23 behavior-sensitive conditional witness

Canonical source `src/S23/m39C7.c` (`4e2ff0a4d57f3159b2fb58ff64c77bb7740e2a415292cc7f2fe9fad095daf4`):

- `win_PrintStyleTextInRect`, lines 148-171, reaches the ctype loop after a style transition when `n > 0`; the lookup is further gated by `record != 0` and prior style face `0x100`. It copies the text run to `buf`, then evaluates `(_ctype + 1)[buf[start]]` and conditionally subtracts `0x20` from the copied byte.
- A signed `char` value `0xDD` is `-35`; original instructions at S23:39C7 function offset `029B` (`MOV AL,[BP+SI-9A]`), `029F` (`CBW`), `02A0` (`MOV BX,AX`), `02A2` (`TEST byte ptr [BX+7A1F],2`), and `02A9` (`SUB byte ptr [BP+SI-9A],20h`) therefore read DGROUP:79FC, `_ctype`-34. If that out-of-owner byte has bit 2 set, the copied byte changes DD -> BD.
- `DisplayCard` loads text and optional style resources and calls the renderer with `record=1` (`src/S23/m39C7.c:450-487`). It has no general high-byte rejection. Its embedded-NUL cleanup at lines 466-479 skips a NUL plus following bytes that compare below space; it does not filter a DD byte inside a nonzero text run. `f_24AB_0367` at `src/root/m24AB.c:141-146` has no input range check; `_font_CharWidth` at `src/root/m25E7.c:151-173` masks the character with `& 0xff` and indexes font widths/fallback, with no ASCII rejection. Source path exists; actual high-bit resource input remains unproved.
- Parent-run conditional VM probe: `build/workers/dos_root_structural_v35/ctype_prefix_probe.py` SHA256 `108e51e81bfe2020f4780fc13c14422dd5cf4715ce944ca89fb4f8b981a7333b`; receipt `ctype-prefix-vm.json` SHA256 `62a1324319eddbd72f96a9e89a355b5be452b1f9717eba2dae6130325b1317a7`. Under text DD followed by x; style runs `(0,0x100),(1,0)`; `record=1`; and a synthetic `TextRez` entry named BD/id 42, changing only RAM at DGROUP:79FC from 0 to 3 changes original hotspot count from 0 to 1. Reconstructed C agrees with the original in both states; original draw trace remains DD. The probe explicitly excludes shipped-resource reachability, actual game execution, heap placement, source acceptance, and raster claims. The synthetic catalogue entry is not the canonical source table.
- Canonical `fd_4EE5_0500` (`src/S23/m39C7.c:57-84`) contains uppercase ASCII names. DOS `WinPrintf` is a one-byte `RETF` (`root:277D:000A`; `src/root/m277D.c`), so the error diagnostic is not a DOS-visible effect. Do not report the synthetic BD witness as evidence that a shipped resource or the canonical static catalogue has that entry.

## Other current ctype sites: raw access vs result relevance

| Site | Original access/domain | Assessment |
|---|---|---|
| `src/root/m1C62.c:170`, `f_1C62_00D5`, original `root:1C62:00D5+0278` | `f_1F58_005A` returns sign-extended BIOS AL (`CBW` in `src/root/m1F58.asm:86-106`). For input bytes 80-FF interpreted as signed char, `_ctype[c+1]` can read DGROUP:799F..7A1D for c=-128..-2. | Raw prefix read. If the flag subtracts 20h, both values remain negative; the following switch only recognizes C, LF, CR, so its dispatch is unchanged. |
| `src/root/m1C62.c:302`, `f_1C62_0415`, original `root:1C62:0415+05F1` | `f_1F58_0090` packs an extended BIOS scan code as positive `0x800|scan`; the `c<=0` branch excludes sign-extended high ASCII but allows positive extended codes. `_ctype[c+1]` can read DGROUP:821F..831E. | Raw suffix read outside the 257-byte owner. Subtracting 20h still leaves an extended value; it cannot match the ASCII button labels. The caller's S10 helper `o10_35F5_0A63` only acts on `+` or `-`. Strict cases do not prove extended-key runtime reachability. |
| `src/S10/m35F5.c:304`, original `S10:35F5:0384+07CE` | `islower(key)` follows `TEST AH,8`; sign-extended high bytes and 0x8xx extended codes are skipped. | No high-byte/special-key prefix read on this path. |
| `src/S10/m35F5.c:324`, original `S10:35F5:0384+083E` | `isalpha(key)` follows `TEST SI,800h` and the special-key branch. | Key-domain guard keeps ctype input in the ordinary key range. |
| `src/S10/m35F5.c:350`, original `S10:35F5:0384+08B9` | `islower(c)` where c is the second byte of a far menu item; original code sign-extends the byte before indexing. No source guard or accepted menu-byte domain proof found. | Raw prefix read is possible for high-byte resource item data. The converted high-byte remains negative and cannot equal the guarded ordinary key; do not infer a menu/UI behavior change. |

## Owner and existing evidence limits

- `layout/manifest.json` SHA256 `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50` records the stock `llibcr.lib` `ctype.asm` `_DATA` member as 257 bytes. `layout/symbols.json` SHA256 `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125` pins `_ctype` at 55B3:7A1E; owner range is 7A1E..7B1E. This stock member does not own prefix 799F..7A1D or suffix 7B1F onward, and its presence does not promise neighboring placement after independent linking.
- Fresh strict source pins: `build/source-only-dos-v35/sources/U034.c` SHA256 `c9a26f97557c8a1b9cd4db0c17eb910787e7719aec0499041dcfd2c69eee1301` (S23 renderer), `U088.c` SHA256 `3acba3b8e221d554b0ec7b2e26870389682ae9db629ca882b9e95d22adfc4d36` (root m1C62 sites), `U019.c` SHA256 `e68eeb865aedf6ff9e2f72ec9fa3f3ab620ed0dd788ec967c59cf6f8f92fdf99` (S10 sites).
- Existing static receipts: `win_PrintStyleTextInRect.json` SHA256 `ba6c9d3f06c6327a55273efa2b5181df3338c7af346d80b4c0cf327235e43ed0`, `f_1C62_0415.json` SHA256 `b6494106b027cdc91f1f53c3afbf9d479853658f50bff8d975fda7eb6aa7de59`, and `o10_35F5_0384.json` SHA256 `beebdbfcfed76215fe7dbf69a61801b9142aef6686f7fdb3508e3342edb4a0c8` claim static algorithm/effect coverage under their stated function-entry and pointer assumptions. Their finite differential cases are corroboration, not proof of resource/input domains or the independent linker's neighboring data layout.

## Source and oracle pins

- `src/S23/m39C7.c`: `4e2ff0a4d57f3159b2fb58ff64c77bb7740e2a415292cc7f2fe9fad095daf4`
- `src/root/m24AB.c`: `1d263c6e1f242981d7c3e37d839dc481dc75deed45d7d1bcaaa075cad124de7f`
- `src/root/m25E7.c`: `6ec2aa7322e88e2b3f1aabc4f18b749ec21867d950424b6fc7c42e35fbcc6530`
- `src/root/m1C62.c`: `927309d2bf5019e17e58962c7da6a0d45298a2f3bf18fef0b0347cc4498ada6c`
- `src/root/m1F58.asm`: `9f314c6e964bcb0955c1f3e976819bdbeddf048781c1bb257c30b2c0b25d49d2`
- `src/S10/m35F5.c`: `69be1d6a9649e99102131c702e1920b6e84acc0c1b4cd737d2a047552f917ed5`
- Oracle identity: `assets/SIMANT.EXE` SHA256 `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`; `layout/oracle.lock.json` SHA256 `2c6d9e98c688621ad49a08c78d0e0968f4076b036be56ec0738217b533ccde13`.