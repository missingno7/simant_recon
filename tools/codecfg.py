"""Diagnostic MSC dense-switch recognition; never used by acceptance.

Recognizes only a guarded, immediately following CS word table. Every other
indirect branch remains unknown. Instruction and table extents stay explicit.
"""
import hashlib
import mismatch


def _reg(op, name):
    return op.get('kind') == 'reg' and op.get('reg') == name


def _imm(op, value=None):
    return op.get('kind') == 'imm' and (value is None or op.get('value') == value)


def _table(rows, data, segment_offset):
    if len(rows) < 6:
        return None
    compare, guard, default, shift, exchange, jump = rows[-6:]
    ops = [x['operands'] for x in rows[-6:]]
    if not (compare['mnemonic'] == 'cmp' and len(ops[0]) == 2 and
            _reg(ops[0][0], 'ax') and _imm(ops[0][1]) and
            guard['mnemonic'] == 'jbe' and default['mnemonic'] == 'jmp' and
            len(ops[1]) == len(ops[2]) == 1 and _imm(ops[1][0]) and _imm(ops[2][0]) and
            ops[1][0]['value'] == shift['load_offset'] and
            shift['mnemonic'] == 'shl' and len(ops[3]) == 2 and
            _reg(ops[3][0], 'ax') and _imm(ops[3][1], 1) and
            exchange['mnemonic'] == 'xchg' and len(ops[4]) == 2 and
            {_op.get('reg') for _op in ops[4]} == {'ax', 'bx'} and
            jump['mnemonic'] == 'jmp' and len(ops[5]) == 1):
        return None
    address = ops[5][0]
    if not (address.get('kind') == 'mem' and address.get('width') == 2 and
            address.get('segment') == 'cs' and address.get('base') == 'bx' and
            not address.get('index')):
        return None
    start = jump['load_offset'] + len(bytes.fromhex(jump['bytes']))
    count = ops[0][1]['value'] + 1
    end = start + 2 * count
    if not (0 < count <= 1024 and end <= len(data) and address['disp'] == segment_offset + start):
        return None
    targets = [int.from_bytes(data[at:at+2], 'little') - segment_offset
               for at in range(start, end, 2)]
    if not all(end <= target < len(data) for target in targets):
        return None
    return {'start': start, 'end': end, 'entry_width': 2, 'count': count,
            'dispatch': jump['load_offset'], 'targets': targets,
            'sha256': hashlib.sha256(data[start:end]).hexdigest(),
            'evidence': 'CMP AX bound; JBE dispatch; JMP default; SHL AX,1; XCHG AX,BX; JMP CS:[BX+immediate table]'}


def decode(data, segment_offset=0):
    rows, tables, offset = [], [], 0
    while offset < len(data):
        part = mismatch._decode(data[offset:offset+16], offset)
        if not part:
            break
        ins = part[0]
        rows.append(ins)
        offset += len(bytes.fromhex(ins['bytes']))
        table = _table(rows, data, segment_offset)
        if table:
            tables.append(table)
            ins['switch_targets'] = table['targets']
            offset = table['end']
    boundaries = {r['load_offset'] for r in rows}
    for table in tables:
        table['targets_validated'] = all(t in boundaries for t in table['targets'])
    return {'instructions': rows, 'tables': tables,
            'covered_bytes': offset,
            'complete': offset == len(data) and all(t['targets_validated'] for t in tables),
            'authority': 'DIAGNOSTIC_ONLY; no ranges are removed from binding or acceptance'}
