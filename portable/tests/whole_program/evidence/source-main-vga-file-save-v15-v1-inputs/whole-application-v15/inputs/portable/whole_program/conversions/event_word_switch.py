"""Keep complete event-code switches in the original unsigned word domain.

On MSC a hexadecimal label such as 0xfa05 converts to the 16-bit controlling
type. Native int16_t promotes to a 32-bit int, so a negative code would never
match that positive native label. Treat these bit-pattern keys as uint16_t.
Masked switches already produce a positive native value and need no change.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHAPES = {
    'src/S19/m384C.c': ('switch (ev->code)', 'switch ((unsigned)ev->code)', 3),
    'src/root/m218D.c': ('switch (fd_50F6_49FA.code)',
                         'switch ((unsigned)fd_50F6_49FA.code)', 1),
}


def adapt(source: str, rel: str) -> tuple[str, dict | None]:
    if rel not in SHAPES:
        return source, None
    old, new, expected = SHAPES[rel]
    if source.count(old) != expected:
        raise ValueError(f'complete event-word switch anchors changed: {rel}')
    result = source.replace(old, new)
    return result, {
        'kind': 'NATIVE_COMPLETE_EVENT_WORD_SWITCH',
        'source': rel,
        'canonical_source_sha256': hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(),
        'input_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'output_sha256': hashlib.sha256(result.encode()).hexdigest(),
        'switches': expected,
        'changes': 'retain 16-bit event-code bit patterns across native integer promotion; labels and branches unchanged',
        'claim': 'native C integer-width conversion, no historical evidence change',
    }
