from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).parent
payload = json.loads((ROOT / "1035-results.json").read_text(encoding="utf-8"))
variants = payload["variants"]
source_hash = lambda path: hashlib.sha256(  # noqa: E731
    Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()

base_hash = source_hash(ROOT / "1035-base.c")
rows = []
for row in variants:
    result = row["result"]
    target = result.get("claims", {}).get("o25_3BA4_1035", {})
    peers = [v for n, v in result.get("claims", {}).items() if n != "o25_3BA4_1035"]
    peer_ok = all(v.get("exact") for v in peers)
    data_ok = all(v.get("exact") for v in result.get("data", {}).values())
    reasons = "; ".join(target.get("reasons", [])) or "exact"
    rows.append((row["name"], source_hash(row["file"]), result.get("compile_ok"),
                 target.get("exact", False), reasons, peer_ok, data_ok))

lines = [
    "# S25 `o25_3BA4_1035` focused search",
    "",
    "No candidate closed the target. The 281-byte body remains 92 instructions; the baseline's",
    "20-byte frame and all ten far-pointer stack words match. Its only residue is the register",
    "choice for the last field pointer: candidate `LES BX,[BP-10h]` / `PUSH ES:[BX]` at 110B/110E,",
    "original `LES SI,[BP-10h]` / `PUSH ES:[SI]`. The two differing operand bytes begin at",
    "target offset +0xD7. Other accepted S25 claims and `CONST`/`_DATA` passed in every row.",
    "",
    f"Seed: `1035-base.c`, SHA-256 (LF-normalized) `{base_hash}`. It is the frozen phase-next S25",
    "whole-module draft (`sources.json` pins the same hash and manifest identity). The phase-next",
    "field lifetime, view, folded-read and optimizer series were not repeated.",
    "",
    "The new semantic lead was separate pointer lifetimes for the same real global at the earlier",
    "draw call and later DigMyTile argument, with one initialization before the coordinate update.",
    "A near-call scalar value-result control tested the post-update argument value. Pointer aliases",
    "preserve the referenced object and read point; none changed the target into an exact match.",
    "The early draw-call pointer is the negative contrast: it leaves the original two operand bytes",
    "unchanged. No exact source or rule follows from these controls.",
    "",
    "| Variant | Compile | Target | Other accepted claims | Private data | Source SHA-256 (LF-normalized) |",
    "|---|---:|---|---|---|---|",
]
for name, digest, compiled, exact, reasons, peer_ok, data_ok in rows:
    lines.append(f"| `{name}` | {'yes' if compiled else 'no'} | "
                 f"{'EXACT' if exact else reasons} | {'all exact' if peer_ok else 'regression'} | "
                 f"{'exact' if data_ok else 'mismatch'} | `{digest}` |")

lines += [
    "",
    "Whole-module checks used `modctx.resolve` and `variants.run(jobs=2, claims_only=True)` for",
    "S25:3BA4, including all currently accepted claims and both private-data placements. The",
    "optional `o25_3BA4_1686` returned-local series was not rerun: its prior result-flow/lifetime",
    "controls already cover those broad forms and no new listing-grounded lead emerged.",
    "",
]
(ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
