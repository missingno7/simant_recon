"""Project DOS SaveRec spans from named native owners, without native adjacency.

Every slice needs an actual observed owner extent. Gaps and conflicting overlaps
are debt, not padding or zero-fill. Actual native SaveRec bytes are kept separately.
"""
import re


def project_save(schema, specs, symbols):
    owners = []
    for name, item in symbols.items():
        spec = specs[name]
        if item['status'] != 'OK' or spec.get('native_expr') or \
                spec.get('owner', name) != name or '::' in name:
            continue
        data = bytes.fromhex(item['data'])
        extent = min(len(data), spec.get('bytes', len(data)))
        owners.append((name, spec['dos_address'], data[:extent]))
    parts, records, errors = [], [], []
    for index, offset, length, elem, expression in schema:
        match = re.fullmatch(r'\((\w+) \+ (\d+)\)', expression)
        name, extra = (match[1], int(match[2])) if match else (expression, 0)
        start = specs[name]['dos_address'] + extra
        cursor, end, chunks, segments = start, start+length, [], []
        while cursor < end:
            covering = [(n, a, data) for n, a, data in owners if a <= cursor < a+len(data)]
            if not covering:
                errors.append(dict(record=index, expression=expression,
                                   status='UNOBSERVED_SAVE_OWNER', dos_address=cursor))
                break
            stop = min(end, min(a+len(data) for n, a, data in covering))
            stop = min([stop]+[a for n,a,data in owners if cursor<a<stop])
            slices = {data[cursor-a:stop-a] for n, a, data in covering}
            if len(slices) != 1:
                errors.append(dict(record=index, expression=expression,
                                   status='CONFLICTING_NATIVE_OWNER_VIEWS', owners=[n for n,a,d in covering]))
                break
            chunks.append(slices.pop())
            segments.append(dict(owners=[n for n,a,d in covering], record_offset=cursor-start, bytes=stop-cursor))
            cursor = stop
        parts.append(b''.join(chunks))
        records.append(dict(record=index, expression=expression, segments=segments))
    return (b''.join(parts) if not errors else None), records, errors
