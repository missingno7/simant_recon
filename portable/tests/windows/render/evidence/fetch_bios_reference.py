#!/usr/bin/env python3
"""Fetch and extract DOSBox Staging reference BIOS glyph tables into build/."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
COMMIT = "7b40053b7ac580843d0461eba8c36a47a990e66c"
RELEASE_TAG = "v0.83.0"
REPOSITORY = "https://github.com/dosbox-staging/dosbox-staging"
RAW = f"https://raw.githubusercontent.com/dosbox-staging/dosbox-staging/{COMMIT}"
SOURCE_PATH = "src/ints/int10_memory.cpp"
LICENSE_PATH = "LICENSE"
DEFAULT_DIR = ROOT / "build" / "bios-reference" / "dosbox-staging-v0.83.0"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "simant-bios-reference-loader/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"download returned HTTP {response.status}: {url}")
        return response.read()


def extract_array(source: str, name: str, height: int) -> bytes:
    pattern = (rf"uint8_t\s+{re.escape(name)}\s*\[\s*256\s*\*\s*{height}\s*\]"
               rf"\s*=\s*\{{(.*?)\}}\s*;")
    match = re.search(pattern, source, flags=re.DOTALL)
    if match is None:
        raise RuntimeError(f"could not find expected {name}[256 * {height}] initializer")
    body = re.sub(r"/\*.*?\*/|//[^\r\n]*", "", match.group(1), flags=re.DOTALL)
    tokens = re.findall(r"0[xX][0-9a-fA-F]+|(?<![\w])\d+(?![\w])", body)
    values = bytes(int(token, 0) for token in tokens)
    expected = 256 * height
    if len(values) != expected:
        raise RuntimeError(f"{name}: parsed {len(values)} bytes, expected {expected}")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DIR,
                        help="generated assets are written beneath build/ by default")
    args = parser.parse_args()
    outdir = args.output_dir.resolve()
    outdir.relative_to((ROOT / "build").resolve())
    outdir.mkdir(parents=True, exist_ok=True)

    source_url = f"{RAW}/{SOURCE_PATH}"
    license_url = f"{RAW}/{LICENSE_PATH}"
    source = fetch(source_url)
    license_text = fetch(license_url)
    source_text = source.decode("utf-8")
    font8 = extract_array(source_text, "int10_font_08", 8)
    font14 = extract_array(source_text, "int10_font_14", 14)
    if b"GPL-2.0-or-later" not in license_text:
        raise RuntimeError("upstream license text did not match the documented GPL-2.0-or-later grant")

    source_file = outdir / "int10_memory.cpp"
    license_file = outdir / "DOSBox-Staging-LICENSE"
    font8_file = outdir / "font-8x8.bin"
    font14_file = outdir / "font-8x14.bin"
    source_file.write_bytes(source)
    license_file.write_bytes(license_text)
    font8_file.write_bytes(font8)
    font14_file.write_bytes(font14)
    manifest = {
        "schema": "bios-font-reference-source-v1",
        "source_identity": {
            "project": "DOSBox Staging",
            "repository": REPOSITORY,
            "release_tag": RELEASE_TAG,
            "immutable_commit": COMMIT,
            "license": "GPL-2.0-or-later",
            "license_url": license_url,
        },
        "extraction": {
            "source_path": SOURCE_PATH,
            "source_url": source_url,
            "arrays": {
                "int10_font_08": {"dimensions": "256 glyphs x 8 rows", "bytes": len(font8),
                                  "sha256": sha(font8), "generated_path": font8_file.name},
                "int10_font_14": {"dimensions": "256 glyphs x 14 rows", "bytes": len(font14),
                                  "sha256": sha(font14), "generated_path": font14_file.name},
            },
            "interpretation": "Upstream DOSBox Staging reference-host BIOS tables. Not a SIMANT asset or claim about a user's physical BIOS ROM.",
        },
        "download_sha256": {
            "source": sha(source),
            "license": sha(license_text),
        },
    }
    manifest_file = outdir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(outdir),
                      "manifest": str(manifest_file),
                      "manifest_sha256": sha(manifest_file.read_bytes()),
                      "font8x8_sha256": sha(font8),
                      "font8x14_sha256": sha(font14),
                      "source_sha256": sha(source)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
