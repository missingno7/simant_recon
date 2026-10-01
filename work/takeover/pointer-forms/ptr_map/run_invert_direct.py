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
BASE_SHA256 = hashlib.sha256(BASE.encode("latin1")).hexdigest()

BODY = csrc.Source(BASE).function(NAME)
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
    if form == "plus":
        h_lvalue, v_lvalue = "(pts + i)->h", "(pts + i)->v"
    else:
        h_lvalue, v_lvalue = "(&pts[i])->h", "(&pts[i])->v"
    h = f"            {h_lvalue} = g_2A42[i * 2]{coordinate} + org.h;"
    v = f"            {v_lvalue} = g_2A42[i * 2 + 1]{coordinate} + v;"
    stores = [h, v] if order == "hv" else [v, h]
    return "        for (i = 0; i < 4; i++) {\n" + "\n".join(stores) + "\n        }"


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"expected one source occurrence, found {source.count(old)}: {old[:60]!r}")
    return source.replace(old, new, 1)


specs = []
for f320, fother, o320, oother in itertools.product(FORMS, FORMS, ORDERS, ORDERS):
    tag = f"direct-m320-{f320}-{o320}_other-{fother}-{oother}"
    body = BASE[BODY.body.s:BODY.body.e]
    body = replace_once(body, LOOP_320, loop(f320, o320, " / 2"))
    body = replace_once(body, LOOP_OTHER, loop(fother, oother, ""))
    text = BASE[:BODY.body.s] + body + BASE[BODY.body.e:]
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
    "hypothesis": "Use the local point array through direct member-pointer lvalues (pts + i)->field or (&pts[i])->field, without a pointer local; vary field store order independently in each branch.",
    "target_listing_anchor": "Both loops use one i*4-derived offset for reads from the global point pair and writes to adjacent local struct fields at BP+SI-16/BP+SI-14.",
    "base_sha256": BASE_SHA256,
    "variant_count": len(specs),
    "jobs": 2,
    "variants": specs,
}
(OUT / "direct-variants.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

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
(OUT / "direct-results.json").write_text(json.dumps({
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
