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


NAME = "InvertPatch"
OUT = Path(__file__).resolve().parent
CTX = modctx.resolve(func=NAME)
CANONICAL = (OUT / "canonical-S13-m384C.c").read_text(encoding="latin1")
BASE = autosearch.unscaffold(CANONICAL, NAME)

RAW_PATH = OUT / "canonical-S13-m384C.c"
BASE_PATH = OUT / "base.c"
RAW_PATH.write_text(CANONICAL, encoding="latin1", newline="\n")
BASE_PATH.write_text(BASE, encoding="latin1", newline="\n")

BODY = csrc.Source(BASE).function(NAME)
body_text = BASE[BODY.body.s:BODY.body.e]
LOOP_320 = """        for (i = 0; i < 4; i++) {
            pts[i].h = g_2A42[i * 2] / 2 + org.h;
            pts[i].v = g_2A42[i * 2 + 1] / 2 + v;
        }"""
LOOP_OTHER = """        for (i = 0; i < 4; i++) {
            pts[i].h = g_2A42[i * 2] + org.h;
            pts[i].v = g_2A42[i * 2 + 1] + v;
        }"""

FORMS = ("plus", "address_of_index")
ORDERS = ("hv", "vh")


def loop(form: str, order: str, coordinate: str) -> str:
    index = "i"
    point = "point"
    init = f"            {point} = pts + {index};" if form == "plus" else f"            {point} = &pts[{index}];"
    h = f"            {point}->h = g_2A42[{index} * 2]{coordinate} + org.h;"
    v = f"            {point}->v = g_2A42[{index} * 2 + 1]{coordinate} + v;"
    fields = [h, v] if order == "hv" else [v, h]
    return "        for (i = 0; i < 4; i++) {\n" + init + "\n" + "\n".join(fields) + "\n        }"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"expected one source occurrence, found {source.count(old)}: {old[:60]!r}")
    return source.replace(old, new, 1)


point_decl = "    struct Pt pts[4];\n    struct Pt org;\n    int i, h, v;"
if BASE.count(point_decl) != 1:
    raise RuntimeError("target declaration anchor changed")

specs = []
for f320, fother, o320, oother in itertools.product(FORMS, FORMS, ORDERS, ORDERS):
    tag = f"m320-{f320}-{o320}_other-{fother}-{oother}"
    text = BASE.replace(point_decl, "    struct Pt pts[4];\n    struct Pt org;\n    struct Pt *point;\n    int i, h, v;", 1)
    body = text[BODY.body.s:BODY.body.e]
    body = replace_once(body, LOOP_320, loop(f320, o320, " / 2"))
    body = replace_once(body, LOOP_OTHER, loop(fother, oother, ""))
    text = text[:BODY.body.s] + body + text[BODY.body.e:]
    path = OUT / f"{tag}.c"
    path.write_text(text, encoding="latin1", newline="\n")
    specs.append({"name": tag, "source": str(path.relative_to(ROOT)),
                  "form_320": f320, "store_order_320": o320,
                  "form_other": fother, "store_order_other": oother,
                  "sha256": hashlib.sha256(text.encode("latin1")).hexdigest()})

if len(specs) != 16:
    raise RuntimeError(f"expected 16 variants, found {len(specs)}")

metadata = {
    "function": NAME,
    "module": CTX.key,
    "semantic_counterpart": "D:/Prog/simantw_recon/src/recovered/tu_antedit_C19C_DrawMapCursor_1_scaffold-bae9e2044a.c",
    "hypothesis": "The output point array is a real local struct array. The two resolution loops may address each member through a used struct pointer initialized by pts + i or &pts[i]; field store order is tested independently in each loop.",
    "target_listing_anchor": "InvertPatch uses one i*4 byte offset for both global point reads and [bp+si-0x16]/[bp+si-0x14] local point writes; the call receives the array base via LEA.",
    "raw_sha256": hashlib.sha256(CANONICAL.encode("latin1")).hexdigest(),
    "base_sha256": hashlib.sha256(BASE.encode("latin1")).hexdigest(),
    "variant_count": len(specs),
    "jobs": 2,
    "variants": specs,
}
(OUT / "variants.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

ev = autosearch.Evaluator(CTX, NAME, 2, OUT / "cache")
base_result = ev.one(BASE)
if not base_result.get("compile_ok"):
    raise RuntimeError(f"frozen base does not compile: {base_result.get('log')}")
ev.set_base(base_result)
losses = ev.regressions(base_result)
if losses:
    raise RuntimeError(f"frozen base fails accepted peer/data gate: {losses}")

texts = [Path(s["source"]).read_text(encoding="latin1") for s in specs]
results = ev.many(texts)
ev.save()
rows = []
for spec, result in zip(specs, results):
    regressions = ev.regressions(result)
    rows.append({**spec, **result, "regressions": regressions,
                 "peer_data_preserved": not regressions})
(OUT / "results.json").write_text(json.dumps({
    "metadata": metadata,
    "base": {"sha256": metadata["base_sha256"], **base_result,
             "regressions": losses, "peer_data_preserved": True},
    "rows": rows,
}, indent=2), encoding="utf-8")

for row in rows:
    print(f"{row['name']}: target_exact={row.get('exact')} all_exact={row.get('all_exact')} "
          f"score={row.get('score')} peers_data={row['peer_data_preserved']} "
          f"regressions={row['regressions']}")
print(f"base_sha256={metadata['base_sha256']} variants={len(rows)} jobs=2")
