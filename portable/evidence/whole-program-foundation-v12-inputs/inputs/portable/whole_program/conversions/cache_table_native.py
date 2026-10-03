"""Size the source cache's two entry banks using their native union width.

The DOS union is four bytes (a pair of words or one far pointer). Its native
pointer member is wider; neither the allocation nor the key-bank clear may
retain a literal four-byte stride. Probe output is separate from DOS evidence.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/root/m1A96.c'
SOURCE_SHA = 'c57124b9d75ea77eb30158c09a71550862cf7081ceed625a2550a26a262bfdfa'
OLD = '_fmemset(*(table = f_171C_13CA((long)(size * 8 + 4), 0, "cachetable")), -1, (size + 1) * 4);'
NEW = ('_fmemset(*(table = f_171C_13CA((long)(offsetof(CacheTable, e) + '
       '(long)size * 2 * sizeof(CacheEntry)), 0, "cachetable")), -1, '
       'offsetof(CacheTable, e) + (long)size * sizeof(CacheEntry));')

def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    if rel != SOURCE or hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('frozen cache table source identity mismatch')
    if source.count(OLD) != 1:
        raise ValueError('expected one original cache allocation/clear expression')
    result = '#include <stddef.h>\n' + source.replace(OLD, NEW, 1)
    return result, {'kind': 'NATIVE_CACHE_ENTRY_BANK_WIDTH',
        'source_sha256': SOURCE_SHA,
        'input_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'output_sha256': hashlib.sha256(result.encode()).hexdigest(),
        'changes': 'Two native CacheEntry banks; clear complete key bank plus unchanged count/used header',
        'claim': 'Native layout conversion only; cache lookup/eviction algorithms unchanged'}
