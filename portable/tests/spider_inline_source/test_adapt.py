"""Validate the pre-word source adapter and its narrow compiler boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from portable.whole_program.conversions import spider_inline_source as adapter

REPORT = Path(__file__).parent / "evidence" / "source-adapt-v1.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def closure(gcc: str) -> dict[str, str]:
    files = [
        ROOT / adapter.SOURCE_RELATIVE,
        ROOT / "portable/whole_program/conversions/spider_inline_source.py",
        ROOT / "portable/whole_program/algorithms/line16b5.h",
        ROOT / "portable/tests/spider_inline_source/test_adapt.py",
    ]
    result = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in files}
    result["compiler_executable"] = sha(Path(gcc).read_bytes())
    return result


def main() -> int:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite {REPORT}")
    source_path = ROOT / adapter.SOURCE_RELATIVE
    original = source_path.read_bytes()
    adapted, receipt = adapter.adapt(original, adapter.SOURCE_RELATIVE)
    if not adapter._lexical_control():
        raise SystemExit("comment/string lexical negative control failed")

    for source, rel in ((original + b"\n", adapter.SOURCE_RELATIVE),
                        (original, "src/root/m0250_other.c")):
        try:
            adapter.adapt(source, rel)
        except ValueError:
            continue
        raise SystemExit("identity/path negative control was accepted")

    text = adapted.decode("utf-8")
    checks = {
        "old_object_extern_removed": "extern Pnt far fd_50F6_1F26;" not in text,
        "typed_owner_bound": "#include \"portable/whole_program/algorithms/line16b5.h\"" in text,
        "f2662_byte_destination": adapter._F2662_NATIVE_PROTO in text,
        "f16b5_void_prefix_abi": adapter._F16B5_NATIVE_PROTO in text,
        "f0008_dos_word_abi": adapter._F0008_NATIVE_PROTO in text,
        "explicit_owner_byte_addresses": text.count("(char far *)&portable_line16b5_source_buffer") == 8,
    }
    if not all(checks.values()):
        raise SystemExit(f"adapted output check failed: {checks}")

    gcc = shutil.which("gcc")
    if not gcc:
        raise SystemExit("gcc unavailable")
    before = closure(gcc)
    with tempfile.TemporaryDirectory(prefix="spider-inline-source-") as td:
        adapted_path = Path(td) / "m0250_adapted.c"
        adapted_path.write_bytes(adapted)
        command = [gcc, "-std=gnu11", "-Dfar=", "-Dnear=", "-fsyntax-only", "-w",
                   "-I", str(ROOT), str(adapted_path)]
        compiled = subprocess.run(command, text=True, capture_output=True)
        if compiled.returncode:
            raise SystemExit("adapted source syntax check failed\n" + compiled.stdout + compiled.stderr)
    after = closure(gcc)
    if before != after:
        raise SystemExit("source or compiler identity changed during syntax check")

    report = {
        "schema": "spider-inline-source-adapt-v1",
        "status": "pass",
        "source": {"path": adapter.SOURCE_RELATIVE, "sha256": receipt.source_sha256},
        "adapted_sha256": receipt.output_sha256,
        "owner": {"symbol": receipt.owner, "size": receipt.owner_size,
                  "pixels_offset": receipt.pixel_offset},
        "conversions": {
            "removed_Pnt_object_extern": receipt.removed_extern_count,
            "lexically_replaced_active_identifiers": receipt.replaced_code_identifiers,
            "f2662_prototype_byte_pointer": receipt.corrected_f2662_prototype_count,
            "f16b5_setup_prototype_void_pointer": receipt.corrected_f16b5_prototype_count,
            "f16b5_line_prototype_fixed_width": receipt.corrected_f0008_prototype_count,
            "explicit_f2662_bytecasts": receipt.f2662_bytecasts,
            "explicit_f16b5_setup_bytecasts": receipt.f16b5_bytecasts,
        },
        "checks": checks,
        "negative_controls": ["source byte mutation rejected", "wrong source route rejected",
                              "same spelling in C comments/string/line comment preserved"],
        "compiler": {"path": gcc, "sha256": before["compiler_executable"]},
        "command": command,
        "compiler_stdout": compiled.stdout,
        "compiler_stderr": compiled.stderr,
        "closure_before": before,
        "closure_after": after,
    }
    data = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite {REPORT}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_bytes(data)
    print(f"PASS: pre-word m0250 owner adaptation; report_sha256={sha(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
