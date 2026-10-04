"""Original-operand research only; no initializer or executable emission."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import exe
import functions
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM
except ImportError:
    sys.path.insert(0, 'C:/tools/capstone-5.0.3')
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM

RANGES = {
    'dgroup_56fe': (0x56fe, 4), 'dgroup_5a28': (0x5a28, 2),
    'dgroup_5a96_residual_0': (0x5a96, 1),
    'dgroup_5a96_residual_2': (0x5a98, 4),
    'dgroup_60b0': (0x60b0, 18), 'dgroup_79f0': (0x79f0, 14),
    'common_tail_overlap_3': (0x8b9d, 3),
    'positive_ctype': (0x7a1e, 257), 'positive_queue_pointer': (0x5ffe, 2),
}
manifest = json.loads((ROOT / 'layout/manifest.json').read_bytes())
image = exe.load()
decoder = Cs(CS_ARCH_X86, CS_MODE_16)
decoder.detail = True
units = {unit: image.unit_bytes(unit) for unit in image.units()}
extents = [dict(unit=r['unit'], start=r['seg'] * 16 + r['off'], size=r['size'],
                frame=r['seg'], tables=r.get('jump_tables', []),
                name=functions.name_of(r['unit'], r['seg'], r['off']), kind='function')
           for r in functions.table()['functions']]
# ForceModeA is a manually reviewed registry row without jump-table metadata.
# Its CMP AX,8/JBE and CS:[BX+0573] dispatch establish nine word targets.
force = next(r for r in extents if r['name'] == 'ForceModeA')
assert force['tables'] == [] and force['frame'] == 0x1383
force['tables'] = [dict(site=0x1383*16+0x56e, table=0x1383*16+0x573,
                       count=9, authority='parent CMP AX,8/JBE review')]
for row in manifest['runtime']['members']:
    extents.append(dict(unit='root', start=row['linear'], size=row['size'],
                        name=row['member'], kind='runtime_member', tables=[]))
hits = {key: [] for key in RANGES}
incomplete = []
instruction_count = 0
# Exclude every registered switch table, including those whose data happen to
# decode as instructions. Verify each registry table against its original JMP.
table_checks = []
for row in extents:
    base, raw = units[row['unit']]
    start = row['start']
    block = raw[start-base:start-base+row['size']]
    chunks = []
    skipped = 0
    cursor = start
    for table_row in sorted(row['tables'], key=lambda x: x['table']):
        site, table, count = (table_row[k] for k in ('site', 'table', 'count'))
        frame = row['frame']
        jump = next(decoder.disasm(raw[site-base:site-base+15], site))
        assert jump.mnemonic == 'jmp'
        assert jump.operands[0].type == X86_OP_MEM
        assert jump.reg_name(jump.operands[0].mem.segment) == 'cs'
        assert jump.reg_name(jump.operands[0].mem.base) == 'bx'
        assert jump.operands[0].mem.disp + frame*16 == table
        assert site + jump.size == table
        assert cursor <= table and table+2*count <= start+len(block)
        if row['name'] == 'ForceModeA':
            header = list(decoder.disasm(block[:0x56b+frame*16-start], start))
            assert header[-3].mnemonic == 'cmp' and header[-3].operands[1].imm == 8
            assert header[-2].mnemonic == 'jbe'
        chunks.append((cursor, raw[cursor-base:table-base]))
        skipped += 2*count
        cursor = table+2*count
        table_checks.append(dict(owner=row['name'], frame=frame,
            linear=table, entries=count,
            bound_authority=table_row.get('authority', 'pinned function registry'),
            dispatch=jump.mnemonic+' '+jump.op_str))
    chunks.append((cursor, raw[cursor-base:start-base+len(block)]))
    consumed = skipped
    instructions = [i for address, chunk in chunks for i in decoder.disasm(chunk, address)]
    for insn in instructions:
        consumed += insn.size
        instruction_count += 1
        for oi, op in enumerate(insn.operands):
            if op.type == X86_OP_IMM:
                value, form = op.imm, 'immediate'
                detail = {}
            elif op.type == X86_OP_MEM:
                value, form = op.mem.disp, 'memory_displacement'
                detail = {key: insn.reg_name(getattr(op.mem, key))
                          for key in ('segment', 'base', 'index')}
            else:
                continue
            for key, (lo, size) in RANGES.items():
                if lo <= value < lo + size:
                    hits[key].append(dict(unit=row['unit'], owner=row['name'],
                        kind=row['kind'], site=insn.address, operand=oi,
                        instruction=insn.mnemonic + ' ' + insn.op_str,
                        operand_form=form, value=value, **detail))
    if consumed != len(block):
        incomplete.append(dict(**row, decoded_bytes=consumed, available_bytes=len(block)))
assert any(r['operand_form'] == 'memory_displacement' for r in hits['positive_ctype']), 'ctype positive control absent'
assert hits['positive_queue_pointer'], 'queue positive control absent'
def pin(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
receipt = dict(schema='simant-original-debt-operand-observation-v35',
    root_reviewed=True, admitted=False, original_analysis_only=True,
    original_build_bytes_used=0, decoder_version=__import__('capstone').__version__,
    ranges=RANGES, function_extents=sum(r['kind'] == 'function' for r in extents),
    runtime_member_extents=sum(r['kind'] == 'runtime_member' for r in extents),
    instructions=instruction_count, incomplete_decodes=incomplete, hits=hits,
    explicit_switch_table_checks=table_checks,
    input_pins=[pin(p) for p in [__file__, 'tools/exe.py', 'tools/functions.py',
        'layout/manifest.json', 'layout/functions.json', 'layout/symbols.json',
        'layout/oracle.lock.json', 'assets/SIMANT.EXE']],
    scope='Literal immediate and memory-displacement operands in registered function '
        'and accepted runtime code extents. Values are candidates, not address or '
        'reachability proofs. Does not cover unregistered code, embedded data, '
        'computed aliases, segment provenance, or indirect references. This is linear '
        'decoding between registered switch tables, not complete CFG-boundary proof. No debt '
        'is discharged by absence of a literal.')
out = Path(__file__).with_name('original-debt-operands.json')
out.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(extents=len(extents), instructions=instruction_count,
    incomplete_decodes=len(incomplete), hits={k: len(v) for k,v in hits.items()}), indent=2))
