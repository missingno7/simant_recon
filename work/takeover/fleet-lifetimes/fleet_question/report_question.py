from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).parent
payload = json.loads((ROOT / "question-results.json").read_text(encoding="utf-8"))
variants = payload["variants"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


lines = [
    "# `f_1C62_0415` question dialog search",
    "",
    "No candidate closed the 649-byte target. The pinned whole-module seed is the prior",
    "`question-loop-order-v2.c` draft, copied to `question-base.c` (653-byte target body); its",
    "manifest identity is recorded in `question-results.json`. The module compiler context is",
    f"`{payload['profile']} {' '.join(payload['flags'])}`.",
    "",
    "The baseline frame is 78 bytes, matching the target, but its body is 653 bytes / 272",
    "linear instructions against 649 / 274. The remaining mismatch is still in the loop-local",
    "layout and control flow: candidate `j` and `count` split across BP-4/BP-C where the original",
    "reuses those homes by phase; at 046C the candidate reloads BP-4 while the original uses AX,",
    "and the first and draw-loop compare branches differ (`JL` candidate versus `JG` original).",
    "`slots.py`/`diag.py` also show the c/v home merge and a missing draw-loop index reload.",
    "The earlier loop-order, coordinate, and storage series were not repeated.",
    "",
    f"Seed SHA-256 (LF-normalized): `{payload['seed_sha256_lf']}`. Manifest SHA-256: "
    f"`{payload['manifest_sha256']}`.",
    "",
    "New controls followed three source-grounded leads:",
    "",
    "- `0x900` is the real object-ID base passed to drawing, key fallback, and cleanup calls.",
    "  Four shared-local initialization placements preserve the argument values, but each grows",
    "  the target to 658 bytes and loses accepted peer `f_1C62_06A6` at the whole-module gate.",
    "- `sel` is the real default-key state: the original initializes BP-12 to -1 before setup,",
    "  then passes its address to `o10_35F5_0A63`, which reads and updates the value for later key",
    "  events. Keeping the initialization early as a declaration initializer leaves the baseline",
    "  residue unchanged. Moving the single initialization to just before the input loop preserves",
    "  state across calls and all accepted peers/data, but still gives a 653-byte mismatch.",
    "- A returned-event snapshot before cleanup tests a result live across cleanup calls; copying",
    "  only at the final return is its contrast. The early snapshot grows the target to 659 bytes,",
    "  and these result-local variants lose `f_1C62_06A6`. Splitting the first-phase spacing",
    "  accumulator from the later key variable also leaves the target inexact and loses that peer.",
    "",
    "All controls compiled. Every private-data placement (`_DATA`, `CONST`, `_BSS`) is exact in",
    "every row. A peer loss rejects that row even when its target/body distance changes.",
    "",
    "| Variant | Target verdict | Other accepted claims | Private data | Source SHA-256 (LF-normalized) |",
    "|---|---|---|---|---|",
]

for row in variants:
    result = row["result"]
    target = result.get("claims", {}).get("f_1C62_0415", {})
    reasons = "; ".join(target.get("reasons", [])) or "EXACT"
    peers = [name for name, claim in result.get("claims", {}).items()
             if name != "f_1C62_0415" and not claim.get("exact")]
    data_ok = all(item.get("exact") for item in result.get("data", {}).values())
    peer_result = "all exact" if not peers else "failed: " + ", ".join(peers)
    lines.append(f"| `{row['name']}` | {reasons} | {peer_result} | "
                 f"{'exact' if data_ok else 'mismatch'} | `{sha(row['file'])}` |")

lines += [
    "",
    "Whole-module checks used `modctx.resolve` and `variants.run(jobs=2, claims_only=True)` for",
    "root:1C62. No candidate was exact, so no `search.py` refinement or `promote.py` call was",
    "made. The generator and every compiled source are retained alongside this report.",
    "",
]
(ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
