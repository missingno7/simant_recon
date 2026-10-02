#!/usr/bin/env python3
"""Exercise the typed zoom adapter with the actual HCEGANT window-0 record."""
from __future__ import annotations

import ctypes as ct
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_helpers():
    path = ROOT / "portable/tests/windows/evidence/differential_window.py"
    spec = importlib.util.spec_from_file_location("window_resource_helpers_v3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Rect(ct.Structure):
    _fields_ = [(field, ct.c_int16) for field in ("left", "top", "right", "bottom")]


class Object(ct.Structure):
    _fields_ = [
        ("resource_offset", ct.c_uint16), ("resource_size", ct.c_uint16),
        ("rect", Rect), ("offsets", ct.c_int16 * 4),
        ("group", ct.c_uint8), ("type", ct.c_uint8),
        ("flags", ct.c_uint16), ("value", ct.c_uint16),
        ("indices", ct.c_int16 * 4), ("modes", ct.c_int16 * 4),
        ("resource_bytes", ct.POINTER(ct.c_uint8)),
        ("bitmap_override", ct.c_int16), ("has_bitmap_override", ct.c_uint8),
    ]


class WindowResource(ct.Structure):
    _fields_ = [
        ("resource_id", ct.c_int16), ("count", ct.c_uint16),
        ("rect", Rect), ("flags", ct.c_uint16),
        ("record_bytes", ct.POINTER(ct.c_uint8)), ("record_size", ct.c_size_t),
        ("objects", ct.POINTER(Object)),
    ]


class ZoomState(ct.Structure):
    _fields_ = [
        ("window_rect", Rect), ("frame_rect", Rect), ("zoom_rect", Rect),
        ("flags", ct.c_uint16), ("min_width", ct.c_int16),
        ("min_height", ct.c_int16), ("grid_x", ct.c_int16),
        ("grid_y", ct.c_int16), ("has_zoom_rect", ct.c_uint8),
    ]


def main() -> None:
    helpers = load_helpers()
    payload, record_flags = helpers.resource_payload("HCEGANT", 0, 0)
    payload_buffer = (ct.c_uint8 * len(payload)).from_buffer_copy(payload)
    object_count = struct.unpack_from("<H", payload, 0x0c)[0]
    frame_offset = struct.unpack_from("<H", payload, 0x2c)[0]
    frame = Object()
    frame.resource_offset = frame_offset
    frame.offsets[:] = struct.unpack_from("<4h", payload, frame_offset + 8)
    objects = (Object * object_count)()
    objects[0] = frame
    resource = WindowResource()
    resource.resource_id = 0
    resource.count = object_count
    resource.rect = Rect(*struct.unpack_from("<4h", payload, 0))
    resource.flags = struct.unpack_from("<H", payload, 0x1c)[0]
    resource.record_bytes = ct.cast(payload_buffer, ct.POINTER(ct.c_uint8))
    resource.record_size = len(payload)
    resource.objects = ct.cast(objects, ct.POINTER(Object))

    build_dir = ROOT / "build/workers/behavior_sim_contracts"
    build_dir.mkdir(parents=True, exist_ok=True)
    library_path = build_dir / "zoom-resource-adapter-v3.dll"
    command = [shutil.which("gcc"), "-std=c11", "-Wall", "-Wextra", "-Werror",
               "-shared", "-fPIC", "-I", str(ROOT / "portable/ui_model/windows"),
               str(ROOT / "portable/ui_model/windows/zoom.c"), "-o", str(library_path)]
    if command[0] is None:
        raise RuntimeError("gcc is unavailable")
    subprocess.run(command, cwd=ROOT, check=True)
    library_hash = sha(library_path.read_bytes())
    library = ct.CDLL(str(library_path))
    initialize = library.portable_window_zoom_state_from_resource
    initialize.argtypes = [ct.POINTER(ZoomState), ct.POINTER(WindowResource), Rect, ct.c_uint16]
    initialize.restype = ct.c_int

    state = ZoomState()
    status = initialize(ct.byref(state), ct.byref(resource), Rect(14, 22, 418, 379), 0x070e)
    observed = {
        "status": status,
        "window_rect": [state.window_rect.left, state.window_rect.top,
                        state.window_rect.right, state.window_rect.bottom],
        "frame_xywh": [state.frame_rect.left, state.frame_rect.top,
                       state.frame_rect.right, state.frame_rect.bottom],
        "runtime_flags": state.flags,
        "minimum_size": [state.min_width, state.min_height],
        "grid": [state.grid_x, state.grid_y],
        "zoom_rect_initialized": bool(state.has_zoom_rect),
    }
    expected = {
        "status": 0, "window_rect": [14, 22, 418, 379],
        "frame_xywh": [14, 22, 404, 357], "runtime_flags": 0x070e,
        "minimum_size": [252, 280], "grid": [16, 16],
        "zoom_rect_initialized": False,
    }
    if observed != expected:
        raise AssertionError({"expected": expected, "observed": observed})

    # Invalid resource is rejected before modifying caller state.
    before = bytes(state)
    resource.count = 0
    invalid_status = initialize(ct.byref(state), ct.byref(resource), Rect(1, 2, 3, 4), 7)
    if invalid_status != 1 or bytes(state) != before:
        raise AssertionError("invalid-resource rejection mutated zoom state")

    report = {
        "schema": "portable-window-zoom-resource-adapter-host-repaint-v3",
        "status": "PASS",
        "claim": "The typed adapter maps the decoded actual HCEGANT resource-0 profile plus live runtime Win.rect/flags to zoom state. The SDL host repaint policy is full z-order redraw after geometry changes; it intentionally does not reproduce the source clip-list union of the uninitialized saved Rect.",
        "resource": {
            "database": "HCEGANT", "resource_id": 0, "kind": 0,
            "record_flags": record_flags, "payload_sha256": sha(payload),
            "payload_size": len(payload), "object_count": object_count,
            "minimum_size": [252, 280], "grid": [16, 16],
            "source_flags": 0x050e, "runtime_open_flags": 0x070e,
        },
        "adapter": {"observed": observed, "expected": expected,
                    "invalid_resource_status": invalid_status,
                    "invalid_resource_preserved_state": True},
        "host_repaint_contract": {
            "policy_enum": "PORTABLE_WINDOW_ZOOM_HOST_REPAINT_FULL_Z_ORDER",
            "behavior": "After geometry success, redraw all open windows in current z-order or repaint the full logical surface.",
            "not_claimed": ["DOS clip-list trace equivalence", "a synthesized saved Rect", "a NewGame caller stack value"],
        },
        "pins": {
            "zoom_source_sha256": sha((ROOT / "portable/ui_model/windows/zoom.c").read_bytes()),
            "zoom_header_sha256": sha((ROOT / "portable/ui_model/windows/zoom.h").read_bytes()),
            "native_test_source_sha256": sha((ROOT / "portable/tests/windows_zoom/test_zoom.c").read_bytes()),
            "native_library_sha256": library_hash,
            "resource_helper_sha256": sha((ROOT / "portable/tests/windows/evidence/differential_window.py").read_bytes()),
            "hcegant_ndx_sha256": sha((ROOT / "assets/HCEGANT.NDX").read_bytes()),
            "hcegant_dat_sha256": sha((ROOT / "assets/HCEGANT.DAT").read_bytes()),
        },
    }
    out = ROOT / "portable/tests/windows_zoom/evidence/adapter-host-repaint-v3.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{out}: adapter and invalid-input check passed")


if __name__ == "__main__":
    main()
