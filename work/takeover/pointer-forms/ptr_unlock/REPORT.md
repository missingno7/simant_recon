# win_UnlockWin pointer/address controls

The target is **root:23AE:01DB**. `python tools/context.py win_UnlockWin` resolves the only registered `win_UnlockWin` to this row; root:21FA is its graphics caller context and has no such function. The target extent is `[01DB, 035D)`, 386 bytes. The whole-module candidate is 390 bytes; the strict gate compares the 386-byte target extent and reports the excess candidate tail.

The frozen seed is the complete `root:23AE` module source with only `win_UnlockWin` unwrapped from its scaffold. The object profile comes from the manifest: `msc600ax /AL /Os /Oe /Og /Gs /Zi`. Hashes are SHA-256:

| Artifact | SHA-256 |
|---|---|
| Canonical `src/root/m23AE.c` before drafting | `531c983e47c1f39b6be2d94bb9fa0ccc1fa557ca9ec35542178a566f4d48076c` |
| Unscaffolded whole-module seed `base.c` | `23aa124a97a2f213fcf99d0f3e9790e2a35813ee5e62d338f7ef205c5b03acc0` |
| `generate_forms.py` | `c2ba91a8f49036e1e15d0a3d5931b444ee36dab63fa15681c1f82c27fb098797` |
| `generate_repeated.py` | `A514D2D41B53636D7D5AEF8EC71F516F3DACFAB998D6D6E59E00FF57A4CE64CA` |

## Reproduction

Run from `D:\Prog\simant_recon` in PowerShell. The first command makes the scratch seed; the second unwraps the target in place while retaining the accepted peers and the rest of the module.

```powershell
python tools/context.py win_UnlockWin
Copy-Item src/root/m23AE.c build/workers/ptr_unlock/base.c
python -c "import sys; sys.path.insert(0,'tools'); import autosearch; from pathlib import Path; p=Path('build/workers/ptr_unlock/base.c'); s=p.read_text(encoding='latin1'); u=autosearch.unscaffold(s,'win_UnlockWin'); p.write_bytes(u.encode('latin1'))"
python build/workers/ptr_unlock/generate_forms.py
python build/workers/ptr_unlock/generate_repeated.py
```

Both generators evaluate complete module files through `autosearch.Evaluator` with `jobs=2`; their candidate variants and per-row source hashes are recorded in `expression-address-results.json` and `repeated-object-expression-results.json`. The first group has ten variants: indexed pointer addition, address-of-first-element plus index, typed inline-list base expressions, unsigned/reversed index forms, and equivalent stored-list-base forms. The second group has eight variants: assign the indexed object in the switch expression, repeat the typed object expression in switch/field-address expressions, or retain the local object pointer while varying the field-address expression.

The diagnostic recheck command was:

```powershell
python tools/search.py win_UnlockWin build/workers/ptr_unlock/base.c build/workers/ptr_unlock/member_add.c build/workers/ptr_unlock/typed_byte_base_add.c build/workers/ptr_unlock/switch_assign_index.c build/workers/ptr_unlock/switch_assign_add.c --quiet
```

The baseline whole-module gate was:

```powershell
python tools/promote.py build/workers/ptr_unlock/base.c --module root:23AE --claim win_UnlockWin --verify-only
```

It refused the target claim, as expected. No candidate was exact, so no candidate verify-only or promotion was run.

## Results and limits

All 18 variants compiled. None matched the target. Every existing claim in the module remained exact, and `_DATA` (203 bytes), `CONST` (2 bytes), and `_BSS` (225 bytes) stayed exact in every whole-module gate row. The baseline gate reports `win_UnlockWin` at 390 versus 386 bytes, first differing byte `+0x5`, 207 differing bytes, and the same seven relocation entries in each side. `search.py` rechecked the baseline and four representative forms: each was 390 versus 386 bytes, 150 versus 151 instructions, with opcode similarity 0.957.

The controls preserved the source's branches, calls, and stores. Typed address forms that spell the observed inline-list base depend on the grounded `0x2c` field offset. Pointer-index forms rely on the existing one-element trailing-array layout and valid nonnegative loop indices. These are value-equivalent source hypotheses within that layout and loop domain; the failed results establish neither the original source expression nor exclusion of MSC output. They provide no basis for assembly classification.
