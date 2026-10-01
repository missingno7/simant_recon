from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import autosearch  # noqa: E402
import csrc  # noqa: E402
import modctx  # noqa: E402


NAME = "DrawMapCursor"
OUT = Path(__file__).resolve().parent
CTX = modctx.resolve(func=NAME)
CANONICAL = (OUT / "cursor-canonical-S12-m384C.c").read_text(encoding="latin1")
BASE = autosearch.unscaffold(CANONICAL, NAME)
BASE_SHA256 = hashlib.sha256(BASE.encode("latin1")).hexdigest()
(OUT / "cursor-canonical-S12-m384C.c").write_text(CANONICAL, encoding="latin1", newline="\n")
(OUT / "cursor-base.c").write_text(BASE, encoding="latin1", newline="\n")
BODY = csrc.Source(BASE).function(NAME)

BODY_START = "{\n    if (!f_22BF_09B0(0x100) || g_298E != 0)"
DECL = "    clip_SetWin(0x100);"
TOP = "    fd_50F6_38C2.top = fd_50F6_3858 * fd_50F6_0508[1] + fd_50F6_10D2.top;"
LEFT = "    fd_50F6_38C2.left = fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left + fd_50F6_38C0;"


def address(form: str, index: int) -> str:
    return f"fd_50F6_0508 + {index}" if form == "plus" else f"&fd_50F6_0508[{index}]"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"expected one source occurrence, found {source.count(old)}: {old!r}")
    return source.replace(old, new, 1)


specs = []
for top_form, left_form in itertools.product(("plus", "address_of_index"), repeat=2):
    tag = f"scale-top-{top_form}_left-{left_form}"
    body = BASE[BODY.body.s:BODY.body.e]
    body = replace_once(body, BODY_START, "{\n    int far *scale;\n    if (!f_22BF_09B0(0x100) || g_298E != 0)")
    top = f"    scale = {address(top_form, 1)};\n" + TOP.replace("fd_50F6_0508[1]", "*scale")
    left = f"    scale = {address(left_form, 0)};\n" + LEFT.replace("fd_50F6_0508[0]", "*scale")
    body = replace_once(body, TOP, top)
    body = replace_once(body, LEFT, left)
    text = BASE[:BODY.body.s] + body + BASE[BODY.body.e:]
    path = OUT / f"{tag}.c"
    path.write_text(text, encoding="latin1", newline="\n")
    specs.append({"name": tag, "source": str(path.relative_to(ROOT)),
                  "top_form": top_form, "left_form": left_form,
                  "sha256": hashlib.sha256(text.encode("latin1")).hexdigest()})

metadata = {
    "function": NAME,
    "module": CTX.key,
    "semantic_counterpart": "D:/Prog/simantw_recon/src/recovered/tu_antedit_C19C_DrawMapCursor_1_scaffold-bae9e2044a.c",
    "hypothesis": "The two DOS far-array scale words semantically correspond to Win16 mapYsize and mapXsize. A used far pointer to each word may compile differently when initialized by base + index versus &base[index].",
    "target_listing_anchor": "The target reads the scale words at frame 50F6 offsets 050A (top) and 0508 (left) through ES; Win16 source multiplies MapPnt.y/x by mapYsize/mapXsize before writing the cursor rectangle.",
    "base_sha256": BASE_SHA256,
    "variant_count": len(specs),
    "jobs": 2,
    "variants": specs,
}
(OUT / "cursor-variants.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

ev = autosearch.Evaluator(CTX, NAME, 2, OUT / "cache")
base_result = ev.one(BASE)
if not base_result.get("compile_ok"):
    raise RuntimeError(f"frozen base does not compile: {base_result.get('log')}")
ev.set_base(base_result)
base_losses = ev.regressions(base_result)
if base_losses:
    raise RuntimeError(f"frozen base fails accepted peer/data gate: {base_losses}")

rows = []
for spec, result in zip(specs, ev.many([Path(s["source"]).read_text(encoding="latin1") for s in specs])):
    losses = ev.regressions(result)
    rows.append({**spec, **result, "regressions": losses, "peer_data_preserved": not losses})
ev.save()
(OUT / "cursor-results.json").write_text(json.dumps({
    "metadata": metadata,
    "base": {"sha256": BASE_SHA256, **base_result,
             "regressions": base_losses, "peer_data_preserved": True},
    "rows": rows,
}, indent=2), encoding="utf-8")

for row in rows:
    print(f"{row['name']}: target_exact={row.get('exact')} all_exact={row.get('all_exact')} "
          f"score={row.get('score')} peers_data={row['peer_data_preserved']} "
          f"regressions={row['regressions']}")
print(f"base_sha256={BASE_SHA256} variants={len(rows)} jobs=2")
