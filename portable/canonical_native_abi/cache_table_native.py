import hashlib
OLD = '_fmemset(*(table = f_171C_13CA((long)(size * 8 + 4), 0, "cachetable")), -1, (size + 1) * 4);'
NEW = '_fmemset(*(table = f_171C_13CA((long)(offsetof(CacheTable, e) + (long)size * 2 * sizeof(CacheEntry)), 0, "cachetable")), -1, offsetof(CacheTable, e) + (long)size * sizeof(CacheEntry));'

def adapt_reviewed(source: str, rel: str) -> tuple[str, dict]:
    if source.count(OLD) != 1:
        raise ValueError('expected one original cache allocation/clear expression')
    result = '#include <stddef.h>\n' + source.replace(OLD, NEW, 1)
    return (result, {'kind': 'NATIVE_CACHE_ENTRY_BANK_WIDTH', 'input_sha256': hashlib.sha256(source.encode()).hexdigest(), 'output_sha256': hashlib.sha256(result.encode()).hexdigest(), 'changes': 'Two native CacheEntry banks; clear complete key bank plus unchanged count/used header', 'claim': 'Native layout conversion only; cache lookup/eviction algorithms unchanged'})
