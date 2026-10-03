"""Negative control: prove shared PCM backing aliases two live DOS voices."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "portable/tests/audio/voice_scheduler_isr_differential_v2.py"
spec = importlib.util.spec_from_file_location("voice_scheduler_v2", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.PCM_SEGS = (0xB000, 0xB000)

try:
    module.main()
except AssertionError as exc:
    fields = exc.args[0]
    if fields[0] != "mixed register" or fields[1] != 20:
        raise
    report = {
        "schema": "dos-dac-live-isr-alias-negative-v1",
        "status": "EXPECTED_MISMATCH",
        "case": "two distinct sample objects point to one shared PCM segment; SFX 2 overwrites SFX 1 backing",
        "first_mismatch_tick": fields[1],
        "dos_output": fields[2],
        "native_output": fields[4],
        "native_channel0_position": fields[5],
        "dos_channel0_position": fields[7],
        "dos_channel0_fraction": fields[8],
        "dos_sample_backing_prefix": fields[12],
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": module.sha(SOURCE),
    }
    out = ROOT / "portable/tests/audio/evidence/voice-admission-v2/alias-negative.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS expected alias mismatch tick={fields[1]} dos={fields[2]} native={fields[4]}")
else:
    raise AssertionError("alias negative control unexpectedly matched")
