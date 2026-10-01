from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build" / "workers" / "fleet_memory"
sys.path.insert(0, str(ROOT / "tools"))

import autosearch  # noqa: E402
import modctx  # noqa: E402


BASE = (OUT / "memory.c").read_text(encoding="utf-8")

PROBES = [
    (
        "f_171C_09CC",
        "next_result_lifetime",
        "After the guard, overwrite the neighbor local with the far pointer returned by f_0160 and pass that value to f_068C.",
        "f_171C_068C(f_171C_0160(b, 0), paras, type);",
        "next = f_171C_0160(b, 0);\n    f_171C_068C(next, paras, type);",
    ),
    (
        "f_171C_0ADC",
        "next_argument_lifetime",
        "Compute the next block once, pass the same real far pointer and its paragraph count to the mover, then overwrite n in its later list-neighbor phase.",
        "f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);",
        "n = NEXTBLK(b);\n    f_194D_0006(b, n, n->paras);",
    ),
    (
        "f_171C_0FBC",
        "compaction_result_lifetime",
        "Store f_0CF4's real Boolean result in the existing compacted state before branching; the false value is reset by the existing fallback path and true continues with first=1.",
        "if (s_2F3E > paras && f_171C_0CF4(0)) {\n                first = compacted = 1;",
        "if (s_2F3E > paras && (compacted = f_171C_0CF4(0))) {\n                first = 1;",
    ),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    report = []
    for function, label, hypothesis, old, new in PROBES:
        negative = autosearch.unscaffold(BASE, function)
        if old not in negative:
            raise SystemExit(f"expected source expression missing for {function}")
        positive = negative.replace(old, new, 1)
        if positive == negative:
            raise SystemExit(f"hypothesis did not change {function}")
        neg_path = OUT / f"{function}-negative.c"
        pos_path = OUT / f"{function}-{label}.c"
        neg_path.write_text(negative, encoding="utf-8", newline="\n")
        pos_path.write_text(positive, encoding="utf-8", newline="\n")

        ctx = modctx.resolve(func=function)
        evaluator = autosearch.Evaluator(ctx, function, 2, OUT / f"cache-{function}")
        results = evaluator.many([negative, positive])
        evaluator.save()
        rows = []
        for name, source, result, path in zip(
            ("negative", "positive"), (negative, positive), results, (neg_path, pos_path)
        ):
            row = {
                "variant": name,
                "hypothesis": hypothesis,
                "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_sha256": sha(source),
                "compile_ok": result.get("compile_ok"),
                "length": result.get("length"),
                "target_exact": result.get("exact"),
                "module_exact": result.get("module_exact"),
                "reasons": result.get("reasons", []),
                "peer_losses": [k for k, v in result.get("claims", {}).items() if not v and k != function],
                "data_losses": [k for k, v in result.get("data", {}).items() if not v],
                "fixups": result.get("fixups"),
                "relocations": result.get("relocations"),
                "reloc_order": result.get("reloc_order"),
                "score": result.get("score"),
            }
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
        report.append({"function": function, "probe": label, "hypothesis": hypothesis, "variants": rows})

    (OUT / "search-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
