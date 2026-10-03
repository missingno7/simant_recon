#!/usr/bin/env python3
"""Verify saved cursor pixel stages emitted by capture.gdb (no asset files needed)."""
import argparse
from pathlib import Path

SCREEN_W = 640
SCREEN_H = 480
X = 288
Y = 234


def read(path: Path, expected: int) -> bytes:
    data = path.read_bytes()
    if len(data) != expected:
        raise SystemExit(f"{path}: expected {expected} bytes, got {len(data)}")
    return data


def crop(frame: bytes, x: int, y: int, width: int, height: int) -> bytes:
    return bytes(frame[(y + row) * SCREEN_W + x + col]
                 for row in range(height) for col in range(width))


def planar4(payload: bytes, width: int, height: int) -> bytes:
    row_bytes = (width + 7) // 8
    if len(payload) != row_bytes * 4 * height:
        raise ValueError("unexpected four-plane payload length")
    out = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            bit = 7 - (x & 7)
            value = 0
            for plane in range(4):
                offset = y * row_bytes * 4 + plane * row_bytes + x // 8
                value |= ((payload[offset] >> bit) & 1) << plane
            out[y * width + x] = value
    return bytes(out)


def mono(payload: bytes, width: int, height: int) -> bytes:
    row_bytes = (width + 7) // 8
    if len(payload) != row_bytes * height:
        raise ValueError("unexpected one-plane payload length")
    return bytes((payload[y * row_bytes + x // 8] >> (7 - (x & 7))) & 1
                 for y in range(height) for x in range(width))


def equal(label: str, actual: bytes, expected: bytes, counts: dict) -> None:
    if len(actual) != len(expected):
        raise SystemExit(f"{label}: length differs {len(actual)} vs {len(expected)}")
    mismatches = sum(a != b for a, b in zip(actual, expected))
    print(f"{label}: pixels={len(actual)} mismatches={mismatches}")
    counts[label] = mismatches
    if mismatches:
        raise SystemExit(f"{label}: mismatch")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scratch", type=Path, help="GDB output directory named in capture.gdb")
    args = ap.parse_args()
    p = args.scratch
    counts = {}
    mask = mono(read(p / "mask1-payload.bin", 32), 16, 16)
    image = planar4(read(p / "g914c1-payload.bin", 128), 16, 16)
    save_unders = []

    for n in range(1, 4):
        capture_screen = read(p / f"cap{n}-screen-before.bin", SCREEN_W * SCREEN_H)
        save_under = read(p / f"mask{n}-save-under.bin", 196)
        if save_under[:4] != bytes((24, 0, 16, 0)):
            raise SystemExit(f"save-under {n}: unexpected dimension header {save_under[:4].hex()}")
        decoded_capture = planar4(save_under[4:], 24, 16)
        equal(f"capture-{n}", decoded_capture,
              crop(capture_screen, X, Y, 24, 16), counts)
        save_unders.append(save_under)

        mask_screen = read(p / f"mask{n}-screen-before.bin", SCREEN_W * SCREEN_H)
        mask_input = crop(mask_screen, X, Y, 16, 16)
        expected_mask = bytes(value & (15 if bit else 0)
                              for value, bit in zip(mask_input, mask))
        after_mask_frame = read(p / f"g914c{2*n-1}-frame-before.bin", SCREEN_W * SCREEN_H)
        equal(f"mask-and-{n}", crop(after_mask_frame, X, Y, 16, 16),
              expected_mask, counts)

        after_image_frame = read(p / f"g914c{2*n-1}-frame-after.bin", SCREEN_W * SCREEN_H)
        expected_image = bytes(a ^ b for a, b in zip(expected_mask, image))
        equal(f"image-xor-{n}", crop(after_image_frame, X, Y, 16, 16),
              expected_image, counts)

        if n < 3:
            restore_payload = read(p / f"g914c{2*n}-payload.bin", 192)
            equal(f"restore-payload-{n}", restore_payload, save_under[4:], counts)
            restored_frame = read(p / f"g914c{2*n}-frame-after.bin", SCREEN_W * SCREEN_H)
            equal(f"restore-frame-{n}", crop(restored_frame, X, Y, 24, 16),
                  decoded_capture, counts)

    for n in (2, 3):
        equal(f"capture-repeat-{n-1}-{n}", save_unders[n-2], save_unders[n-1], counts)
    print(f"PASS comparisons={len(counts)} total_mismatches={sum(counts.values())}")


if __name__ == "__main__":
    main()
