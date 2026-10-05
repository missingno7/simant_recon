from __future__ import annotations
import hashlib
SOURCE = 'src/root/m1E57.c'
OLD = 'f_171C_1A9E(size + 8L, 1, "clip_Push")'
NEW = 'f_171C_1A9E(size + (long)(2 * sizeof(Handle)), 1, "clip_Push")'

def adapt(source: str, rel: str) -> tuple[str, dict | None]:
    if rel != SOURCE:
        return (source, None)
    if source.count(OLD) != 1:
        raise ValueError('clip-stack allocation anchor changed')
    result = source.replace(OLD, NEW, 1)
    return (result, {'kind': 'NATIVE_CLIP_STACK_HEADER_WIDTH', 'source': SOURCE, 'input_sha256': hashlib.sha256(source.encode()).hexdigest(), 'output_sha256': hashlib.sha256(result.encode()).hexdigest(), 'changes': 'two native pointer slots replace the original eight-byte DOS header allocation; node fields, payload, Push/Pop order unchanged', 'claim': 'native pointer-width conversion only; no historical acceptance change'})
