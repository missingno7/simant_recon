"""Reviewed symbolic bindings for an independently laid out DOS image.

Changes apply to generated whole TUs only. Storage needs an explicit reviewed
communal contract; object edits and oracle bytes are forbidden. Compare whole
contributions against the same source before the reviewed edits.
"""
from collections import Counter
import hashlib
import json
import ntpath
import re


# Each family was reviewed against the complete owner and every direct consumer,
# including the persistent byte-address views. This is not a declaration scanner.
SCALAR_FAMILIES = {
    'health': ('S08:35F5', ('HealthB', 'HealthR'), 'health_storage_contract'),
    'food_cycle': ('S08:35F5', ('FoodB', 'FoodR', 'Cycle'), 'food_cycle_storage_contract'),
    'population': ('root:0BE8', ('BpopT', 'RpopT'), 'population_storage_contract'),
    'lion': ('root:0AD9', ('AntsEatenByLions', 'InitialLions'), 'lion_storage_contract'),
    'init_sim': ('S08:35F5', ('fd_50F6_06AA', 'fd_50F6_073A', 'fd_50F6_07C8',
                'fd_50F6_0850', 'fd_50F6_0FBA', 'fd_50F6_0FFE', 'CurExpTool'), 'init_sim_storage_contract'),
    'yellow_reset': ('S22:39C7', ('fd_50F6_0A8E', 'fd_50F6_0AA0', 'fd_50F6_0B1E',
                    'fd_50F6_0C38', 'fd_50F6_0C3E'), 'yellow_reset_storage_contract'),
}

ARRAY_FAMILIES = {
    'water_drop': ('root:0BE8', ('fd_50F6_0256', 'fd_50F6_02C0'), 100,
                   'unsigned char far[100]', 'water_storage_contract'),
}

# Signed sets of (code contribution, operand offset, external target). Only the
# reviewed SS operands are admitted; local symbols and numeric literals remain
# separate layout debt. A different or partial site set fails closed.
DRIVER_SS_SITE_HASHES = {
    'S00:31AD': '5ed1fef640710371d36612bbe51af8c8497efb84db933df55383d6087a31299b',
    'S01:3126': '651ef155dc18f42ded5276c96a99493d490a2ed10250880b491eb0a577263e48',
    'S02:3126': '1e3658784fcf277018f03c60eb9639e340225230de8e08f1131b3cfb3d543759',
    'S03:3126': '9aff44521bb566483058f8faee74a706275881294afa3e77079cfa143d8eccbb',
}

PATTERN_BANK_OWNER = {'name': '_g_41D0', 'segment': '_DATA', 'offset': 0x4B0,
                      'length': 256, 'interior': '_g_4220', 'interior_delta': 80}
PATTERN_BANK_SITES = [0x2A9, 0x30B, 0x352]
LOCAL_SS_SITES = {
    'S01:3126': [('S01A_TEXT', 0x5AD, '_g_2118', 0), ('S01A_TEXT', 0x63B, '_g_2118', 0)],
    'S03:3126': [('S03A_TEXT', 0xDD4, '_g_222C', 0x1E), ('S03A_TEXT', 0xDE1, '_g_222A', 0x1C),
                ('S03A_TEXT', 0xE48, '_g_222C', 0x1E), ('S03A_TEXT', 0xEF4, '_g_222A', 0x1C),
                ('S03A_TEXT', 0xF5B, '_g_222C', 0x1E), ('S03A_TEXT', 0x100E, '_g_22E4', 0xD6),
                ('S03A_TEXT', 0x1029, '_g_22E4', 0xD6), ('S03A_TEXT', 0x1044, '_g_22E4', 0xD6)],
}

DGROUP_RECT_SEGMENT_CORRECTION = {
    'segment': 'MOUSE_TEXT', 'offset': 0x133,
    'old': {'width': 2, 'loc': 'base16', 'self_relative': False,
            'target_kind': 'external', 'target': '_g_5A9C', 'displacement': 0,
            'frame_kind': 'segment', 'frame': '_DATA', 'encoded_addend': '0000'},
    'new': {'width': 2, 'loc': 'base16', 'self_relative': False,
            'target_kind': 'group', 'target': 'DGROUP', 'displacement': 0,
            'frame_kind': 'group', 'frame': 'DGROUP', 'encoded_addend': '0000'},
}


def review_segment_corrections(binding):
    specs = binding.get('segment_corrections', [])
    if specs and (binding['module'] != 'root:1B73'
                  or specs != [DGROUP_RECT_SEGMENT_CORRECTION]):
        raise ValueError('unreviewed assembly SEG target/frame correction')


def review_local_frame_sites(binding):
    specs = binding.get('local_reframes', [])
    if not specs:
        return
    sites = sorted((s['segment'], s['offset'], s['source_symbol'], s['displacement']) for s in specs)
    if (sites != LOCAL_SS_SITES.get(binding['module']) or any(
            (s['target_kind'], s['target'], s['encoded_addend'], s['old_frame_kind'], s['old_frame'],
             s['frame_kind'], s['frame']) != ('segment', '_DATA', '0000', 'segment', '_DATA', 'group', 'DGROUP')
            for s in specs)):
        raise ValueError('unreviewed local assembly frame location set or source anchor')


def review_pattern_binding(binding):
    if binding.get('pattern_bank_owner'):
        if (binding['module'] != 'root:1B4E' or binding['pattern_bank_owner'] != PATTERN_BANK_OWNER
                or binding.get('exports') != [{'name': '_g_41D0', 'segment': '_DATA',
                    'offset': 0x4B0, 'registry_symbol': 'g_41C0', 'registry_delta': 16}]):
            raise ValueError('unreviewed pattern bank source owner')
    if binding.get('pattern_bank_operands'):
        specs = [s for s in binding.get('relocations', []) if s.get('pattern_operand')]
        if (binding['module'] != 'S00:31AD' or len(specs) != 1
                or specs[0] != {'pattern_operand': True, 'segment': 'S00B_TEXT',
                    'offsets': PATTERN_BANK_SITES, 'count': 3, 'target_kind': 'external',
                    'target': '_g_41D0', 'original_value': 0x41D0, 'frame_kind': 'group',
                    'frame': 'DGROUP', 'displacement': 0, 'encoded_addend': '0000'}):
            raise ValueError('unreviewed pattern bank operand set')
    elif any(s.get('pattern_operand') for s in binding.get('relocations', [])):
        raise ValueError('pattern operand lacks reviewed source owner contract')

PROVIDER_SPECS = {
    'source-owned:driver-callback-table': ('CBOWNER', '_driver_callback_table',
        (('_driver_callback_table', 100),), 'void (far * near driver_callback_table[25])();'),
    'source-owned:mouse-words': ('MSOWNER', None,
        (('_g_9120', 2), ('_g_9122', 2), ('_g_9124', 2)),
        'int near g_9120; int near g_9122; int near g_9124;'),
    'source-owned:memory-state': ('MMOWNER', None,
        (('_g_91A0', 2), ('_g_91A2', 2), ('_g_91A4', 4), ('_g_91A8', 4), ('_g_91AC', 4)),
        'typedef struct Block { int handle; long size; unsigned paras; unsigned char type; '
        'unsigned char lock; long age; unsigned next; unsigned prev; unsigned char attr; '
        'char name[13]; } Block; unsigned near g_91A0; unsigned near g_91A2; '
        'Block far * near g_91A4; Block far * near g_91A8; Block far * near g_91AC;'),
    'source-owned:render-scalars': ('RSOWNER', None,
        (('_g_8BD2', 2), ('_g_8BD4', 2), ('_g_9126', 2), ('_g_94E4', 1)),
        'int near g_8BD2; int near g_8BD4; unsigned near g_9126; unsigned char near g_94E4;'),
    'source-owned:memory-far-state': ('MFOWNER', None,
        (('_fd_50F6_394C', 2), ('_fd_50F6_394E', 2), ('_fd_50F6_3950', 2),
         ('_fd_50F6_3948', 4), ('_fd_50F6_3B48', 4)),
        'unsigned far fd_50F6_394C; unsigned far fd_50F6_394E; unsigned far fd_50F6_3950; '
        'char far * far fd_50F6_3948; char far * far fd_50F6_3B48;'),
    'source-owned:mono-pattern-prefix': ('MPOWNER', None, (('_g_8EC0', 24),),
        'unsigned char near g_8EC0[24];'),
    'source-owned:clip-pointer': ('CPOWNER', None, (('_g_5AAC', 4),),
        'struct Rect { int left; int top; int right; int bottom; }; struct Rect far * near g_5AAC;'),
    'source-owned:yard-scalars': ('YDOWNER', None,
        (('_fd_50F6_105E', 2), ('_fd_50F6_0478', 2), ('_fd_50F6_0504', 2),
         ('_fd_50F6_0228', 2), ('_MapPlane', 2), ('_YardMode', 2),
         ('_fd_50F6_0366', 2), ('_fd_50F6_0376', 2)),
        'int far fd_50F6_105E; int far fd_50F6_0478; int far fd_50F6_0504; '
        'int far fd_50F6_0228; int far MapPlane; int far YardMode; '
        'int far fd_50F6_0366; int far fd_50F6_0376;'),
    'source-owned:database-index-state': ('DIOWNER', None,
        (('_fd_50F6_3952', 4), ('_fd_50F6_3956', 2)),
        'typedef union IndexKey { char far *data; long offset; } IndexKey; '
        'typedef struct IndexEntry { IndexKey key; int id; unsigned char kind; unsigned char flags; } IndexEntry; '
        'IndexEntry far * far fd_50F6_3952; int far fd_50F6_3956;'),
    'source-owned:spider-counters': ('SPIDATA', None,
        (('_DeathCnt', 2), ('_EatCnt', 2), ('_SCorpseBase', 2), ('_Scycle', 2),
         ('_Scycle2', 2), ('_SpidBurpCnt', 2), ('_SpidRevenge', 2)),
        'int far DeathCnt; int far EatCnt; int far SCorpseBase; int far Scycle; '
        'int far Scycle2; int far SpidBurpCnt; int far SpidRevenge;'),
    'source-owned:lion-sow-pillar': ('LIOWNER', None,
        (('_LionListM', 10), ('_LionListS', 10), ('_LionListT', 10),
         ('_LionListX', 10), ('_LionListY', 10), ('_PillDir', 2), ('_PillarSeg', 2),
         ('_PillarMap', 12), ('_SowDir', 6), ('_SowSave', 6), ('_SowX', 6), ('_SowY', 6)),
        'unsigned char far LionListM[10]; unsigned char far LionListS[10]; '
        'unsigned char far LionListT[10]; unsigned char far LionListX[10]; '
        'unsigned char far LionListY[10]; int far PillDir; int far PillarSeg; '
        'int far PillarMap[6]; int far SowDir[3]; int far SowSave[3]; '
        'int far SowX[3]; int far SowY[3];'),
    'source-owned:spider-controls': ('SPICTRL', None,
        (('_ChaseSpid', 2), ('_SMode', 2), ('_SuserX', 2), ('_SuserY', 2),
         ('_Starg', 2), ('_StargLife', 2)),
        'int far ChaseSpid; int far SMode; int far SuserX; int far SuserY; '
        'int far Starg; int far StargLife;'),
    'source-owned:point-state': ('PTOWNER', None,
        (('_fd_50F6_0508', 4), ('_fd_50F6_0596', 4), ('_fd_50F6_06A6', 4),
         ('_fd_50F6_072E', 4), ('_fd_50F6_07BC', 4)),
        'typedef struct { int x; int y; } Point; Point far fd_50F6_0508; '
        'Point far fd_50F6_0596; Point far fd_50F6_06A6; '
        'Point far fd_50F6_072E; Point far fd_50F6_07BC;'),
    'source-owned:database-record-state': ('DBRECOWN', None,
        (('_fd_50F6_3958', 496), ('_db_handles', 8)),
        'typedef union IndexKey { char far *data; long offset; } IndexKey; '
        'typedef struct IndexEntry { IndexKey key; int id; unsigned char kind; '
        'unsigned char flags; } IndexEntry; typedef struct IndexHeader { '
        'int count; int spare; long stat1; long stat2; long stat3; int field8; '
        'int field9; } IndexHeader; typedef struct DBHeader { long magic; '
        'int count; long freeBytes; long wastedBytes; } DBHeader; '
        'typedef struct OpenDBIndexView { IndexEntry far *index; '
        'IndexHeader header; } OpenDBIndexView; typedef union OpenDBIndexArea { '
        'OpenDBIndexView typed; char bytes[0x18]; } OpenDBIndexArea; '
        'typedef union OpenDBIndexFileView { int indexFile; char bytes[2]; } '
        'OpenDBIndexFileView; typedef struct OpenDBRec { char name[0x50]; '
        'OpenDBIndexArea indexArea; DBHeader dbHeader; '
        'OpenDBIndexFileView indexFileArea; int file; int dirty; } OpenDBRec; '
        'OpenDBRec far fd_50F6_3958[4]; int far db_handles[4];'),
}

FAR_PROVIDER_MODULES = {'source-owned:memory-far-state', 'source-owned:yard-scalars',
                        'source-owned:database-index-state', 'source-owned:spider-counters',
                        'source-owned:lion-sow-pillar', 'source-owned:spider-controls',
                        'source-owned:point-state', 'source-owned:database-record-state'}

# The compiler represents these actual word arrays by element count and width;
# singleton words use its byte-count COMDEF form. Preserve both measured shapes.
FAR_PROVIDER_WORD_ARRAYS = {'source-owned:lion-sow-pillar':
                          {'_PillarMap', '_SowDir', '_SowSave', '_SowX', '_SowY'},
                          'source-owned:database-record-state': {'_db_handles'}}

FAR_PROVIDER_RECORD_ARRAYS = {'source-owned:database-record-state': {'_fd_50F6_3958': 124}}

def provider_communals(module):
    spec = PROVIDER_SPECS.get(module)
    if not spec:
        raise ValueError('unreviewed functional storage provider')
    if module in INITIALIZED_PROVIDER_SPECS:
        return []
    far = module in FAR_PROVIDER_MODULES
    words = FAR_PROVIDER_WORD_ARRAYS.get(module, set())
    records = FAR_PROVIDER_RECORD_ARRAYS.get(module, {})
    return [{'name': name, 'kind': 'far' if far else 'near', 'length': size,
             **({'count': size // records.get(name, 2 if name in words else 1),
                 'element_size': records.get(name, 2 if name in words else 1)} if far else {})}
            for name, size in spec[2]]


def review_frame_sites(binding):
    specs = binding.get('reframes', [])
    if not specs:
        return
    sites = sorted((s['segment'], s['offset'], s['target']) for s in specs)
    if binding['module'] == 'root:1B73':
        accepted = [('MOUSE_TEXT', 0xCBB, '_g_9120'),
                    ('MOUSE_TEXT', 0xCC0, '_g_9122'), ('MOUSE_TEXT', 0xCC5, '_g_9124')]
        valid = sites == accepted
    else:
        digest = hashlib.sha256(json.dumps(sites, separators=(',', ':')).encode()).hexdigest()
        valid = DRIVER_SS_SITE_HASHES.get(binding['module']) == digest
    if not valid:
        raise ValueError('unreviewed assembly frame correction location set')


def rtlink_alias_delta(offset):
    # RTLink interprets unsuffixed numeric DEFINE operands as hexadecimal.
    # In particular, writing decimal "12" would select byte 18, not byte 12.
    if not isinstance(offset, int) or offset < 0:
        raise ValueError('invalid RTLink alias offset')
    return f' + 0{offset:X}h' if offset else ''


# Generated names below describe functional roles, never historical spellings.
INDEXED_OPERANDS = {
    'S00:31AD': ('S00B_TEXT', [0x341], 'external', '_g_3DCA', 0, 0x3DCA),
    'S00:35A6': ('S00C_TEXT', [0x195], 'external', '_glyph_edge_masks', 0, 0x6778),
    'S03:3126': ('S03A_TEXT', [0xDF7, 0xE0C, 0xE21, 0xE36, 0xF0A, 0xF1F, 0xF34, 0xF49],
                  'segment', '_DATA', 0x18, 0x2226),
}
GRAPHICS_MASK_OPERANDS = {
    'S01:32B5': ('S01C_TEXT', [0xC0], 'external', '_mono_tail_masks', 0, 0x68AC),
    'S03:3258': ('S03C_TEXT', [0x4E4], 'external', '_packed_tail_masks', 0, 0x68B4),
}
GLYPH_EXPORT = {'name': '_glyph_edge_masks', 'segment': '_DATA', 'offset': 12,
                'generated_existing_view': True}


def closed_operand(module, families, flag):
    segment, offsets, kind, target, displacement, original = families[module]
    return {flag: True, 'segment': segment, 'offsets': offsets, 'count': len(offsets),
            'target_kind': kind, 'target': target, 'displacement': displacement,
            'original_value': original, 'frame_kind': 'group', 'frame': 'DGROUP',
            'encoded_addend': '0000'}


def review_indexed_binding(binding, module=None, symbols=None):
    specs = [s for s in binding.get('relocations', []) if s.get('indexed_operand')]
    enabled = binding.get('indexed_address_operands')
    if enabled:
        if binding['module'] not in INDEXED_OPERANDS or specs != [
                closed_operand(binding['module'], INDEXED_OPERANDS, 'indexed_operand')]:
            raise ValueError('unreviewed indexed address site set')
    elif specs:
        raise ValueError('indexed operands lack reviewed ownership')
    exports = [p for p in binding.get('exports', []) if p.get('generated_existing_view')]
    if binding.get('glyph_edge_owner'):
        if binding['module'] != 'root:2650' or exports != [GLYPH_EXPORT]:
            raise ValueError('unreviewed generated existing-data view')
        if module is not None and module['placements']['_DATA'] != {
                'seg': 0x55B3, 'off': 0x676C, 'size': 20}:
            raise ValueError('glyph edge source contribution changed')
    elif exports:
        raise ValueError('generated existing view lacks closed source owner')
    if module is not None and enabled:
        if binding['module'] == 'S03:3126':
            placement = module['placements']['_DATA']
            if (placement['seg'], placement['off'] + 24) != (0x55B3, 0x2226):
                raise ValueError('indexed local table source anchor changed')
            for delta in range(4):
                anchor = symbols['data'][f'g_{0x2226+delta:04X}']
                if (anchor['seg'], anchor['off']) != (0x55B3, 0x2226+delta):
                    raise ValueError('indexed local table field changed')
        elif binding['module'] == 'S00:31AD':
            anchor = symbols['data']['g_3DCA']
            if (anchor['seg'], anchor['off']) != (0x55B3, 0x3DCA):
                raise ValueError('indexed external owner anchor changed')


def review_graphics_binding(binding):
    specs = [s for s in binding.get('relocations', []) if s.get('graphics_mask_operand')]
    if specs and (binding['module'] not in GRAPHICS_MASK_OPERANDS or specs != [
            closed_operand(binding['module'], GRAPHICS_MASK_OPERANDS, 'graphics_mask_operand')]):
        raise ValueError('unreviewed graphics mask operand site')


S01_PATTERN_VIEW_SITE = {
    'segment': 'S01A_TEXT', 'offsets': [0x5A8], 'count': 1,
    'target_kind': 'external', 'target': '_g_4220', 'original_value': 0x4220,
    'frame_kind': 'group', 'frame': 'DGROUP', 'displacement': 0,
    'encoded_addend': '0000', 's01_pattern_view_operand': True,
}


def review_s01_pattern_view(binding, symbols=None):
    specs = [s for s in binding.get('relocations', []) if s.get('s01_pattern_view_operand')]
    if binding.get('s01_pattern_view_operands'):
        if (binding['module'] != 'S01:3126' or specs != [S01_PATTERN_VIEW_SITE]
                or binding.get('s01_pattern_view_owner') != PATTERN_BANK_OWNER):
            raise ValueError('unreviewed S01 pattern-view operand site or owner')
        if symbols is not None:
            anchor = symbols['data']['g_4220']
            if (anchor['seg'], anchor['off']) != (0x55B3, 0x4220):
                raise ValueError('S01 pattern-view symbol anchor changed')
    elif specs or binding.get('s01_pattern_view_owner'):
        raise ValueError('S01 pattern-view operand lacks its closed owner contract')


INITIALIZED_PROVIDER_SPECS = {
    'source-owned:graphics-formulas': ('consumer_mask_formulas',
        [('_g_2100', 0, 8), ('_mono_tail_masks', 8, 8), ('_packed_tail_masks', 16, 2)]),
    'source-owned:g2108-color-translation': ('accepted_source_literal_translation', [('_g_2108', 0, 16)]),
}


def initialized_payload(module):
    if module == 'source-owned:graphics-formulas':
        return bytes([0x80 >> phase for phase in range(8)] +
                     [0xFF if r == 0 else (0xFF << (8-r)) & 0xFF for r in range(8)] +
                     [0xFF, 0xFF & ~0x0F])
    if module == 'source-owned:g2108-color-translation':
        from pathlib import Path
        # Read only the accepted source table, never the research image/debt bytes.
        source = (Path(__file__).resolve().parents[1] / 'src/S03/m3126.asm').read_text(encoding='latin1')
        match = re.search(r'(?m)^_g_2216\s+db\s+([^\n]+)\n\s*db\s+([^\n]+)', source)
        if not match:
            raise ValueError('accepted color-map source anchor changed')
        tokens = [t.strip() for t in ','.join(match.groups()).split(',')]
        values = [int(t[:-1], 16) if re.fullmatch(r'[0-9A-Fa-f]+h', t) else int(t) for t in tokens]
        if len(values) != 16:
            raise ValueError('accepted color-map extent changed')
        return bytes(values)
    raise ValueError('unreviewed initialized source recipe')


def initialized_publics(module):
    payload = initialized_payload(module)
    return [{'name': name, 'segment': '_DATA', 'offset': offset, 'extent_bytes': length,
             'initialized': True, 'value_sha256': hashlib.sha256(payload[offset:offset+length]).hexdigest()}
            for name, offset, length in INITIALIZED_PROVIDER_SPECS[module][1]]


def review_initialized_provider(provider, symbols=None):
    module = provider['module']
    if (provider.get('storage_kind') != 'initialized_storage'
            or provider.get('recipe') != INITIALIZED_PROVIDER_SPECS[module][0]
            or provider.get('public_DATA') != initialized_publics(module)):
        raise ValueError('initialized owner recipe/public contract changed')
    if symbols is not None:
        for name, offset in (('_g_2100', 0x2100), ('_g_2108', 0x2108)):
            if name not in {r['name'] for r in provider['public_DATA']}:
                continue
            anchor = symbols['data'][name[1:]]
            if (anchor['seg'], anchor['off']) != (0x55B3, offset):
                raise ValueError('initialized source owner registry anchor changed')


def verify_initialized_provider(obj, provider):
    review_initialized_provider(provider)
    module = provider['module']
    payload = initialized_payload(module)
    expected_publics = [{'name': name, 'segment': '_DATA', 'offset': offset}
                        for name, offset, _ in INITIALIZED_PROVIDER_SPECS[module][1]]
    live = [d for d in obj.segment_defs if d['length']]
    if (obj.communals or obj.externals or obj.local_publics or obj.linker_fixups or obj.fixups
            or obj.publics != expected_publics
            or len(live) != 1 or live[0]['name'] != '_DATA'
            or (live[0]['class'], live[0]['combine'], live[0]['use_32bit_offset']) != ('DATA', 'public', False)
            or not any(g['name'] == 'DGROUP' and '_DATA' in g['segments'] for g in obj.groups)
            or obj.segment_length('_DATA') != len(payload) or obj.segment_bytes('_DATA') != payload
            or any(length for name, length in obj.segment_lengths.items() if name != '_DATA')
            or any(data for name, data in obj.segments.items() if name != '_DATA')):
        raise ValueError('initialized provider introduced wrong values/layout/imports/code')
    return {'status': 'PASS', 'data_only': True, 'live_initialized_bytes': len(payload),
            'code_bytes': 0, 'communals': [], 'publics': expected_publics, 'fixups': [],
            'recipe': provider['recipe'], 'value_sha256': hashlib.sha256(payload).hexdigest()}


def require_initialized_and_indexed_contracts(report, profile, tool):
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    rows = {r['module']: r for r in report['translation_units']}
    specifications = [
        ('source-owned:g2108-color-translation', 'g2108_color_translation_contract', {
            'separate_mutable_exact_values': 'PASS', 'reversed_mapping_negative': 'FAIL_VALUES',
            'one_byte_shifted_map_base_negative': 'FAIL_VALUES', 'alias_view_negative': 'FAIL_ALIAS'}),
        ('source-owned:graphics-formulas', 'graphics_formula_binding_contract', {
            'positive': 'PASS', 'negative_s01_wrong_frame': 'FAIL', 'negative_s01_wrong_base': 'FAIL',
            'negative_s03_wrong_frame': 'FAIL', 'negative_s03_wrong_base': 'FAIL',
            'negative_reversed_selector': 'FAIL', 'negative_low_bit_mono': 'FAIL',
            'negative_low_nibble_packed': 'FAIL'}),
        ('S00:35A6', 'driver_indexed_address_contract', {'LITERAL': 'LITERAL', 'DGROUP': 'DGROUP', 'DATA': 'OTHER'})]
    for module, key, required in specifications:
        if module not in rows or (module == 'S00:35A6' and not (rows[module].get('source_binding') or {}).get('indexed_address_operands')):
            continue
        contract = report.get(key, {})
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
        if (contract.get('root_reviewed') is not True or not contract.get('all_required_checks_pass')
                or contract.get('required_cases') != required
                or len(cases) != len(required) or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
                or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
            raise ValueError(f'{key} lacks selected linker/closed source runtime evidence')
        if module in INITIALIZED_PROVIDER_SPECS and contract.get('public_DATA') != initialized_publics(module):
            raise ValueError('initialized runtime contract belongs to different owner')
        if module == 'source-owned:graphics-formulas':
            if not all((rows.get(m, {}).get('source_binding') or {}).get('relocations') == [
                    closed_operand(m, GRAPHICS_MASK_OPERANDS, 'graphics_mask_operand')] for m in GRAPHICS_MASK_OPERANDS):
                raise ValueError('graphics runtime contract lacks complete consumer site set')
        if module == 'S00:35A6':
            sites = [[m, segment, offset, target] for m, (segment, offsets, _, target, _, _) in INDEXED_OPERANDS.items()
                     for offset in offsets]
            if (contract.get('signed_site_tuples') != sites
                    or not (rows.get('root:2650', {}).get('source_binding') or {}).get('glyph_edge_owner')
                    or not all((rows.get(m, {}).get('source_binding') or {}).get('indexed_address_operands') for m in INDEXED_OPERANDS)
                    or not all(r.get('actual_DS_SS_DGROUP') and r.get('expectation_matched')
                               and r['observed_hex'] == r['expected_observation_hex']
                               and r.get('emulator_exit') == 0
                               and r['link_map']['data_group_offset'] > 0
                               and r['link_map']['data_frame_skew'] == 2 for r in cases)):
                raise ValueError('indexed runtime contract lacks shifted-group site proof')


def debug_fingerprint(obj, segment):
    """Account for an entire compiler debug contribution, including every fixup."""
    packet = {'definition': [s for s in obj.segment_defs if s['name'] == segment],
              'bytes_sha256': hashlib.sha256(obj.segment_bytes(segment)).hexdigest(),
              'fixups': sorted(fixup_key(f) for f in obj.linker_fixups if f['segment'] == segment)}
    return hashlib.sha256(json.dumps(packet, sort_keys=True).encode('ascii')).hexdigest()


def apply_binding(text, binding):
    for edit in binding['edits']:
        if text.count(edit['before']) != edit['count']:
            raise ValueError('DOS binding source context changed: ' + binding['module'])
        text = text.replace(edit['before'], edit['after'])
    return text


def review_addresses(binding, module, symbols):
    """Join source-owned relative locations to already reviewed symbol anchors."""
    review_pattern_binding(binding)
    review_local_frame_sites(binding)
    review_indexed_binding(binding, module, symbols)
    review_graphics_binding(binding)
    review_s01_pattern_view(binding, symbols)
    scalar_names = set()
    array_names = {}
    if binding.get('scalar_storage'):
        families = binding['scalar_storage']['families']
        if not families or len(families) != len(set(families)):
            raise ValueError('unreviewed scalar storage family')
        for family in families:
            spec = SCALAR_FAMILIES.get(family)
            if not spec or binding['module'] != spec[0]:
                raise ValueError('unreviewed scalar source owner')
            scalar_names.update('_' + name for name in spec[1])
    if binding.get('array_storage'):
        families = binding['array_storage']['families']
        if not families or len(families) != len(set(families)):
            raise ValueError('unreviewed array storage family')
        for family in families:
            spec = ARRAY_FAMILIES.get(family)
            if not spec or binding['module'] != spec[0]:
                raise ValueError('unreviewed array source owner')
            array_names.update(('_' + name, spec[2]) for name in spec[1])
    if (scalar_names or array_names) and {c['name'] for c in binding.get('communals', [])} != scalar_names | set(array_names):
        raise ValueError('scalar/array storage member set changed')
    for communal in binding.get('communals', []):
        if binding.get('queue_storage'):
            if (binding['module'] != 'root:1FD2' or communal !=
                    {'name': '_input_queue', 'kind': 'near', 'length': 112}):
                raise ValueError('unreviewed near queue storage')
            continue
        anchor = symbols['data'][communal['name'][1:]]
        if (anchor['seg'], anchor['off']) != tuple(communal['historical_address']):
            raise ValueError('DOS communal symbol address changed')
        expected = (('far', 2, 1, 2) if communal['name'] in scalar_names else
                    ('far', array_names[communal['name']], 1, array_names[communal['name']])
                    if communal['name'] in array_names else ('far', 64, 2, 128))
        if (communal['kind'], communal['count'], communal['element_size'], communal['length']) != expected:
            raise ValueError('unreviewed communal type or extent')
        if anchor['seg'] != 0x50F6 or any(s['seg'] == anchor['seg'] and
                anchor['off'] < s['off'] < anchor['off'] + communal['length']
                for s in symbols['data'].values()):
            raise ValueError('communal contains another registered storage view')
    for public in binding.get('exports', []):
        if public.get('generated_existing_view'):
            continue  # Exact source extent/address checked by review_indexed_binding.
        if public['segment'] in module['placements']:
            placement = module['placements'][public['segment']]
            segment, offset = placement['seg'], placement['off'] + public['offset']
        elif public['segment'].endswith('_TEXT'):
            segment = module['seg']
            offset = module['extent']['start'] - segment * 16 + public['offset']
        else:
            raise ValueError('unanchored DOS storage export')
        anchor = symbols['data'][public.get('registry_symbol', public['name'][1:])]
        delta = public.get('registry_delta', 0)
        if delta and not binding.get('pattern_bank_owner'):
            raise ValueError('unreviewed relative storage export')
        if (segment, offset) != (anchor['seg'], anchor['off'] + delta):
            raise ValueError('DOS storage export conflicts with reviewed symbol address')
        if binding.get('pattern_bank_owner'):
            interior = symbols['data']['g_4220']
            if ((segment, offset + 80) != (interior['seg'], interior['off'])
                    or offset + 256 > module['placements']['_DATA']['off'] + module['placements']['_DATA']['size']):
                raise ValueError('pattern bank extent/interior anchor changed')
    review_frame_sites(binding)
    review_segment_corrections(binding)
    if binding.get('segment_corrections'):
        anchor = symbols['data']['g_5A9C']
        if (anchor['seg'], anchor['off']) != (0x55B3, 0x5A9C):
            raise ValueError('assembly SEG pointer target conflicts with registry anchor')
    for spec in binding.get('reframes', []):
        if (symbols['data'][spec['target'][1:]]['seg'] != 0x55B3
                or (spec['old_frame_kind'], spec['old_frame'], spec['frame_kind'], spec['frame']) !=
                   ('segment', '_DATA', 'group', 'DGROUP')):
            raise ValueError('unreviewed assembly segment/group frame correction')
    for spec in binding.get('local_reframes', []):
        placement = module['placements']['_DATA']
        anchor = symbols['data'][spec['source_symbol'][1:]]
        if (placement['seg'], placement['off'] + spec['displacement']) != (anchor['seg'], anchor['off']):
            raise ValueError('local frame source owner conflicts with registry anchor')
    for spec in binding.get('relocations', []):
        if spec.get('indexed_operand') or spec.get('graphics_mask_operand') or spec.get('s01_pattern_view_operand'):
            continue  # Closed site sets checked above, not speculative registry names.
        if spec.get('pattern_operand'):
            if (symbols['data']['g_41C0']['seg'], symbols['data']['g_41C0']['off'] + 16) != (0x55B3, 0x41D0):
                raise ValueError('pattern bank base anchor changed')
            continue
        if spec.get('storage_pointer'):
            view = symbols['data']['g_5FFE']
            placement = module['placements']['_DATA']
            if (binding.get('queue_storage') != {'slots': 7, 'stride': 16, 'pointer_view': '_g_5FFE'}
                    or spec['target'] != '_input_queue' or spec['original_value'] != 0x91B0
                    or (placement['seg'], placement['off'] + spec['offset']) != (view['seg'], view['off'])
                    or (spec['segment'], spec['offset'], spec['owner'], spec['owner_offset'], spec['field_offset']) !=
                       ('_DATA', 24, '_g_5FF2', 12, 12)):
                raise ValueError('queue pointer is not its reviewed descriptor field')
            continue
        table = 'code' if spec.get('target_label') else 'data'
        name = spec.get('target_label', spec['target'])[1:]
        anchor = symbols[table][name]
        if spec['original_value'] != anchor['off']:
            raise ValueError('DOS operand conflicts with reviewed symbol address')
        if table == 'code' and (anchor['seg'] != module['seg'] or
                anchor.get('unit', 'root') != module['unit']):
            raise ValueError('DOS near callback targets another frame')


def fixup_key(fixup):
    # OMF indices can shift when an external/public is introduced. Compare the
    # resolved symbolic identities, location, width, frame and addend instead.
    return tuple(fixup[k] for k in ('segment', 'offset', 'width', 'loc',
        'self_relative', 'target_kind', 'target', 'displacement',
        'frame_kind', 'frame', 'encoded_addend'))


def communal_key(row):
    return tuple(row.get(k) for k in ('name', 'kind', 'count', 'element_size', 'length'))


def runtime_component_path(path):
    """Compare Windows tool identities independently of slash spelling/case."""
    return ntpath.normcase(ntpath.normpath(path)).replace('\\', '/')


def review_provider_source(text, provider, symbols=None):
    """Admit only explicitly recovered types and objects, never generic stubs."""
    spec = PROVIDER_SPECS.get(provider.get('module'))
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    if (not spec or provider.get('owner') != spec[1]
            or provider.get('communals') != provider_communals(provider.get('module'))
            or ' '.join(text.split()) != spec[3]):
        raise ValueError('unreviewed functional storage provider')
    if provider['module'] in INITIALIZED_PROVIDER_SPECS:
        review_initialized_provider(provider, symbols)
        return
    if symbols is not None and spec[1] is None:
        addresses = dict(zip(('_g_9120', '_g_9122', '_g_9124', '_g_91A0', '_g_91A2',
                             '_g_91A4', '_g_91A8', '_g_91AC', '_g_8BD2', '_g_8BD4', '_g_9126', '_g_94E4',
                             '_fd_50F6_394C', '_fd_50F6_394E', '_fd_50F6_3950', '_fd_50F6_3948', '_fd_50F6_3B48'),
                            (0x9120, 0x9122, 0x9124, 0x91A0, 0x91A2, 0x91A4, 0x91A8, 0x91AC,
                             0x8BD2, 0x8BD4, 0x9126, 0x94E4, 0x394C, 0x394E, 0x3950, 0x3948, 0x3B48)))
        addresses.update({'_g_8EC0': 0x8EC0, '_g_5AAC': 0x5AAC,
            '_fd_50F6_105E': 0x105E, '_fd_50F6_0478': 0x0478, '_fd_50F6_0504': 0x0504,
            '_fd_50F6_0228': 0x0228, '_MapPlane': 0x032E, '_YardMode': 0x035C,
            '_fd_50F6_0366': 0x0366, '_fd_50F6_0376': 0x0376,
            '_fd_50F6_3952': 0x3952, '_fd_50F6_3956': 0x3956,
            '_DeathCnt': 0x109A, '_EatCnt': 0x1054, '_SCorpseBase': 0x105A, '_Scycle': 0x1042,
            '_Scycle2': 0x1072, '_SpidBurpCnt': 0x1076, '_SpidRevenge': 0x108A,
            '_LionListM': 0x0ABA, '_LionListS': 0x0ACC, '_LionListT': 0x0ADE,
            '_LionListX': 0x0A92, '_LionListY': 0x0AA8, '_PillDir': 0x0C3C,
            '_PillarSeg': 0x0C36, '_PillarMap': 0x0D9C, '_SowDir': 0x0F1A,
            '_SowSave': 0x0F28, '_SowX': 0x0EAE, '_SowY': 0x0F00,
            '_ChaseSpid': 0x0248, '_SMode': 0x0FB8, '_SuserX': 0x0F42,
            '_SuserY': 0x0F7E, '_Starg': 0x0FFC, '_StargLife': 0x10AE,
            '_fd_50F6_0508': 0x0508, '_fd_50F6_0596': 0x0596,
            '_fd_50F6_06A6': 0x06A6, '_fd_50F6_072E': 0x072E,
            '_fd_50F6_07BC': 0x07BC})
        addresses.update({'_fd_50F6_3958': 0x3958, '_db_handles': 0x3B50})
        addresses.update({'_g_5A97': 0x5A97})
        addresses.update({name: row[0] for name, row in V15_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V17_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V18_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V19_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V20_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V21_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V22_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V23_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V24_STORAGE_ANCHORS.items()})
        addresses.update({name: row[0] for name, row in V25_STORAGE_ANCHORS.items()})
        for name, size in spec[2]:
            anchor = symbols['data'][name[1:]]
            segment = 0x50F6 if provider['module'] in FAR_PROVIDER_MODULES else 0x55B3
            interiors = [(n, s['off'] - anchor['off']) for n, s in symbols['data'].items()
                         if s['seg'] == anchor['seg'] and anchor['off'] < s['off'] < anchor['off'] + size]
            expected_interiors = [('g_5AAE', 2)] if name == '_g_5AAC' else []
            reviewed_anchors = {**V15_STORAGE_ANCHORS, **V17_STORAGE_ANCHORS,
                                **V18_STORAGE_ANCHORS, **V19_STORAGE_ANCHORS, **V20_STORAGE_ANCHORS, **V21_STORAGE_ANCHORS, **V22_STORAGE_ANCHORS, **V23_STORAGE_ANCHORS, **V24_STORAGE_ANCHORS, **V25_STORAGE_ANCHORS}
            if name in reviewed_anchors:
                same_base = sorted(n for n, s in symbols['data'].items()
                                   if (s['seg'], s['off']) == (anchor['seg'], anchor['off']))
                if same_base != sorted(reviewed_anchors[name][1]):
                    raise ValueError('functional storage exact-base views changed')
            if name == '_g_5A97' and sorted(n for n, s in symbols['data'].items()
                    if (s['seg'], s['off']) == (anchor['seg'], anchor['off'])) != ['g_5A97']:
                raise ValueError('display selector exact-base views changed')
            if ((anchor['seg'], anchor['off']) != (segment, addresses[name])
                    or interiors != expected_interiors):
                raise ValueError('functional storage extent conflicts with reviewed registry')


def verify_provider(obj, provider):
    if provider.get('module') in INITIALIZED_PROVIDER_SPECS:
        return verify_initialized_provider(obj, provider)
    spec = PROVIDER_SPECS.get(provider.get('module'))
    if not spec or provider.get('communals') != provider_communals(provider.get('module')):
        raise ValueError('unreviewed functional storage provider')
    expected = Counter(communal_key(c) for c in provider['communals'])
    if (Counter(communal_key(c) for c in obj.communals) != expected
            or obj.publics or obj.local_publics or obj.linker_fixups
            or any(obj.segment_lengths.values()) or any(obj.segments.values())
            or obj.externals != [n for n, _ in spec[2]]
            or obj.external_scopes != ['communal'] * len(spec[2])):
        raise ValueError('functional storage provider introduced code/data/extra allocation')
    return {'status': 'PASS', 'data_only': True, 'live_initialized_bytes': 0,
            'code_bytes': 0, 'communals': provider['communals'], 'publics': [], 'fixups': []}


def bind_communal_alias(spec, obj, row, symbols):
    provider = row.get('storage_provider', {})
    source = row['source']
    offset = spec['offset']
    callback = (provider.get('module') == 'source-owned:driver-callback-table'
                and spec['owner'] == '_driver_callback_table'
                and spec['owner_size'] == 100 and spec['view_size'] == 4
                and isinstance(offset, int) and offset % 4 == 0 and 0 <= offset <= 96)
    clip = (provider.get('module') == 'source-owned:clip-pointer'
            and spec['owner'] == '_g_5AAC' and spec['alias'] == '_g_5AAE'
            and spec['owner_size'] == 4 and spec['view_size'] == 2 and offset == 2)
    if (not (callback or clip)
            or spec['source'].replace('\\', '/') != source['path'].replace('\\', '/')
            or spec['source_sha256'] != source['sha256']
            or spec['module'] != row['module']):
        raise ValueError('unreviewed communal slot view or source owner')
    verify_provider(obj, provider)
    historical = [0x55B3, (0x9128 if callback else 0x5AAC) + offset]
    anchor = symbols['data'][spec['alias'][1:]]
    if historical != [anchor['seg'], anchor['off']]:
        raise ValueError('communal slot view conflicts with reviewed registry address')
    return {'alias': spec['alias'], 'owner': spec['owner'], 'offset': offset,
            'kind': 'data', 'reason': 'reviewed source communal slot view',
            'module': row['module'], 'address': historical,
            'owner_size': spec['owner_size'], 'view_size': spec['view_size'],
            'source_anchor': spec['source_anchor']}


def require_callback_storage_contract(report, profile, tool):
    if not any(row['module'] == 'source-owned:driver-callback-table' for row in report['translation_units']):
        return
    contract = report.get('callback_storage_contract', {})
    required = contract.get('required_cases', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (not contract.get('all_required_checks_pass') or contract.get('root_reviewed') is not True
            or contract.get('slots') != 25 or contract.get('slot_bytes') != 4
            or contract.get('owner_bytes') != 100
            or Counter(required.values()) != Counter({'PASS': 1, 'FAIL': 3})
            or len(cases) != 4 or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('callback table lacks the selected linker/MSC startup contract')


def require_near_storage_contracts(report, profile, tool):
    require_provider_contracts(report, profile, tool, [
        ('source-owned:mouse-words', 'mouse_storage_contract', 2),
        ('source-owned:memory-state', 'memory_storage_contract', 3)])


def require_additional_storage_contracts(report, profile, tool):
    require_provider_contracts(report, profile, tool, [
        ('source-owned:render-scalars', 'render_scalar_contract', 2),
        ('source-owned:memory-far-state', 'memory_far_storage_contract', 3),
        ('source-owned:mono-pattern-prefix', 'mono_pattern_prefix_contract', 1),
        ('source-owned:clip-pointer', 'clip_pointer_contract', 2),
        ('source-owned:yard-scalars', 'yard_scalar_contract', 6, 2),
        ('source-owned:database-index-state', 'database_index_state_contract', 2),
        ('source-owned:spider-counters', 'spider_counter_contract', 17, 2),
        ('source-owned:lion-sow-pillar', 'lion_array_storage_contract', 5, 2),
        ('source-owned:spider-controls', 'spider_control_contract', 14, 2),
        ('source-owned:point-state', 'point_state_contract', 2),
        ('source-owned:database-record-state', 'database_record_state_contract', 4, 2)])


def require_v15_storage_contracts(report, profile, tool):
    """Keep the exact reviewed case matrix, including non-generic result classes.

    Wider-owner and overrun diagnostics cannot replace rejected type/extent
    controls. They stay recorded outside this gating matrix.
    """
    _require_reviewed_storage_contracts(report, profile, tool, V15_STORAGE_CONTRACTS)


def _require_reviewed_storage_contracts(report, profile, tool, contracts):
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    modules = {r['module'] for r in report['translation_units']}
    for module, (key, required) in contracts.items():
        if module not in modules:
            continue
        contract = report.get(key, {})
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
        if (contract.get('root_reviewed') is not True
                or contract.get('all_required_checks_pass') is not True
                or contract.get('communals') != provider_communals(module)
                or contract.get('required_cases') != required
                or len(cases) != len(required) or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] is True and r['expected'] == r['actual'] == required[r['case']]
                           and not r.get('timed_out', False) for r in cases)
                or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
            raise ValueError(f'{module} lacks the selected linker/MSC startup contract')


def require_v17_storage_contracts(report, profile, tool):
    _require_reviewed_storage_contracts(report, profile, tool, V17_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V17_STORAGE_CONTRACTS)
    _require_ant_control_compiler_controls(report)


def _require_clean_owner_maps(report, profile, contracts):
    for module, (key, _) in contracts.items():
        if not any(r['module'] == module for r in report['translation_units']):
            continue
        expected_names = sorted(n for n, _ in PROVIDER_SPECS[module][2])
        for case in report[key]['cases']:
            if case['linker'] != profile:
                continue
            if (case.get('linker_diagnostics') != []
                    or case.get('linker_produced_executable') is not True
                    or case.get('linker_produced_map') is not True
                    or sorted(case.get('expected_owner_publics', [])) != expected_names
                    or sorted(case.get('owner_publics_found_in_map', [])) != expected_names):
                raise ValueError(f'{module} lacks clean resolved owner maps in its startup contract')


def _require_ant_control_compiler_controls(report):
    if any(r['module'] == 'source-owned:ant-ui-control-state' for r in report['translation_units']):
        controls = report.get('ant_ui_control_state_contract', {}).get('compiler_negative_controls', [])
        if (len(controls) != 2 or controls[0].get('name') != 'mode triple shortened to two words'
                or controls[0].get('detected') is not True
                or controls[0].get('result_class') != 'OMF_FAR_COMMUNAL_SHORT_EXTENT'
                or controls[0].get('expected_length') != 6 or controls[0].get('observed_length') != 4
                or controls[0].get('runtime_executed') is not False
                or {k: controls[0].get('actual_communal', {}).get(k) for k in ('name', 'kind', 'count', 'element_size', 'length')}
                    != {'name': '_modeLevels', 'kind': 'far', 'count': 2, 'element_size': 2, 'length': 4}
                or controls[1].get('name') != 'knobSize given a static initializer'
                or controls[1].get('detected') is not True or controls[1].get('still_communal') is not False
                or controls[1].get('result_class') != 'OMF_INITIALIZED_FAR_DATA_PUBLIC'
                or controls[1].get('runtime_executed') is not False
                or controls[1].get('initialized_data_segment', {}).get('class') != 'FAR_DATA'
                or controls[1].get('initialized_data_segment', {}).get('length') != 4):
            raise ValueError('ant control owner lacks the reviewed compiler negative controls')


def display_selector_cases():
    """The closed producer matrix: two entry bytes, eight modes and two exits."""
    modes = [(-1, -1, 255), (0, 0, 0), (3, 3, 3), (5, 5, 5),
             (2, 2, 2), (8, 8, 8), (4, 4, 4), (7, 7, 7)]
    rows = {}
    for seed, before in enumerate(([0, 0, 0], [-1, -1, 255])):
        for index, after in enumerate(modes, 1):
            rows[f'C{seed * 8 + index:02d}'] = {
                'expected_before': before, 'expected_after': list(after),
                'expected_status': 0, 'expected_message': None}
        for index, message in enumerate(("Bad 'Display Mode' in configuration file", 'Fixture config missing'), 17):
            rows[f'C{seed * 2 + index:02d}'] = {
                'expected_before': before, 'expected_after': None,
                'expected_status': 1, 'expected_message': message}
    rows['C21'] = {'expected_before': [0, 0, 0], 'expected_after': [0, 0, 0],
                   'expected_status': 0, 'expected_message': None}
    return rows


def require_display_selector_contract(report, profile, tool):
    from pathlib import Path
    module = 'source-owned:display-mode-selector'
    if not any(r['module'] == module for r in report['translation_units']):
        return
    contract = report.get('display_mode_selector_contract', {})
    required = display_selector_cases()
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    closed = {f'{p}:{name}': row for p in ('rtlink400', 'rtlink610') for name, row in required.items()}
    if (contract.get('root_reviewed') is not True or contract.get('all_required_checks_pass') is not True
            or contract.get('communals') != provider_communals(module)
            or contract.get('required_cases') != closed
            or len(cases) != 21 or {r['case'] for r in cases} != set(required)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('display selector lacks closed producer/runtime evidence')
    for row in cases:
        expected = required[row['case']]
        if (row.get('passed') is not True or row.get('timed_out', False)
                or any(row.get(k) != v for k, v in expected.items())
                or row.get('actual_before') != expected['expected_before']
                or row.get('actual_after') != expected['expected_after']
                or row.get('actual_status') != expected['expected_status']
                or (expected['expected_message'] and expected['expected_message'] not in row.get('actual_before_and_after_log', ''))):
            raise ValueError('display selector lacks closed producer/runtime evidence')


def require_provider_contracts(report, profile, tool, specifications):
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    for specification in specifications:
        module, key, negatives = specification[:3]
        positives = specification[3] if len(specification) == 4 else 1
        if not any(r['module'] == module for r in report['translation_units']):
            continue
        contract = report.get(key, {})
        required = contract.get('required_cases', {})
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
        if (contract.get('root_reviewed') is not True or not contract.get('all_required_checks_pass')
                or contract.get('communals') != provider_communals(module)
                or Counter(required.values()) != Counter({'PASS': positives, 'FAIL': negatives})
                or len(cases) != positives + negatives or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
                or (module == 'source-owned:clip-pointer'
                    and any(not r.get('map_alias_geometry') for r in cases if r['expected'] == 'PASS'))
                or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
            raise ValueError(f'{module} lacks the selected linker/MSC startup contract')


def require_history_startup_contract(report, profile, tool):
    """Require the proven MSC-startup path for any admitted far history storage."""
    if not any(any(c['kind'] == 'far' and c.get('length') == 128 for c in r.get('source_binding', {}).get('communals', [])) for r in report['translation_units']
               if r.get('source_binding')):
        return
    contract = report.get('history_storage_contract', {})
    required = {'crt_overlay_zero_communal': 'CRT', 'crt_overlay_nonzero_contrast': 'CRT',
                'crt_byte_and_word_views': 'BYTE', 'crt_byte_and_word_nonzero_contrast': 'BYTE'}
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile and r['case'] in required]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (not contract.get('all_required_checks_pass') or len(cases) != 4
            or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['startup'] == required[r['case']] for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('far history storage lacks the selected linker/MSC startup contract')


def require_scalar_startup_contracts(report, profile, tool):
    """Check the selected runtime and both address-view positives for each family."""
    families = {family for row in report['translation_units']
                for family in (row.get('source_binding') or {}).get('scalar_storage', {}).get('families', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    for family in families:
        _, members, key = SCALAR_FAMILIES[family]
        contract = report.get(key, {})
        required = contract.get('required_cases', {})
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
        negative_count = 7 if family == 'yellow_reset' else 4
        if (not contract.get('all_required_checks_pass') or contract.get('root_reviewed') is not True
                or contract.get('members') != list(members)
                or contract.get('dos_type') != 'int far' or contract.get('word_bytes') != 2
                or Counter(required.values()) != Counter({'PASS': 2, 'FAIL': negative_count})
                or len(cases) != 2 + negative_count or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
                or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
            raise ValueError(f'{family} scalar storage lacks the selected linker/MSC startup contract')


def require_array_startup_contracts(report, profile, tool):
    families = {family for row in report['translation_units']
                for family in (row.get('source_binding') or {}).get('array_storage', {}).get('families', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    for family in families:
        _, members, size, dos_type, key = ARRAY_FAMILIES[family]
        contract = report.get(key, {})
        required = contract.get('required_cases', {})
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
        if (contract.get('root_reviewed') is not True or not contract.get('all_required_checks_pass')
                or contract.get('members') != list(members) or contract.get('element_count') != size
                or contract.get('dos_type') != dos_type
                or Counter(required.values()) != Counter({'PASS': 1, 'FAIL': 1})
                or len(cases) != 2 or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
                or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
            raise ValueError(f'{family} array storage lacks the selected linker/MSC startup contract')


def require_queue_startup_contract(report, profile, tool):
    """Near queue storage requires the actual assembly/MSC startup ABI controls."""
    if not any(r.get('source_binding', {}).get('queue_storage') for r in report['translation_units']
               if r.get('source_binding')):
        return
    contract = report.get('queue_storage_contract', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    required = {'canonical_source_positive': 'PASS', 'reviewed_dgroup_positive': 'PASS',
                'data_segment_frame_contrast': 'FAIL', 'queue_initializer_nonzero': 'FAIL',
                'buffer_pointer_plus_one': 'FAIL', 'capacity_eight': 'FAIL'}
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (not contract.get('all_required_checks_pass') or len(cases) != len(required)
            or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']] for r in cases)
            or contract.get('contract') != {'ring_slots': 7, 'stride': 16, 'copy_bytes': 16, 'usable_capacity': 6}
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('near queue storage lacks the selected linker/MSC startup contract')


def require_assembly_frame_contract(report, profile, tool):
    if not any(r['module'] == 'root:1B73' and r.get('source_binding', {}).get('reframes')
               for r in report['translation_units'] if r.get('source_binding')):
        return
    contract = report.get('assembly_frame_contract', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    expected = {'canonical_data_frame': 'FAIL', 'reviewed_dgroup_frame': 'PASS'}
    if (not contract.get('all_required_checks_pass') or len(cases) != 2
            or {r['case'] for r in cases} != set(expected)
            or not all(r['passed'] and r['expected'] == r['actual'] == expected[r['case']] for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('assembly frame correction lacks the selected linker/shifted DGROUP contract')


def require_dgroup_rect_frame_contract(report, profile, tool):
    if not any((r.get('source_binding') or {}).get('segment_corrections')
               for r in report['translation_units']):
        return
    contract = report.get('dgroup_rect_frame_contract', {})
    required = contract.get('required_cases', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (contract.get('root_reviewed') is not True or not contract.get('all_required_checks_pass')
            or contract.get('segment_corrections') != [DGROUP_RECT_SEGMENT_CORRECTION]
            or Counter(required.values()) != Counter({'PASS': 1, 'FAIL': 1})
            or len(cases) != 2 or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']]
                       and not r.get('timed_out') and r.get('emulator_exit') == 0 for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('assembly SEG correction lacks the selected linker/shifted DGROUP contract')


def require_driver_ss_frame_contract(report, profile, tool):
    rows = [r for r in report['translation_units'] if r['module'] in DRIVER_SS_SITE_HASHES
            and r.get('source_binding', {}).get('reframes')]
    if not rows:
        return
    contract = report.get('driver_ss_frame_contract', {})
    expected = {'canonical_DATA': 'FAIL', 'reviewed_DGROUP': 'PASS'}
    cases = [r for r in contract.get('runtime_fixture', {}).get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    signatures = contract.get('signed_site_tuples', [])
    hashes = {module: hashlib.sha256(json.dumps(sorted(tuple(s[1:]) for s in signatures if s[0] == module),
                separators=(',', ':')).encode()).hexdigest() for module in DRIVER_SS_SITE_HASHES}
    if (contract.get('root_reviewed') is not True or not contract.get('all_required_checks_pass')
            or hashes != DRIVER_SS_SITE_HASHES or len(signatures) != 128
            or {r['module'] for r in rows} != set(DRIVER_SS_SITE_HASHES)
            or len(cases) != 2 or {r['variant'] for r in cases} != set(expected)
            or not all(r['passed'] and r['expected'] == r['actual'] == expected[r['variant']]
                       and r['actual_DS_SS_DGROUP'] and r['map']['passed']
                       and r['map']['data_group_delta'] > 0 for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('driver SS frames lack the selected linker/shifted DGROUP contract')


def require_pattern_bank_contract(report, profile, tool):
    rows = {r['module']: r for r in report['translation_units']
            if (r.get('source_binding') or {}).get('pattern_bank_owner')
            or (r.get('source_binding') or {}).get('pattern_bank_operands')}
    if not rows:
        return
    contract = report.get('pattern_bank_contract', {})
    required = contract.get('required_cases', {})
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (set(rows) != {'root:1B4E', 'S00:31AD'} or contract.get('root_reviewed') is not True
            or not contract.get('all_required_checks_pass') or contract.get('owner') != PATTERN_BANK_OWNER
            or contract.get('sites') != [['S00B_TEXT', offset] for offset in PATTERN_BANK_SITES]
            or Counter(required.values()) != Counter({'PASS': 1, 'FAIL': 2})
            or len(cases) != 3 or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] and r['expected'] == r['actual'] == required[r['case']]
                       and r['actual_DS_SS_DGROUP'] and r['shifted_data_group_delta'] > 0
                       and (r['actual'] != 'PASS' or r['all_256_formula_reads_checked']) for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('pattern bank lacks the selected linker/source owner contract')
    for row in rows.values():
        review_pattern_binding(row['source_binding'])


def require_s01_pattern_view_contract(report, profile, tool):
    rows = [r for r in report['translation_units'] if (r.get('source_binding') or {}).get('s01_pattern_view_operands')]
    if not rows:
        return
    from pathlib import Path
    contract = report.get('s01_pattern_view_contract', {})
    required = {'group_frame': 'PASS', 'wrong_segment_frame': 'FAIL', 'one_byte_shift': 'FAIL'}
    cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    components = [(str(Path(tool['directory'])/name), digest) for name,digest in tool['files'].items()]
    components += [(r['path'],r['sha256']) for r in report['runtime_components']]
    if (len(rows) != 1 or rows[0]['module'] != 'S01:3126'
            or contract.get('root_reviewed') is not True or contract.get('all_required_checks_pass') is not True
            or contract.get('owner') != PATTERN_BANK_OWNER
            or contract.get('sites') != [['S01:3126','S01A_TEXT',0x5A8,'_g_4220']]
            or contract.get('required_cases') != required or len(cases) != 3
            or {r['case'] for r in cases} != set(required)
            or not all(r['passed'] is True and r['actual'] == r['expected'] == required[r['case']]
                       and r['runner_returncode'] == 0 and r['actual_DS_SS_DGROUP'] is True
                       and r['dgroup_data_shift'] > 0 and r['map']['passed'] is True
                       and r.get('linker_diagnostics') == [] and r.get('linker_produced_executable') is True
                       for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path,digest in components)):
        raise ValueError('S01 pattern view lacks selected linker/source-owner/frame proof')
    review_s01_pattern_view(rows[0]['source_binding'])
    require_pattern_bank_contract(report, profile, tool)
    require_driver_ss_frame_contract(report, profile, tool)


def require_local_frame_contract(report, profile, tool):
    rows = [r for r in report['translation_units'] if (r.get('source_binding') or {}).get('local_reframes')]
    if not rows:
        return
    contract = report.get('driver_local_frame_contract', {})
    signatures = [[module, segment, offset, '_DATA'] for module, sites in LOCAL_SS_SITES.items()
                  for segment, offset, _, _ in sites]
    expected = {'canonical_DATA': 'FAIL', 'reviewed_DGROUP': 'PASS'}
    cases = [r for r in contract.get('runtime_fixture', {}).get('cases', []) if r['linker'] == profile]
    identities = {runtime_component_path(p['path']): p['sha256'] for p in contract.get('inputs', [])}
    from pathlib import Path
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    if (contract.get('root_reviewed') is not True or not contract.get('all_required_checks_pass')
            or contract.get('signed_site_tuples') != signatures or {r['module'] for r in rows} != set(LOCAL_SS_SITES)
            or len(cases) != 2 or {r['variant'] for r in cases} != set(expected)
            or not all(r['passed'] and r['expected'] == r['actual'] == expected[r['variant']]
                       and r['actual_DS_SS_DGROUP'] and r['map']['passed']
                       and r['map']['data_group_delta'] > 0 and r['map']['segment_frame_skew'] == 2 for r in cases)
            or any(identities.get(runtime_component_path(path)) != digest for path, digest in components)):
        raise ValueError('local SS frames lack the selected linker/source owner contract')
    for row in rows:
        review_local_frame_sites(row['source_binding'])


def bind_data_alias(spec, obj, row, module, symbols):
    """Bind a reviewed consumer view to a public in its one source owner."""
    if (module['source'] != spec['source'] or
            module['source_sha256'] != spec['source_sha256']):
        raise ValueError('data alias source owner changed')
    placement = module['placements'][spec['segment']]
    segment = (spec['segment'].replace('UNIT', row['basename'], 1)
               if spec['segment'].startswith('UNIT') else spec['segment'])
    public = [p for p in obj.publics if p['name'] == spec['owner']]
    if len(public) != 1 or (public[0]['segment'], public[0]['offset']) != (segment, spec['owner_offset']):
        raise ValueError('data alias public does not match its reviewed source location')
    if obj.segment_length(segment) != placement['size']:
        raise ValueError('data alias contribution extent changed')
    if not (0 <= spec['offset'] < spec['owner_size'] and spec['view_size'] > 0
            and spec['offset'] + spec['view_size'] <= spec['owner_size']
            and spec['owner_offset'] + spec['owner_size'] <= placement['size']):
        raise ValueError('data alias view extends outside its existing source object')
    address = symbols['data'][spec['alias'][1:]]
    historical = (placement['seg'], placement['off'] + spec['owner_offset'] + spec['offset'])
    if historical != (address['seg'], address['off']):
        raise ValueError('data alias view conflicts with reviewed consumer address')
    return {'alias': spec['alias'], 'owner': spec['owner'], 'offset': spec['offset'],
            'kind': 'data', 'reason': 'reviewed source owner/interior view',
            'module': row['module'], 'address': list(historical),
            'object_public': public[0], 'owner_size': spec['owner_size'],
            'view_size': spec['view_size'], 'source_anchor': spec['source_anchor']}


def verify_objects(original, generated, binding):
    review_frame_sites(binding)
    review_pattern_binding(binding)
    review_local_frame_sites(binding)
    review_segment_corrections(binding)
    review_indexed_binding(binding)
    review_graphics_binding(binding)
    review_s01_pattern_view(binding)
    debug = binding.get('debug_contributions', {})
    for segment, contract in debug.items():
        if (not binding.get('queue_storage') or segment not in ('$$SYMBOLS', '$$TYPES')
                or debug_fingerprint(original, segment) != contract['control']
                or debug_fingerprint(generated, segment) != contract['generated']):
            raise ValueError('unreviewed compiler debug contribution or relocation')
    defs = lambda obj: [s for s in obj.segment_defs if s['name'] not in debug]
    lengths = lambda obj: {s: n for s, n in obj.segment_lengths.items() if s not in debug}
    expected_communals = Counter(communal_key(c) for c in original.communals)
    expected_communals.update(communal_key(c) for c in binding.get('communals', []))
    if expected_communals != Counter(communal_key(c) for c in generated.communals):
        raise ValueError('DOS binding changed communal type, extent or ownership')
    if binding.get('scalar_storage') or binding.get('array_storage'):
        names = {c['name'] for c in binding['communals']}
        expected_scopes = ['communal' if name in names else scope
                           for name, scope in zip(original.externals, original.external_scopes)]
        if (original.externals != generated.externals
                or expected_scopes != generated.external_scopes
                or not names <= {name for name, scope in zip(original.externals, original.external_scopes)
                                 if scope == 'external'}
                or [fixup_key(f) for f in original.linker_fixups] !=
                   [fixup_key(f) for f in generated.linker_fixups]):
            raise ValueError('scalar storage changed external scope or ordered relocations')
    if (lengths(original) != lengths(generated)
            or set(original.segments) != set(generated.segments)
            or defs(original) != defs(generated) or original.groups != generated.groups):
        raise ValueError('DOS binding changed segment extents')
    public_key = lambda p: (p['name'], p['segment'], p['offset'])
    expected_publics = Counter(public_key(p) for p in original.publics)
    expected_publics.update(public_key(p) for p in binding.get('exports', []))
    if expected_publics != Counter(public_key(p) for p in generated.publics):
        raise ValueError('DOS binding changed an existing public or exported wrong storage')
    original_fixups = [dict(f) for f in original.linker_fixups if f['segment'] not in debug]
    frame_checks = []
    for spec in binding.get('reframes', []) + binding.get('local_reframes', []):
        matches = [f for f in original_fixups if f['segment'] == spec['segment']
                   and f['offset'] == spec['offset'] and f['target_kind'] == spec.get('target_kind', 'external')
                   and f['target'] == spec['target']]
        if len(matches) != 1:
            raise ValueError('unreviewed assembly frame correction location')
        f = matches[0]
        if ((f['width'], f['loc'], f['self_relative'], f['frame_kind'], f['frame'],
                f['displacement'], f['encoded_addend']) !=
                (2, 'offset16', False, spec['old_frame_kind'], spec['old_frame'], spec.get('displacement', 0), '0000')):
            raise ValueError('assembly frame correction changed a different operand')
        if (spec['frame_kind'], spec['frame']) != ('group', 'DGROUP'):
            raise ValueError('assembly frame correction is not DGROUP')
        f.update(frame_kind=spec['frame_kind'], frame=spec['frame'])
        frame_checks.append(spec)
    for spec in binding.get('segment_corrections', []):
        matches = [f for f in original_fixups if (f['segment'], f['offset']) ==
                   (spec['segment'], spec['offset'])]
        if len(matches) != 1 or any(matches[0][k] != v for k, v in spec['old'].items()):
            raise ValueError('assembly SEG correction changed a different operand')
        matches[0].update(spec['new'])
        frame_checks.append(spec)
    old_fixups = Counter(fixup_key(f) for f in original_fixups)
    new_fixups = Counter(fixup_key(f) for f in generated.linker_fixups if f['segment'] not in debug)
    if old_fixups - new_fixups:
        raise ValueError('DOS binding changed an existing relocation')
    additions = new_fixups - old_fixups
    if [fixup_key(f) for f in original_fixups] != [
            fixup_key(f) for f in generated.linker_fixups
            if f['segment'] not in debug and not additions[fixup_key(f)]]:
        raise ValueError('assembly frame correction changed ordered existing relocations')
    actual = [f for f in generated.linker_fixups if additions[fixup_key(f)]]
    if len(actual) != sum(s['count'] for s in binding.get('relocations', [])):
        raise ValueError('DOS binding added unexpected relocations')
    remaining = actual[:]
    fields = set()
    checks = []
    for spec in binding.get('relocations', []):
        matches = [f for f in remaining if f['target_kind'] == spec['target_kind']
                   and f['target'] == spec['target']
                   and f['encoded_addend'] == spec['encoded_addend']
                   and f['displacement'] == spec['displacement']]
        if len(matches) != spec['count']:
            raise ValueError('DOS binding relocation target/addend mismatch')
        if spec.get('pattern_operand') and sorted((f['segment'], f['offset']) for f in matches) != [
                (spec['segment'], offset) for offset in PATTERN_BANK_SITES]:
            raise ValueError('pattern bank relocation location set changed')
        if (spec.get('indexed_operand') or spec.get('graphics_mask_operand') or spec.get('s01_pattern_view_operand')) and sorted(
                (f['segment'], f['offset']) for f in matches) != [
                (spec['segment'], offset) for offset in spec['offsets']]:
            raise ValueError('indexed relocation location set changed')
        for f in matches:
            if (f['width'] != 2 or f['loc'] != 'offset16' or f['self_relative']
                    or f['frame_kind'] != spec['frame_kind']
                    or f['frame'] != spec['frame']):
                raise ValueError('DOS binding relocation frame/width mismatch')
            segment, offset = f['segment'], f['offset']
            if spec.get('storage_pointer'):
                owner = [p for p in generated.publics if p['name'] == spec['owner']]
                if (not binding.get('queue_storage') or len(owner) != 1
                        or (segment, offset) != (spec['segment'], spec['offset'])
                        or (owner[0]['segment'], owner[0]['offset']) != (segment, spec['owner_offset'])
                        or offset != spec['owner_offset'] + spec['field_offset']):
                    raise ValueError('DOS queue pointer replaced another storage field')
            elif not segment.endswith('_TEXT'):
                raise ValueError('DOS binding attempted to replace a storage field')
            raw = original.segment_bytes(segment)[offset:offset+2]
            if int.from_bytes(raw, 'little') != spec['original_value']:
                raise ValueError('DOS binding replaced a different historical operand')
            if spec.get('target_label'):
                public = next(p for p in generated.publics if p['name'] == spec['target_label'])
                if (public['segment'] != f['target'] or public['offset'] !=
                        f['displacement'] + int.from_bytes(bytes.fromhex(f['encoded_addend']), 'little')):
                    raise ValueError('DOS binding callback does not address its existing procedure')
            fields.update((segment, offset+i) for i in range(2))
            checks.append({'segment': segment, 'offset': offset,
                           'old_operand': spec['original_value'], 'target': f['target'],
                           'frame': f['frame'], 'displacement': f['displacement'],
                           'addend': f['encoded_addend']})
            remaining.remove(f)
    for segment in original.segments:
        if segment in debug:
            continue  # Entire bytes/definitions/fixups already checked by exact fingerprints.
        before, after = original.segment_bytes(segment), generated.segment_bytes(segment)
        if len(before) != len(after) or any(a != b and (segment, i) not in fields
                                          for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('DOS binding changed bytes outside reviewed address operands')
    return {'status': 'PASS', 'segment_extents_unchanged': not bool(debug),
            'live_segment_extents_unchanged': True,
            'existing_publics_and_relocations_unchanged': not bool(debug or frame_checks),
            'live_existing_publics_and_relocations_unchanged': not bool(frame_checks),
            'reviewed_frame_corrections': frame_checks,
            'storage_bytes_unchanged': not any(s.get('storage_pointer') for s in binding.get('relocations', [])),
            'reviewed_debug_contributions': debug, 'added_exports': binding.get('exports', []),
            'added_communals': binding.get('communals', []),
            'symbolic_operand_checks': checks}


# Closed initialized owners: source recipes, not an executable-byte provider.
PROVIDER_SPECS['source-owned:graphics-formulas'] = ('GFXOWNER', None, (('_g_2100', 8), ('_mono_tail_masks', 8), ('_packed_tail_masks', 2)), '#define PLANE_BIT(phase) \\ ((unsigned char)(0x80u >> (phase))) unsigned char near g_2100[8] = { PLANE_BIT(0), PLANE_BIT(1), PLANE_BIT(2), PLANE_BIT(3), PLANE_BIT(4), PLANE_BIT(5), PLANE_BIT(6), PLANE_BIT(7) }; #define BYTE_TAIL_MASK(residue) \\ ((unsigned char)((residue) == 0 ? 0xFFu : \\ ((0xFFu << (8 - (residue))) & 0xFFu))) unsigned char near mono_tail_masks[8] = { BYTE_TAIL_MASK(0), BYTE_TAIL_MASK(1), BYTE_TAIL_MASK(2), BYTE_TAIL_MASK(3), BYTE_TAIL_MASK(4), BYTE_TAIL_MASK(5), BYTE_TAIL_MASK(6), BYTE_TAIL_MASK(7) }; #define PACKED_TAIL_MASK(is_odd) \\ ((unsigned char)((is_odd) ? (0xFFu & ~0x0Fu) : 0xFFu)) unsigned char near packed_tail_masks[2] = { PACKED_TAIL_MASK(0), PACKED_TAIL_MASK(1) };')
PROVIDER_SPECS['source-owned:g2108-color-translation'] = ('G210808', None, (('_g_2108', 16),), 'unsigned char near g_2108[16] = { 0x00F, 0x00E, 0x00C, 4, 0x00D, 5, 1, 0x00B, 2, 0x00A, 6, 6, 7, 7, 8, 0 };')


# Reviewed functional FAR_BSS owners. These definitions establish types and
# extents, not historical communal order, padding or producing TUs.
PROVIDER_SPECS['source-owned:ant-list-counts'] = ('ALCOUNT', None, (('_ListIndexA', 2), ('_ListIndexB', 2), ('_ListIndexR', 2)), 'int far ListIndexA; int far ListIndexB; int far ListIndexR;')
PROVIDER_SPECS['source-owned:colony-simulation-words'] = ('COLWORD', None, (('_fd_50F6_0254', 2), ('_fd_50F6_02BE', 2), ('_fd_50F6_032C', 2), ('_fd_50F6_0352', 2), ('_fd_50F6_0356', 2), ('_fd_50F6_03E0', 2), ('_fd_50F6_03E2', 2), ('_fd_50F6_0400', 2)), 'int far fd_50F6_0254; int far fd_50F6_02BE; int far fd_50F6_032C; int far fd_50F6_0352; int far fd_50F6_0356; int far fd_50F6_03E0; int far fd_50F6_03E2; int far fd_50F6_0400;')
PROVIDER_SPECS['source-owned:player-locations'] = ('PLOCOWN', None, (('_MeLocX', 2), ('_MeLocY', 2), ('_MePlane', 2), ('_RedLocX', 2), ('_RedLocY', 2), ('_RedPlane', 2)), 'int far MeLocX; int far MeLocY; int far MePlane; int far RedLocX; int far RedLocY; int far RedPlane;')
PROVIDER_SPECS['source-owned:ant-counters-timer'] = ('ANTCTR', None, (('_BAntsEaten', 4), ('_RAntsEaten', 4), ('_fd_50F6_0620', 4)), 'long far BAntsEaten; long far RAntsEaten; long far fd_50F6_0620;')
PROVIDER_SPECS['source-owned:language-string-list-pointers'] = ('LANGPTR', None, (('_AdviceStrs', 4), ('_fd_50F6_02BA', 4), ('_fd_50F6_0324', 4), ('_fd_50F6_0328', 4), ('_fd_50F6_0368', 4)), 'typedef char far * far *StrList; StrList far AdviceStrs; StrList far fd_50F6_02BA; StrList far fd_50F6_0324; StrList far fd_50F6_0328; StrList far fd_50F6_0368;')
PROVIDER_SPECS['source-owned:dead-ant-coordinate-rings'] = ('DEADXY', None, (('_fd_50F6_037C', 100), ('_fd_50F6_0404', 100)), 'unsigned char far fd_50F6_037C[100]; unsigned char far fd_50F6_0404[100];')
PROVIDER_SPECS['source-owned:ant-player-state'] = ('ANTSTATE', None, (('_FuzLocX', 2), ('_FuzLocY', 2), ('_MeHealth', 2), ('_ModeAuto', 2), ('_StrategicModeB', 2), ('_TilesDugR', 2)), 'int far FuzLocX; int far FuzLocY; int far MeHealth; int far ModeAuto; int far StrategicModeB; int far TilesDugR;')
PROVIDER_SPECS['source-owned:display-mode-selector'] = ('MODEOWN', None, (('_g_5A97', 1),), 'char near g_5A97;')

FAR_PROVIDER_MODULES.update({'source-owned:ant-counters-timer',
 'source-owned:ant-list-counts',
 'source-owned:ant-player-state',
 'source-owned:colony-simulation-words',
 'source-owned:dead-ant-coordinate-rings',
 'source-owned:language-string-list-pointers',
 'source-owned:player-locations'})

V15_STORAGE_ANCHORS = {'_ListIndexA': (3434, ('ListIndexA', 'fd_50F6_0D6A')),
 '_ListIndexB': (3496, ('ListIndexB', 'fd_50F6_0DA8')),
 '_ListIndexR': (3754, ('ListIndexR', 'fd_50F6_0EAA')),
 '_fd_50F6_0254': (596, ('fd_50F6_0254',)),
 '_fd_50F6_02BE': (702, ('fd_50F6_02BE',)),
 '_fd_50F6_032C': (812, ('fd_50F6_032C',)),
 '_fd_50F6_0352': (850, ('fd_50F6_0352',)),
 '_fd_50F6_0356': (854, ('fd_50F6_0356',)),
 '_fd_50F6_03E0': (992, ('fd_50F6_03E0',)),
 '_fd_50F6_03E2': (994, ('fd_50F6_03E2',)),
 '_fd_50F6_0400': (1024, ('fd_50F6_0400',)),
 '_MeLocX': (1148, ('MeLocX', 'fd_50F6_047C')),
 '_MeLocY': (1162, ('MeLocY', 'fd_50F6_048A')),
 '_MePlane': (1164, ('MePlane', 'fd_50F6_048C')),
 '_RedLocX': (1168, ('RedLocX',)),
 '_RedLocY': (1172, ('RedLocY',)),
 '_RedPlane': (1176, ('RedPlane',)),
 '_BAntsEaten': (3872, ('BAntsEaten',)),
 '_RAntsEaten': (3968, ('RAntsEaten',)),
 '_fd_50F6_0620': (1568, ('fd_50F6_0620',)),
 '_AdviceStrs': (864, ('AdviceStrs',)),
 '_fd_50F6_02BA': (698, ('fd_50F6_02BA',)),
 '_fd_50F6_0324': (804, ('fd_50F6_0324',)),
 '_fd_50F6_0328': (808, ('fd_50F6_0328',)),
 '_fd_50F6_0368': (872, ('fd_50F6_0368',)),
 '_fd_50F6_037C': (892, ('fd_50F6_037C',)),
 '_fd_50F6_0404': (1028, ('fd_50F6_0404',)),
 '_FuzLocX': (554, ('FuzLocX',)),
 '_FuzLocY': (568, ('FuzLocY',)),
 '_MeHealth': (3960, ('MeHealth', 'fd_50F6_0F78')),
 '_ModeAuto': (888, ('ModeAuto', 'fd_50F6_0378')),
 '_StrategicModeB': (4244, ('StrategicModeB',)),
 '_TilesDugR': (562, ('TilesDugR', 'fd_50F6_0232'))}

V15_STORAGE_CONTRACTS = {'source-owned:ant-list-counts': ('ant_list_counts_contract',
                                  {'SaveRec_BYTE_exact_aliases': 'PASS',
                                   'SaveRec_BYTE_wrong_ListIndexA_alias_plus2': 'FAIL',
                                   'SaveRec_BYTE_wrong_ListIndexB_alias_plus2': 'FAIL',
                                   'SaveRec_BYTE_wrong_ListIndexR_alias_plus2': 'FAIL',
                                   'initialized_nonzero_owner_SaveRec_BYTE': 'FAIL',
                                   'initialized_nonzero_owner_word': 'FAIL',
                                   'typed_word_exact_aliases': 'PASS',
                                   'typed_word_wrong_ListIndexA_alias_plus2': 'FAIL',
                                   'typed_word_wrong_ListIndexB_alias_plus2': 'FAIL',
                                   'typed_word_wrong_ListIndexR_alias_plus2': 'FAIL',
                                   'unsigned_consumer_sign_contrast': 'FAIL',
                                   'wrong_four_byte_extent_long_owner': 'FAIL'}),
 'source-owned:colony-simulation-words': ('colony_simulation_words_contract',
                                          {'initialized_nonzero_owner_rejected': 'FAIL_ZERO',
                                           'one_byte_interior_SaveRec_view_rejected': 'FAIL_PTR',
                                           'signed_word_and_exact_SaveRec_byte_views': 'PASS'}),
 'source-owned:player-locations': ('player_locations_contract',
                                   {'SaveRec_byte_exact_aliases': 'PASS',
                                    'nonzero_initializer_rejected': 'FAIL_ZERO',
                                    'typed_word_exact_aliases': 'PASS',
                                    'unsigned_consumer_sign_contrast': 'UNSIGNED_CONTRAST',
                                    'wrong_MeLocX_alias_plus2': 'FAIL_ALIAS',
                                    'wrong_MeLocY_alias_plus2': 'FAIL_ALIAS',
                                    'wrong_MePlane_alias_plus2': 'FAIL_ALIAS'}),
 'source-owned:ant-counters-timer': ('ant_counters_timer_contract',
                                     {'SaveRec_four_byte_view': 'PASS',
                                      'initialized_owner_startup_negative': 'FAIL',
                                      'signed_long_semantics': 'PASS',
                                      'typed_owner_startup_roundtrip': 'PASS',
                                      'unsigned_long_view_negative': 'FAIL',
                                      'wrong_SaveRec_count': 'FAIL',
                                      'wrong_SaveRec_size': 'FAIL',
                                      'wrong_two_byte_consumer_view': 'FAIL'}),
 'source-owned:language-string-list-pointers': ('language_string_list_pointers_contract',
                                                {'independent_BYTE_pointer_storage_roundtrip': 'PASS',
                                                 'initialized_nonzero_owner_BYTE_zero_contrast': 'FAIL',
                                                 'initialized_nonzero_owner_typed_zero_contrast': 'FAIL',
                                                 'typed_far_pointer_halves_zero_and_write': 'PASS',
                                                 'wrong_eight_byte_array_extent_view': 'FAIL',
                                                 'wrong_near_outer_pointer_view': 'FAIL',
                                                 'wrong_near_row_pointer_view': 'FAIL',
                                                 'wrong_pointer_depth_view': 'FAIL'}),
 'source-owned:dead-ant-coordinate-rings': ('dead_ant_coordinate_rings_contract',
                                            {'SaveRec_direct_byte_view': 'PASS',
                                             'initialized_nonzero_owner': 'FAIL',
                                             'typed_unsigned_byte_exact_base_and_extent': 'PASS',
                                             'wrong_base_plus1': 'FAIL',
                                             'wrong_extent_101': 'FAIL',
                                             'wrong_signed_byte_view': 'FAIL'}),
 'source-owned:ant-player-state': ('ant_player_state_words_contract',
                                   {'SaveRec_BYTE_exact_aliases': 'PASS',
                                    'SaveRec_BYTE_wrong_MeHealth_alias_plus2': 'FAIL',
                                    'SaveRec_BYTE_wrong_ModeAuto_alias_plus2': 'FAIL',
                                    'SaveRec_BYTE_wrong_TilesDugR_alias_plus2': 'FAIL',
                                    'initialized_nonzero_owner_SaveRec_BYTE': 'FAIL',
                                    'initialized_nonzero_owner_word': 'FAIL',
                                    'typed_word_exact_aliases': 'PASS',
                                    'typed_word_wrong_MeHealth_alias_plus2': 'FAIL',
                                    'typed_word_wrong_ModeAuto_alias_plus2': 'FAIL',
                                    'typed_word_wrong_TilesDugR_alias_plus2': 'FAIL',
                                    'unsigned_consumer_sign_contrast': 'FAIL',
                                    'wrong_four_byte_extent_long_owner': 'FAIL'})}


# Reviewed functional control/resource/terrain owners; no historical TU claim.
PROVIDER_SPECS['source-owned:ant-ui-control-state'] = ('ANTCTRL', None, (('_casteLevels', 6), ('_modeLevels', 6), ('_knobSize', 4), ('_triHeight', 2), ('_triWidth', 2), ('_triWidthL', 2), ('_triWidthR', 2), ('_fd_50F6_3816', 12), ('_fd_50F6_3822', 12), ('_fd_50F6_382E', 4), ('_fd_50F6_0358', 4), ('_fd_50F6_022E', 4)), 'struct TriLevel { unsigned frac; unsigned mid; unsigned weight; }; struct Pt { int x; int y; }; struct TriPoints { int apexX; int apexY; int leftX; int leftY; int rightX; int rightY; }; struct TriLevel far casteLevels; struct TriLevel far modeLevels; struct Pt far knobSize; unsigned far triHeight; unsigned far triWidth; unsigned far triWidthL; unsigned far triWidthR; struct TriPoints far fd_50F6_3816; struct TriPoints far fd_50F6_3822; long far fd_50F6_382E; struct Pt far fd_50F6_0358; struct Pt far fd_50F6_022E;')
FAR_PROVIDER_MODULES.add('source-owned:ant-ui-control-state')
PROVIDER_SPECS['source-owned:ui-resource-scalars'] = ('UIRESOWN', None, (('_win_numOfWindows', 2), ('_win_numOfColors', 2), ('_win_numOfGroups', 2), ('_fd_50F6_3B4C', 4), ('_fd_50F6_3B58', 4), ('_fd_50F6_3B5C', 4)), 'typedef struct { unsigned int age; int file; int page; } EmsSlot; typedef char far * far *Handle; int far win_numOfWindows; int far win_numOfColors; int far win_numOfGroups; EmsSlot far * far * far fd_50F6_3B4C; void (far * far fd_50F6_3B58)(char far *, char far *, int, int); Handle far fd_50F6_3B5C;')
FAR_PROVIDER_MODULES.add('source-owned:ui-resource-scalars')
PROVIDER_SPECS['source-owned:terrain-state-words'] = ('TERRNOWN', None, (('_Barrier', 2), ('_TERRAINset', 2)), 'int far Barrier; int far TERRAINset;')
FAR_PROVIDER_MODULES.add('source-owned:terrain-state-words')
V17_STORAGE_ANCHORS = {'_Barrier': (1152, ('Barrier', 'fd_50F6_0480')),
 '_TERRAINset': (3876, ('TERRAINset', 'fd_50F6_0F24')),
 '_casteLevels': (1154, ('casteLevels', 'fd_50F6_0482')),
 '_fd_50F6_022E': (558, ('fd_50F6_022E',)),
 '_fd_50F6_0358': (856, ('fd_50F6_0358',)),
 '_fd_50F6_3816': (14358, ('fd_50F6_3816',)),
 '_fd_50F6_3822': (14370, ('fd_50F6_3822',)),
 '_fd_50F6_382E': (14382, ('fd_50F6_382E',)),
 '_fd_50F6_3B4C': (15180, ('fd_50F6_3B4C',)),
 '_fd_50F6_3B58': (15192, ('fd_50F6_3B58',)),
 '_fd_50F6_3B5C': (15196, ('fd_50F6_3B5C',)),
 '_knobSize': (14386, ('fd_50F6_3832', 'knobSize')),
 '_modeLevels': (1182, ('fd_50F6_049E', 'modeLevels')),
 '_triHeight': (14350, ('fd_50F6_380E', 'triHeight')),
 '_triWidth': (14356, ('fd_50F6_3814', 'triWidth')),
 '_triWidthL': (14352, ('fd_50F6_3810', 'triWidthL')),
 '_triWidthR': (14354, ('fd_50F6_3812', 'triWidthR')),
 '_win_numOfColors': (18390, ('fd_50F6_47D6', 'win_numOfColors')),
 '_win_numOfGroups': (18388, ('fd_50F6_47D4', 'win_numOfGroups')),
 '_win_numOfWindows': (18392, ('fd_50F6_47D8', 'win_numOfWindows'))}

V17_STORAGE_CONTRACTS = {
    'source-owned:ant-ui-control-state': ('ant_ui_control_state_contract', {'typed_struct_array_save_views': 'PASS'}),
    'source-owned:ui-resource-scalars': ('ui_resource_scalars_contract', {
        'typed_startup_and_roundtrip': 'PASS', 'wrong_scalar_width_guard': 'FAIL',
        'initialized_owner_zero_startup_guard': 'FAIL'}),
    'source-owned:terrain-state-words': ('terrain_state_words_contract', {
        'signed_word_exact_two_byte_save_view': 'PASS',
        'one_byte_interior_save_view_rejected': 'FAIL_PTR',
        'initialized_nonzero_owner_rejected': 'FAIL_ZERO',
        'unsigned_consumer_is_semantically_different': 'TYPE_NEGATIVE_UNSIGNED_VIEW'}),
}

# Functional serialized owners: complete source-visible saved spans, no
# historical COMDEF TU, placement or communal-order claim.
PROVIDER_SPECS['source-owned:swarm-serialized-buffers'] = ('SWARMOWN', None,
    (('_fd_50F6_0F46', 50), ('_fd_50F6_0F84', 50), ('_fd_50F6_0FC6', 50), ('_fd_50F6_1008', 50)),
    'unsigned char far fd_50F6_0F46[50]; unsigned char far fd_50F6_0F84[50]; '
    'unsigned char far fd_50F6_0FC6[50]; unsigned char far fd_50F6_1008[50];')
PROVIDER_SPECS['source-owned:population-work-arrays'] = ('POPWORK', None,
    (('_fd_50F6_0AEC', 12), ('_fd_50F6_0AFA', 12)),
    'int far fd_50F6_0AEC[6]; int far fd_50F6_0AFA[6];')
FAR_PROVIDER_MODULES.update({'source-owned:swarm-serialized-buffers', 'source-owned:population-work-arrays'})
FAR_PROVIDER_WORD_ARRAYS['source-owned:population-work-arrays'] = {'_fd_50F6_0AEC', '_fd_50F6_0AFA'}
V18_STORAGE_ANCHORS = {
    '_fd_50F6_0F46': (0x0F46, ('fd_50F6_0F46',)),
    '_fd_50F6_0F84': (0x0F84, ('fd_50F6_0F84',)),
    '_fd_50F6_0FC6': (0x0FC6, ('fd_50F6_0FC6',)),
    '_fd_50F6_1008': (0x1008, ('fd_50F6_1008',)),
    '_fd_50F6_0AEC': (0x0AEC, ('fd_50F6_0AEC',)),
    '_fd_50F6_0AFA': (0x0AFA, ('fd_50F6_0AFA',)),
}
V18_STORAGE_CONTRACTS = {
    'source-owned:swarm-serialized-buffers': ('swarm_serialized_buffers_contract', {
        'zero': 'PASS', 'typed': 'PASS', 'saverec': 'PASS',
        'wrong_type': 'FAIL', 'wrong_extent': 'FAIL', 'wrong_base': 'FAIL'}),
    'source-owned:population-work-arrays': ('population_work_arrays_contract', {
        'typed_SaveRec_alias_positive': 'PASS',
        'wrong_element_type_same_12_byte_extent': 'REJECTED',
        'wrong_sixth_word_array_extent': 'REJECTED_GUARD_OVERLAP',
        'wrong_exact_base_plus_one_word': 'REJECTED',
        'wrong_SaveRec_count_extent': 'REJECTED'}),
}


def require_v18_storage_contracts(report, profile, tool):
    _require_reviewed_storage_contracts(report, profile, tool, V18_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V18_STORAGE_CONTRACTS)


PROVIDER_SPECS['source-owned:saved-sound-state'] = ('SNDSTATE', None,
    (('_fd_50F6_01F0', 14),), 'int far fd_50F6_01F0[7];')
PROVIDER_SPECS['source-owned:control-flag-words'] = ('CTRLFLAG', None,
    (('_fd_50F6_0468', 2), ('_fd_50F6_0370', 2), ('_fd_50F6_024E', 2)),
    'int far fd_50F6_0468; int far fd_50F6_0370; int far fd_50F6_024E;')
PROVIDER_SPECS['source-owned:count-ants-transition-word'] = ('ANTLATCH', None,
    (('_fd_50F6_0354', 2),), 'int far fd_50F6_0354;')
FAR_PROVIDER_MODULES.update({'source-owned:saved-sound-state', 'source-owned:control-flag-words',
                            'source-owned:count-ants-transition-word'})
FAR_PROVIDER_WORD_ARRAYS['source-owned:saved-sound-state'] = {'_fd_50F6_01F0'}
V19_STORAGE_ANCHORS = {
    '_fd_50F6_01F0': (0x01F0, ('fd_50F6_01F0',)),
    '_fd_50F6_0468': (0x0468, ('fd_50F6_0468',)),
    '_fd_50F6_0370': (0x0370, ('fd_50F6_0370',)),
    '_fd_50F6_024E': (0x024E, ('fd_50F6_024E',)),
    '_fd_50F6_0354': (0x0354, ('fd_50F6_0354',)),
}
V19_STORAGE_CONTRACTS = {
    'source-owned:saved-sound-state': ('saved_sound_state_contract', {
        'far_bss_zero_at_main': 'PASS', 'initialized_nonzero_control': 'FAIL',
        # These measure rejected shapes; their in-bounds zero reads do pass.
        'wrong_width_control': 'PASS', 'short_extent_control': 'PASS'}),
    'source-owned:control-flag-words': ('control_flag_words_contract', {
        'positive': 'PASS',
        'wrong_type': 'NEGATIVE: wrong_type unsigned view is 65535\nPROGRAM_NONZERO',
        'wrong_extent': 'NEGATIVE: wrong_extent one-byte word overwrote guard\nPROGRAM_NONZERO',
        'wrong_base': 'FAIL SaveRec2 address\nPROGRAM_NONZERO'}),
    'source-owned:count-ants-transition-word': ('count_ants_transition_word_contract', {
        'typed_word': 'PASS_TYPED_WORD', 'saverec_byte': 'PASS_SAVEREC_BYTE',
        'wrong_width_long_owner': 'WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED',
        'wrong_signedness_unsigned_view': 'WRONG_UNSIGNED_VIEW_DETECTED',
        'initialized_nonzero_owner': 'INITIALIZED_OWNER_DETECTED',
        'wrong_alias_base_plus_two': 'SHIFTED_ALIAS_BASE_DETECTED'}),
}


def require_v19_storage_contracts(report, profile, tool):
    _require_reviewed_storage_contracts(report, profile, tool, V19_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V19_STORAGE_CONTRACTS)
    modules = {r['module'] for r in report['translation_units']}
    if 'source-owned:saved-sound-state' in modules:
        contract = report.get('saved_sound_state_contract', {})
        shape = contract.get('candidate_source_contract', {})
        wanted = lambda count, width: [{'name': '_fd_50F6_01F0', 'kind': 'far',
            'count': count, 'element_size': width, 'length': count * width}]
        controls = contract.get('controls', {})
        if (shape.get('owner_comdef') != wanted(7, 2)
                or shape.get('wrong_width_comdef') != wanted(7, 4)
                or shape.get('short_extent_comdef') != wanted(6, 2)
                or not shape.get('nonzero_control_segments')
                or controls != dict.fromkeys(('initialized_nonzero_detected',
                    'wrong_width_shape_rejected', 'short_extent_shape_rejected',
                    'all_maps_have_clean_required_publics_and_separate_data_alias'), True)):
            raise ValueError('saved sound state lacks rejected compiler shapes')
        for case in contract['cases']:
            if case['linker'] != profile:
                continue
            layout = case.get('far_bss_layout', {})
            length = {'far_bss_zero_at_main': 14, 'wrong_width_control': 28,
                      'short_extent_control': 12}.get(case['case'])
            if (set(layout.get('required_publics', {})) != {'_fd_50F6_01F0', '_fd_55B3_74FE', '_main'}
                    or length is not None and (layout.get('owner_in_far_bss') is not True
                        or layout.get('owner_far_bss_region_length') != length)
                    or case.get('dosbox_exit') != 0):
                raise ValueError('saved sound state lacks actual startup/alias/extent controls')
    if 'source-owned:control-flag-words' in modules:
        controls = report.get('control_flag_words_contract', {}).get('compiler_negative_controls', [])
        if (len(controls) != 3 or not all(r.get('detected') is True for r in controls)
                or communal_key(controls[0].get('observed', {})) != ('_fd_50F6_024E', 'far', 1, 1, 1)
                or communal_key(controls[1].get('observed', {})) != ('_fd_50F6_0370', 'far', 4, 1, 4)
                or controls[2].get('still_communal') is not False
                or controls[2].get('public', {}).get('name') != '_fd_50F6_0468'
                or controls[2].get('segment', {}).get('class') != 'FAR_DATA'
                or controls[2].get('segment', {}).get('length') != 2):
            raise ValueError('control flag words lack rejected compiler shapes')


# Source-functional sound-control storage. All six words have complete signed
# word views; they are distinct objects, not an inferred packed common block.
PROVIDER_SPECS['source-owned:sound-control-words'] = ('SNDCTRL', None,
    (('_fd_50F6_4A46', 2), ('_fd_50F6_4A48', 2), ('_fd_50F6_4A4A', 2),
     ('_fd_50F6_4A4C', 2), ('_fd_50F6_4B14', 2), ('_fd_50F6_4B16', 2)),
    'int far fd_50F6_4A46; int far fd_50F6_4A48; int far fd_50F6_4A4A; '
    'int far fd_50F6_4A4C; int far fd_50F6_4B14; int far fd_50F6_4B16;')
FAR_PROVIDER_MODULES.add('source-owned:sound-control-words')
V20_STORAGE_ANCHORS = {
    '_fd_50F6_4A46': (0x4A46, ('fd_50F6_4A46',)),
    '_fd_50F6_4A48': (0x4A48, ('fd_50F6_4A48',)),
    '_fd_50F6_4A4A': (0x4A4A, ('fd_50F6_4A4A',)),
    '_fd_50F6_4A4C': (0x4A4C, ('fd_50F6_4A4C',)),
    '_fd_50F6_4B14': (0x4B14, ('fd_50F6_4B14',)),
    '_fd_50F6_4B16': (0x4B16, ('fd_50F6_4B16',)),
}
V20_STORAGE_CONTRACTS = {
    'source-owned:sound-control-words': ('sound_control_words_contract', {
        'typed_raw_positive': 'PASS_TYPED_RAW',
        'wrong_width_long_owner': 'WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED',
        'wrong_signedness_unsigned_view': 'WRONG_UNSIGNED_VIEW_DETECTED',
        'initialized_nonzero_owner': 'INITIALIZED_NONZERO_OWNER_DETECTED',
        'shifted_alias_base': 'SHIFTED_ALIAS_BASE_DETECTED'}),
}


def require_v20_storage_contracts(report, profile, tool):
    _require_reviewed_storage_contracts(report, profile, tool, V20_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V20_STORAGE_CONTRACTS)
    module = 'source-owned:sound-control-words'
    if not any(row['module'] == module for row in report['translation_units']):
        return
    contract = report.get('sound_control_words_contract', {})
    expected = provider_communals(module)
    controls = contract.get('compiler_controls', {})
    if (controls.get('owner_communals') != expected
            or controls.get('wider_communals') != [dict(c, count=4, length=4) for c in expected]
            or controls.get('unsigned_communals') != expected
            or controls.get('initialized_communal_absent') is not True
            or sorted(controls.get('initialized_publics', [])) != sorted(c['name'] for c in expected)):
        raise ValueError('sound control words lack measured compiler shapes')
    names = [name.lower() for name, _ in PROVIDER_SPECS[module][2]]
    for case in contract['cases']:
        if case['linker'] != profile:
            continue
        aliases = []
        for prefix, delta in {
                'typed_raw_positive': (('exact', 0),),
                'wrong_width_long_owner': (('whole', 0), ('upper', 2)),
                'shifted_alias_base': (('shift', 2),)}.get(case['case'], ()):
            aliases.extend((f'_probe{prefix}{i}', name, delta) for i, name in enumerate(names))
        relations = case.get('alias_map_relations', [])
        required = sorted(names + [alias for alias, _, _ in aliases])
        if (case.get('runner_returncode') != 0
                or case.get('all_required_publics_in_both_sections') is not True
                or sorted(case.get('required_publics', [])) != required
                or set(case.get('map_public_sections', {})) != {'Name', 'Value'}
                or any(section.get('heading_present') is not True
                       or section.get('missing_required_publics') != []
                       for section in case['map_public_sections'].values())
                or len(relations) != len(aliases)
                or sorted((r.get('alias'), r.get('target'), r.get('expected_offset_delta'))
                          for r in relations) != sorted(aliases)):
            raise ValueError('sound control words lack complete map/alias controls')
        for relation in relations:
            addresses = []
            for section in ('name', 'value'):
                try:
                    alias = tuple(int(n, 16) for n in relation[f'alias_address_{section}_section'].split(':'))
                    target = tuple(int(n, 16) for n in relation[f'target_address_{section}_section'].split(':'))
                except (KeyError, ValueError, AttributeError):
                    raise ValueError('sound control words lack measured alias addresses')
                if (len(alias) != 2 or len(target) != 2 or alias[0] != target[0]
                        or alias[1] != target[1] + relation['expected_offset_delta']):
                    raise ValueError('sound control word alias displacement changed')
                addresses.append((alias, target))
            if relation.get('passed') is not True or addresses[0] != addresses[1]:
                raise ValueError('sound control word map sections disagree')


# Complete source views and loop extents, independently checked by both linkers.
PROVIDER_SPECS['source-owned:sound-record-arrays'] = ('SNDRECS', None,
    (('_fd_50F6_0000', 336), ('_fd_50F6_4A4E', 198)),
    'union VoicePayload { long offset; char far *sample; }; struct Voice { int kind; '
    'union VoicePayload payload; }; struct Chan { char type; char num; char c2; '
    'char c3; char c4; char c5; }; struct Voice far fd_50F6_0000[56]; '
    'struct Chan far fd_50F6_4A4E[33];')
FAR_PROVIDER_MODULES.add('source-owned:sound-record-arrays')
FAR_PROVIDER_RECORD_ARRAYS['source-owned:sound-record-arrays'] = {
    '_fd_50F6_0000': 6, '_fd_50F6_4A4E': 6}
V21_STORAGE_ANCHORS = {'_fd_50F6_0000': (0, ('fd_50F6_0000',)),
                       '_fd_50F6_4A4E': (0x4A4E, ('fd_50F6_4A4E',))}
V21_STORAGE_CONTRACTS = {'source-owned:sound-record-arrays': ('sound_record_arrays_contract', {
    'positive_exact_provider': 'PASS',
    'wrong_total_size_57_voice_rows': 'LINKED',
    'wrong_record_stride_near_pointer': 'LINKED',
    'signed_word_unsigned_view_negative': 'UNSIGNED_WORD_CONTROL_DETECTED',
    'near_pointer_consumer_view_negative': 'NEAR_POINTER_CONTROL_DETECTED',
    'short_extent_55_voice_32_channels': 'LINKED',
    'initialized_storage_negative': 'INITIALIZED_CONTROL_DETECTED'})}

SOUND_RECORD_OFFSETS = [
    'sizeof(int)=2, sizeof(long)=4, sizeof(far data pointer)=4, sizeof(near data pointer)=2',
    'Voice: sizeof 6; kind@0; union payload@2; external array sizeof 336',
    'InstrSample(char far*), InstrByte(unsigned char far*), InstrVoid(void far*), Drv(int far*): sizeof 6 and payload@2',
    'Chan plain-char writer and unsigned-char reader views: sizeof 6; offsets 0,1,2,3,4,5; external array sizeof 198']

def require_v21_storage_contracts(report, profile, tool):
    _require_reviewed_storage_contracts(report, profile, tool, V21_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V21_STORAGE_CONTRACTS)
    _require_sound_record_controls(report, profile)
    _require_v21_scalar_controls(report, profile)

def _require_sound_record_controls(report, profile):
    module = 'source-owned:sound-record-arrays'
    if not any(row['module'] == module for row in report['translation_units']):
        return
    contract = report.get('sound_record_arrays_contract', {})
    expected = provider_communals(module)
    voice, chan = expected
    shapes = {
        'SNDRECS': expected, 'SNDUNSG': expected,
        'SND57': [dict(voice, count=57, length=342), chan],
        'SNDS4': [dict(voice, element_size=4, length=224), chan],
        'SND32': [dict(voice, count=55, length=330), dict(chan, count=32, length=192)],
        'SNDBASE': [dict(voice, name='_fd_50F6_0002'), chan], 'SNDINIT': []}
    controls = contract.get('compiler_controls', {})
    if (set(controls) != set(shapes)
            or contract.get('sizeof_offsetof_assertions') != SOUND_RECORD_OFFSETS):
        raise ValueError('sound record owners lack complete view/extent controls')
    for name, communals in shapes.items():
        row = controls[name]
        if row.get('communals') != communals or (name != 'SNDINIT' and (
                row.get('publics') != [] or row.get('nonempty_segments') != []
                or row.get('initialized_segment_names_and_hex') != {}
                or any(row.get('segment_lengths', {}).values()))):
            raise ValueError('sound record compiler contrast changed')
    init = controls['SNDINIT']
    segments = init.get('nonempty_segments', [])
    if (len(segments) != 1 or segments[0].get('class') != 'FAR_DATA'
            or segments[0].get('length') != 534
            or init.get('publics') != [
                {'name': voice['name'], 'offset': 0, 'segment': 'SNDINIT5_DATA'},
                {'name': chan['name'], 'offset': 336, 'segment': 'SNDINIT5_DATA'}]):
        raise ValueError('sound record initialized owner contrast changed')
    names = sorted(row['name'] for row in expected)
    lengths = {'wrong_total_size_57_voice_rows': 540,
               'wrong_record_stride_near_pointer': 422,
               'short_extent_55_voice_32_channels': 522}
    for case in contract['cases']:
        if case['linker'] != profile:
            continue
        sections = case.get('map_public_sections', {})
        layout = case.get('far_bss_layout', {})
        initialized = case['case'] == 'initialized_storage_negative'
        if (case.get('executed') is not True or case.get('dosbox_exit') != 0
                or set(sections) != {'Name', 'Value'}
                or any(section.get('heading_present') is not True
                       or any(name not in section.get('publics', {}) for name in names)
                       for section in sections.values())
                or any(sections['Name']['publics'][name] != sections['Value']['publics'][name]
                       for name in names)
                or layout.get('region_present') is not (not initialized)
                or (not initialized and layout.get('length') != lengths.get(case['case'], 534))):
            raise ValueError('sound record owners lack measured resolved map extents')
        addresses = []
        sizes = {'_fd_50F6_0000': 336, '_fd_50F6_4A4E': 198}
        if case['case'] == 'wrong_total_size_57_voice_rows': sizes[voice['name']] = 342
        elif case['case'] == 'wrong_record_stride_near_pointer': sizes[voice['name']] = 224
        elif case['case'] == 'short_extent_55_voice_32_channels':
            sizes = {voice['name']:330, chan['name']:192}
        for name in names:
            try:
                segment, offset = (int(n, 16) for n in sections['Name']['publics'][name].split(':'))
            except (KeyError, ValueError, AttributeError):
                raise ValueError('sound record owner address missing')
            if layout.get('symbols', {}).get(name.upper()) != {'segment':segment, 'offset':offset}:
                raise ValueError('sound record map address disagrees with measured owner')
            start = 16*segment+offset
            if not initialized and not (layout['start_linear'] <= start
                    and start+sizes[name]-1 <= layout['stop_linear']
                    and layout['stop_linear']-layout['start_linear']+1 == layout['length']):
                raise ValueError('sound record owner outside measured communal allocation')
            addresses.append((start, start+sizes[name]))
        if not (addresses[0][1] <= addresses[1][0] or addresses[1][1] <= addresses[0][0]):
            raise ValueError('sound record owners overlap')
    negatives = [r for r in contract.get('link_binding_negative_controls', []) if r.get('linker') == profile]
    if (len(negatives) != 1 or negatives[0].get('case') != 'wrong_symbol_base_name_negative'
            or negatives[0].get('executed') is not False or negatives[0].get('passed') is not True
            or negatives[0].get('diagnosed_symbol') != '_fd_50F6_0000'
            or negatives[0].get('unresolved_target_diagnosed') is not True
            or negatives[0].get('run_log_absent') is not True
            or negatives[0].get('actual_log') != ''
            or negatives[0].get('expected') != 'UNRESOLVED_NOT_EXECUTED'
            or negatives[0].get('actual') != 'UNRESOLVED_NOT_EXECUTED'
            or negatives[0].get('linker_produced_executable') is not True
            or negatives[0].get('linker_produced_map') is not True):
        raise ValueError('sound record wrong-name control was not diagnosed and kept unexecuted')
    sections = negatives[0].get('map_public_sections', {})
    wrong_names = ['_fd_50F6_0002', '_fd_50F6_4A4E']
    if (set(sections) != {'Name', 'Value'}
            or any(s.get('heading_present') is not True
                   or any(n not in s.get('publics', {}) for n in wrong_names)
                   or '_fd_50F6_0000' in s.get('publics', {}) for s in sections.values())
            or any(sections['Name']['publics'][n] != sections['Value']['publics'][n] for n in wrong_names)):
        raise ValueError('sound record wrong-name map did not retain the distinct owner and unresolved target')


# Individual source-functional scalar owners; no allocation-order assumptions.
PROVIDER_SPECS['source-owned:ant-movement-words'] = ('ANTMOVE', None, (('_fd_50F6_0496', 2), ('_fd_50F6_04C2', 2), ('_fd_50F6_04C4', 2), ('_fd_50F6_04E2', 2), ('_fd_50F6_07C0', 2), ('_fd_50F6_084E', 2), ('_fd_50F6_08DA', 2), ('_fd_50F6_08E2', 2), ('_fd_50F6_09F0', 2), ('_fd_50F6_0AB6', 2), ('_fd_50F6_0AC6', 2), ('_fd_50F6_0AD6', 2), ('_fd_50F6_0AE8', 2), ('_fd_50F6_0AF8', 2), ('_fd_50F6_104E', 2), ('_fd_50F6_1058', 2)), 'int far fd_50F6_0496; int far fd_50F6_04C2; int far fd_50F6_04C4; int far fd_50F6_04E2; int far fd_50F6_07C0; int far fd_50F6_084E; int far fd_50F6_08DA; int far fd_50F6_08E2; int far fd_50F6_09F0; int far fd_50F6_0AB6; int far fd_50F6_0AC6; int far fd_50F6_0AD6; int far fd_50F6_0AE8; int far fd_50F6_0AF8; int far fd_50F6_104E; int far fd_50F6_1058;')
FAR_PROVIDER_MODULES.add('source-owned:ant-movement-words')
V21_STORAGE_ANCHORS.update({'_fd_50F6_0496': [1174, ['fd_50F6_0496']], '_fd_50F6_04C2': [1218, ['fd_50F6_04C2']], '_fd_50F6_04C4': [1220, ['fd_50F6_04C4']], '_fd_50F6_04E2': [1250, ['fd_50F6_04E2']], '_fd_50F6_07C0': [1984, ['fd_50F6_07C0']], '_fd_50F6_084E': [2126, ['fd_50F6_084E']], '_fd_50F6_08DA': [2266, ['fd_50F6_08DA']], '_fd_50F6_08E2': [2274, ['fd_50F6_08E2']], '_fd_50F6_09F0': [2544, ['fd_50F6_09F0']], '_fd_50F6_0AB6': [2742, ['fd_50F6_0AB6']], '_fd_50F6_0AC6': [2758, ['fd_50F6_0AC6']], '_fd_50F6_0AD6': [2774, ['fd_50F6_0AD6']], '_fd_50F6_0AE8': [2792, ['fd_50F6_0AE8']], '_fd_50F6_0AF8': [2808, ['fd_50F6_0AF8']], '_fd_50F6_104E': [4174, ['fd_50F6_104E']], '_fd_50F6_1058': [4184, ['fd_50F6_1058']]})
PROVIDER_SPECS['source-owned:world-output-state'] = ('WORLDOUT', None, (('_fd_50F6_0200', 2), ('_fd_50F6_020E', 2), ('_fd_50F6_0224', 2), ('_fd_50F6_0242', 2), ('_fd_50F6_035E', 2), ('_fd_50F6_036C', 2), ('_fd_50F6_0472', 4), ('_fd_50F6_09FA', 2), ('_fd_50F6_0A00', 2), ('_fd_50F6_1040', 2), ('_fd_50F6_1068', 4), ('_fd_50F6_1082', 4), ('_fd_50F6_108E', 4), ('_fd_50F6_10A2', 4), ('_fd_50F6_10B2', 2), ('_fd_50F6_10C0', 2)), 'int far fd_50F6_0200; int far fd_50F6_020E; int far fd_50F6_0224; int far fd_50F6_0242; int far fd_50F6_035E; int far fd_50F6_036C; typedef union { long signed_view; unsigned long unsigned_view; } FAR_LONG_VIEWS; FAR_LONG_VIEWS far fd_50F6_0472; int far fd_50F6_09FA; int far fd_50F6_0A00; int far fd_50F6_1040; long far fd_50F6_1068; long far fd_50F6_1082; long far fd_50F6_108E; long far fd_50F6_10A2; int far fd_50F6_10B2; int far fd_50F6_10C0;')
FAR_PROVIDER_MODULES.add('source-owned:world-output-state')
V21_STORAGE_ANCHORS.update({'_fd_50F6_0200': [512, ['fd_50F6_0200']], '_fd_50F6_020E': [526, ['fd_50F6_020E']], '_fd_50F6_0224': [548, ['fd_50F6_0224']], '_fd_50F6_0242': [578, ['fd_50F6_0242']], '_fd_50F6_035E': [862, ['fd_50F6_035E']], '_fd_50F6_036C': [876, ['fd_50F6_036C']], '_fd_50F6_0472': [1138, ['fd_50F6_0472']], '_fd_50F6_09FA': [2554, ['fd_50F6_09FA']], '_fd_50F6_0A00': [2560, ['fd_50F6_0A00']], '_fd_50F6_1040': [4160, ['fd_50F6_1040']], '_fd_50F6_1068': [4200, ['fd_50F6_1068']], '_fd_50F6_1082': [4226, ['fd_50F6_1082']], '_fd_50F6_108E': [4238, ['fd_50F6_108E']], '_fd_50F6_10A2': [4258, ['fd_50F6_10A2']], '_fd_50F6_10B2': [4274, ['fd_50F6_10B2']], '_fd_50F6_10C0': [4288, ['fd_50F6_10C0']]})
PROVIDER_SPECS['source-owned:history-scalar-state'] = ('HISTOTAL', None, (('_fd_50F6_04F4', 2), ('_fd_50F6_0A90', 2), ('_fd_50F6_0A9E', 2), ('_fd_50F6_0AC4', 2), ('_fd_50F6_0AC8', 2), ('_fd_50F6_0ADA', 4), ('_fd_50F6_0EFC', 4), ('_fd_50F6_0F30', 4), ('_fd_50F6_0F3E', 4), ('_fd_50F6_0FBC', 4), ('_fd_50F6_0FC2', 4), ('_fd_50F6_1000', 4)), 'int far fd_50F6_04F4; int far fd_50F6_0A90; int far fd_50F6_0A9E; int far fd_50F6_0AC4; int far fd_50F6_0AC8; long far fd_50F6_0ADA; long far fd_50F6_0EFC; long far fd_50F6_0F30; long far fd_50F6_0F3E; long far fd_50F6_0FBC; long far fd_50F6_0FC2; long far fd_50F6_1000;')
FAR_PROVIDER_MODULES.add('source-owned:history-scalar-state')
V21_STORAGE_ANCHORS.update({'_fd_50F6_04F4': [1268, ['fd_50F6_04F4']], '_fd_50F6_0A90': [2704, ['fd_50F6_0A90']], '_fd_50F6_0A9E': [2718, ['fd_50F6_0A9E']], '_fd_50F6_0AC4': [2756, ['fd_50F6_0AC4']], '_fd_50F6_0AC8': [2760, ['fd_50F6_0AC8']], '_fd_50F6_0ADA': [2778, ['fd_50F6_0ADA']], '_fd_50F6_0EFC': [3836, ['fd_50F6_0EFC']], '_fd_50F6_0F30': [3888, ['fd_50F6_0F30']], '_fd_50F6_0F3E': [3902, ['fd_50F6_0F3E']], '_fd_50F6_0FBC': [4028, ['fd_50F6_0FBC']], '_fd_50F6_0FC2': [4034, ['fd_50F6_0FC2']], '_fd_50F6_1000': [4096, ['fd_50F6_1000']]})
V21_SCALAR_CONTRACTS = {'source-owned:ant-movement-words': ('ant_movement_words_contract', {'typed_raw_save_positive': 'PASS_TYPED16_SAVE_RAW16_ZERO_STARTUP', 'wrong_width_long_owner': 'WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED', 'wrong_signedness_unsigned_view': 'WRONG_UNSIGNED_VIEW_DETECTED', 'initialized_nonzero_owner': 'INITIALIZED_NONZERO_OWNER_DETECTED', 'shifted_save_rec_base': 'SHIFTED_SAVEREC_BASE_DETECTED', 'short_extent_overrun_runtime': 'OVERFLOW_RUNTIME_PASS_SHORT_OWNER_REJECTED_BY_OMF'}), 'source-owned:world-output-state': ('world_output_state_contract', {'typed_raw_saverec_zero_crt': 'PASS_TYPED_RAW_SAVEREC_ZERO_CRT', 'wrong_unsigned_long_consumer': 'WRONG_UNSIGNED_VIEW_DETECTED', 'initialized_nonzero_owner': 'INITIALIZED_NONZERO_OWNER_DETECTED', 'shifted_saverec_base': 'SHIFTED_SAVEREC_BASE_DETECTED'}), 'source-owned:history-scalar-state': ('history_scalar_state_contract', {'typed_positive': 'PASS_TYPED_SIGNED_STARTUP', 'raw_saverec_positive': 'PASS_RAW_SAVEREC_SIGNED', 'width_short_long': 'WIDTH_LAYOUT_CONTRAST_DETECTED', 'width_wide_int': 'WIDTH_LAYOUT_CONTRAST_DETECTED', 'unsigned_contrast': 'UNSIGNED_SIGN_CONTRAST_DETECTED', 'initializer_contrast': 'NONZERO_INITIALIZER_DETECTED', 'shifted_saverec_contrast': 'SHIFTED_SAVEREC_BASE_DETECTED'})}

def _v21_scalar_case_layout(module, groups=(), extra_publics=(), literal_aliases=()):
    names = [c['name'].lower() for c in provider_communals(module)]
    aliases = [(prefix+str(i), names[target], deltas.get(i, 0))
               for prefix, targets, deltas in groups for i,target in enumerate(targets)]
    aliases += [(alias,names[target],delta) for alias,target,delta in literal_aliases]
    return {'required_publics': sorted(names + list(extra_publics) + [a for a,_,_ in aliases]),
            'aliases': sorted(aliases)}

V21_SCALAR_CASE_LAYOUTS = {}
V21_SCALAR_CASE_LAYOUTS['source-owned:ant-movement-words'] = {
    'typed_raw_save_positive': _v21_scalar_case_layout('source-owned:ant-movement-words', [('_probeexact', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), {})], ('_probesaverows',), ()),
    'wrong_width_long_owner': _v21_scalar_case_layout('source-owned:ant-movement-words', [('_probeupper', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2, 13: 2, 14: 2, 15: 2}), ('_probewhole', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), {})], (), ()),
    'wrong_signedness_unsigned_view': _v21_scalar_case_layout('source-owned:ant-movement-words', [], (), ()),
    'initialized_nonzero_owner': _v21_scalar_case_layout('source-owned:ant-movement-words', [], (), ()),
    'shifted_save_rec_base': _v21_scalar_case_layout('source-owned:ant-movement-words', [], ('_probesaverows',), ()),
    'short_extent_overrun_runtime': _v21_scalar_case_layout('source-owned:ant-movement-words', [], (), ()),
}
V21_SCALAR_CASE_LAYOUTS['source-owned:world-output-state'] = {
    'typed_raw_saverec_zero_crt': _v21_scalar_case_layout('source-owned:world-output-state', [('_probee', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), {}), ('_probes', (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15), {})], (), ()),
    'wrong_unsigned_long_consumer': _v21_scalar_case_layout('source-owned:world-output-state', [], (), (('_probesign', 10, 0),)),
    'initialized_nonzero_owner': _v21_scalar_case_layout('source-owned:world-output-state', [('_probee', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), {})], (), ()),
    'shifted_saverec_base': _v21_scalar_case_layout('source-owned:world-output-state', [('_probee', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), {}), ('_probes', (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15), {0: 2})], (), ()),
}
V21_SCALAR_CASE_LAYOUTS['source-owned:history-scalar-state'] = {
    'typed_positive': _v21_scalar_case_layout('source-owned:history-scalar-state', [('_probetyped', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), {})], (), ()),
    'raw_saverec_positive': _v21_scalar_case_layout('source-owned:history-scalar-state', [('_probesave', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), {})], (), ()),
    'width_short_long': _v21_scalar_case_layout('source-owned:history-scalar-state', [], (), ()),
    'width_wide_int': _v21_scalar_case_layout('source-owned:history-scalar-state', [], (), ()),
    'unsigned_contrast': _v21_scalar_case_layout('source-owned:history-scalar-state', [], (), ()),
    'initializer_contrast': _v21_scalar_case_layout('source-owned:history-scalar-state', [], (), ()),
    'shifted_saverec_contrast': _v21_scalar_case_layout('source-owned:history-scalar-state', [('_probeshift', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), {0: 2})], (), ()),
}

def _v21_scalar_compiler_shapes(module, wide_names, short_widths, initialized_names,
                                 initialized_segment, unsigned=False, save_fixups=False):
    owner = provider_communals(module)
    result = {'owner': owner,
              'wide': [dict(c, count=4, length=4) if c['name'] in wide_names else c for c in owner],
              'short': [dict(c, count=short_widths[c['name']], length=short_widths[c['name']])
                        if c['name'] in short_widths else c for c in owner],
              'initialized': [c for c in owner if c['name'] not in initialized_names],
              'initialized_publics': sorted(initialized_names),
              'initialized_segments': [dict(name=initialized_segment, kind='FAR_DATA',
                  length=sum(c['length'] for c in owner if c['name'] in initialized_names))]}
    if unsigned: result['unsigned'] = owner
    if save_fixups: result['save_rec_pointer_fixups'] = True
    return result

V21_SCALAR_SHAPES = {}
V21_SCALAR_SHAPES['source-owned:ant-movement-words'] = _v21_scalar_compiler_shapes(
    'source-owned:ant-movement-words', ('_fd_50F6_0496', '_fd_50F6_04C2', '_fd_50F6_04C4', '_fd_50F6_04E2', '_fd_50F6_07C0', '_fd_50F6_084E', '_fd_50F6_08DA', '_fd_50F6_08E2', '_fd_50F6_09F0', '_fd_50F6_0AB6', '_fd_50F6_0AC6', '_fd_50F6_0AD6', '_fd_50F6_0AE8', '_fd_50F6_0AF8', '_fd_50F6_104E', '_fd_50F6_1058'), {'_fd_50F6_0496': 1},
    ('_fd_50F6_0496', '_fd_50F6_04C2', '_fd_50F6_04C4', '_fd_50F6_04E2', '_fd_50F6_07C0', '_fd_50F6_084E', '_fd_50F6_08DA', '_fd_50F6_08E2', '_fd_50F6_09F0', '_fd_50F6_0AB6', '_fd_50F6_0AC6', '_fd_50F6_0AD6', '_fd_50F6_0AE8', '_fd_50F6_0AF8', '_fd_50F6_104E', '_fd_50F6_1058'), 'ANTMINI7_DATA', unsigned=False, save_fixups=True)
V21_SCALAR_SHAPES['source-owned:world-output-state'] = _v21_scalar_compiler_shapes(
    'source-owned:world-output-state', ('_fd_50F6_0200',), {'_fd_50F6_1068': 2},
    ('_fd_50F6_0200',), 'INITOWN7_DATA', unsigned=True, save_fixups=False)
V21_SCALAR_SHAPES['source-owned:history-scalar-state'] = _v21_scalar_compiler_shapes(
    'source-owned:history-scalar-state', ('_fd_50F6_04F4',), {'_fd_50F6_0ADA': 2},
    ('_fd_50F6_04F4',), 'HISTINIT5_DATA', unsigned=False, save_fixups=False)
V21_STORAGE_CONTRACTS.update(V21_SCALAR_CONTRACTS)

def _require_v21_scalar_controls(report, profile):
    for module, (key, _) in V21_SCALAR_CONTRACTS.items():
        if not any(r['module'] == module for r in report['translation_units']):
            continue
        contract = report.get(key, {})
        expected = provider_communals(module)
        shapes = V21_SCALAR_SHAPES[module]
        controls = contract.get('compiler_controls', {})
        if (set(controls) != set(shapes)
                or any(controls.get(name) != value for name, value in shapes.items()
                       if name != 'save_rec_pointer_fixups')):
            raise ValueError('v21 scalar owner lacks measured type/width/initializer contrasts')
        if 'save_rec_pointer_fixups' in shapes:
            fixups = controls.get('save_rec_pointer_fixups', {})
            for key, addend, segment in [('positive_rows', 0, 'ANTPOS7_DATA'),
                                         ('shifted_rows', 1, 'ANTSHFT7_DATA')]:
                wanted = [dict(segment=segment, field_offset=4+8*i, target=c['name'],
                               fixup_displacement=0, raw_offset_addend=addend)
                          for i,c in enumerate(expected)]
                if fixups.get(key) != wanted:
                    raise ValueError('v21 movement SaveRec pointer fixup/addend matrix changed')
            if (fixups.get('positive_expected_raw_offset_addend') != 0
                    or fixups.get('shifted_expected_raw_offset_addend') != 1
                    or fixups.get('fixup_displacement_for_both') != 0):
                raise ValueError('v21 movement SaveRec pointer contrast changed')
        for case in contract['cases']:
            if case['linker'] != profile:
                continue
            spec = V21_SCALAR_CASE_LAYOUTS[module][case['case']]
            matrix = case.get('public_address_matrix', {})
            relations = case.get('reviewed_alias_relations', [])
            marker = V21_SCALAR_CONTRACTS[module][1][case['case']]
            if (case.get('runner_returncode') != 0 or case.get('exe_created') is not True
                    or case.get('actual_marker_verbatim') != marker+'\r\n'
                    or case.get('actual_marker_bytes_hex') != (marker+'\r\n').encode().hex()
                    or case.get('all_required_publics_in_both_sections') is not True
                    or case.get('required_publics') != spec['required_publics']
                    or set(matrix) != {'Name','Value'}
                    or any(sorted(rows) != spec['required_publics'] for rows in matrix.values())
                    or matrix.get('Name') != matrix.get('Value')
                    or len(relations) != len(spec['aliases'])
                    or sorted((r.get('alias'),r.get('target'),r.get('delta')) for r in relations)
                       != [tuple(r) for r in spec['aliases']]):
                raise ValueError('v21 scalar owner lacks complete raw output/public/alias matrices')
            try:
                addresses = {n:tuple(int(x,16) for x in a.split(':'))
                             for n,a in matrix['Name'].items()}
                if any(len(a)!=2 or any(v<0 or v>0xffff for v in a) for a in addresses.values()):
                    raise ValueError()
            except (ValueError, AttributeError):
                raise ValueError('v21 scalar public address is invalid')
            for relation in relations:
                alias,target=relation['alias'],relation['target']
                a,t=addresses[alias],addresses[target]
                if (relation.get('passed') is not True or a[0]!=t[0] or a[1]!=t[1]+relation['delta']
                        or relation.get('name_alias')!=matrix['Name'][alias]
                        or relation.get('value_alias')!=matrix['Value'][alias]
                        or relation.get('name_target')!=matrix['Name'][target]
                        or relation.get('value_target')!=matrix['Value'][target]):
                    raise ValueError('v21 scalar alias displacement/address disagrees')


# Source-derived CountAnts histogram; no historical placement claim.
PROVIDER_SPECS['source-owned:ant-class-histogram'] = ('ANTCOUNT', None,
    (('_fd_50F6_0EB6', 64),), 'int far fd_50F6_0EB6[32];')
FAR_PROVIDER_MODULES.add('source-owned:ant-class-histogram')
FAR_PROVIDER_WORD_ARRAYS['source-owned:ant-class-histogram'] = {'_fd_50F6_0EB6'}
V22_STORAGE_ANCHORS = {'_fd_50F6_0EB6': (0x0EB6, ('fd_50F6_0EB6',))}
V22_STORAGE_CONTRACTS = {'source-owned:ant-class-histogram': ('ant_class_histogram_contract', {
    'positive_crt_zero_all_32_signed_words_raw_bytes': 'PASS',
    'wrong_test_base_plus_one_word': 'REJECTED_BASE',
    'wrong_initialized_data_owner': 'REJECTED_CRT_ZERO',
    'wrong_unsigned_consumer_view': 'REJECTED_UNSIGNED_VIEW'})}

def _communal(name: str, count: int, element_size: int) -> dict:
    return {"count": count, "element_size": element_size, "kind": "far",
            "length": count * element_size, "name": name, "type_index": 0}


def _segments(text_name: str, text_size: int, data_size: int,
              const_size: int, far_data: tuple[str, int] | None = None) -> list[dict]:
    rows = [(text_name, "CODE", text_size, "word"), ("_DATA", "DATA", data_size, "word"),
            ("CONST", "CONST", const_size, "word"), ("_BSS", "BSS", 0, "word")]
    if far_data:
        rows.append((far_data[0], "FAR_DATA", far_data[1], "paragraph"))
    return [{"alignment": a, "big": False, "class": c, "combine": "public",
             "index": i, "length": n, "name": s}
            for i, (s, c, n, a) in enumerate(rows, 1)]


def _fixture(declaration, communals, publics, segments):
    return {"declaration": declaration, "actual_communals": communals,
            "actual_publics": publics, "actual_segments": segments}


# OMF summary literals only. Deliberately omit each fixture's ignored OBJ/EXE
# artifact pin; production build admission must not need historical binaries.
HIST_OMF_FIXTURES = {
    "BYTE": _fixture("unsigned char far fd_50F6_0EB6[64];",
        [_communal("_fd_50F6_0EB6", 64, 1)], [], _segments("BYTE_TEXT", 0, 0, 0)),
    "CRTGOOD": _fixture(None, [], [{"name": "_main", "offset": 0, "segment": "CRTGOOD_TEXT"}],
        _segments("CRTGOOD_TEXT", 249, 95, 2)),
    "CRTSIGNED": _fixture(None, [], [{"name": "_main", "offset": 0, "segment": "CRTSIGN_TEXT"}],
        _segments("CRTSIGN_TEXT", 51, 60, 2)),
    "INITIALIZED": _fixture("int far fd_50F6_0EB6[32] = { 0x1357 };", [],
        [{"name": "_fd_50F6_0EB6", "offset": 0, "segment": "INIT5_DATA"}],
        _segments("INIT_TEXT", 0, 0, 0, ("INIT5_DATA", 64))),
    "OWNER": _fixture("int far fd_50F6_0EB6[32];",
        [_communal("_fd_50F6_0EB6", 32, 2)], [], _segments("OWNER_TEXT", 0, 0, 0)),
    "SHORT": _fixture("int far fd_50F6_0EB6[31];",
        [_communal("_fd_50F6_0EB6", 31, 2)], [], _segments("SHORT_TEXT", 0, 0, 0)),
    "UNSIGNED": _fixture("unsigned int far fd_50F6_0EB6[32];",
        [_communal("_fd_50F6_0EB6", 32, 2)], [], _segments("UNSIGNED_TEXT", 0, 0, 0)),
}
def require_v22_storage_contracts(report, profile, tool):
    """Check reviewed evidence metadata; ignored probe binaries are not build inputs."""
    _require_reviewed_storage_contracts(report, profile, tool, V22_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V22_STORAGE_CONTRACTS)
    module = 'source-owned:ant-class-histogram'
    if not any(r['module'] == module for r in report['translation_units']):
        return
    contract = report['ant_class_histogram_contract']
    fixtures = contract.get('compiler_controls', {}).get('fixtures', {})
    if set(fixtures) != set(HIST_OMF_FIXTURES) or contract.get('save_rec_pointer_fixups') != []:
        raise ValueError('histogram compiler control or source-escape matrix changed')
    for name, wanted in HIST_OMF_FIXTURES.items():
        if {k: fixtures[name].get(k) for k in wanted} != wanted:
            raise ValueError('histogram measured compiler shape changed')
    if fixtures['INITIALIZED'].get('initialized_segments_hex') != {'INIT5_DATA': '5713' + '00'*62}:
        raise ValueError('histogram initializer contrast changed')
    required = V22_STORAGE_CONTRACTS[module][1]
    rows = contract['cases']
    pairs = [(r.get('linker'), r.get('case')) for r in rows]
    if (len(pairs) != 8 or set(pairs) != {(p, c) for p in ('rtlink400', 'rtlink610') for c in required}):
        raise ValueError('histogram complete linker/case matrix changed')
    names = {'_fd_50f6_0eb6', '_histogramprobealias'}
    for row in rows:
        if row['linker'] != profile:
            continue
        raw = (required[row['case']] + '\r\n').encode('ascii')
        digest = hashlib.sha256(raw).hexdigest()
        if (row.get('runner_returncode') != 0 or row.get('timed_out') is not False
                or row.get('all_required_publics_in_both_sections') is not True
                or row.get('save_rec_pointer_fixups') != []
                or any(row.get(k) != raw.decode('ascii') for k in ('expected_marker_verbatim', 'actual_marker_verbatim'))
                or any(row.get(k) != raw.hex() for k in ('expected_marker_bytes_hex', 'actual_marker_bytes_hex'))
                or any(row.get(k) != digest for k in ('expected_marker_sha256', 'actual_marker_sha256'))
                or row.get('run_log_pin', {}).get('sha256') != digest
                or row.get('run_log_pin', {}).get('size') != len(raw)):
            raise ValueError('histogram lacks complete raw execution evidence')
        sections = row.get('map_public_sections', {})
        matrix = row.get('public_address_matrix', {})
        if (set(sections) != {'Name', 'Value'} or set(matrix) != {'Name', 'Value'}
                or any(s.get('heading_present') is not True or s.get('missing_required_publics') != []
                       for s in sections.values())
                or any(set(m) != names for m in matrix.values()) or matrix['Name'] != matrix['Value']):
            raise ValueError('histogram lacks both complete public address matrices')
        delta = 2 if row['case'] == 'wrong_test_base_plus_one_word' else 0
        relations = row.get('alias_map_relations', [])
        if len(relations) != 2 or {r.get('section') for r in relations} != {'Name', 'Value'}:
            raise ValueError('histogram alias relations missing or duplicated')
        for relation in relations:
            public = matrix[relation['section']]
            target = public['_fd_50f6_0eb6']; alias = public['_histogramprobealias']
            try:
                tseg, toff = (int(n, 16) for n in target.split(':'))
                aseg, aoff = (int(n, 16) for n in alias.split(':'))
            except (ValueError, AttributeError):
                raise ValueError('histogram public address malformed')
            if (tseg != aseg or aoff != toff + delta
                    or relation.get('alias') != '_histogramprobealias'
                    or relation.get('target') != '_fd_50f6_0eb6'
                    or relation.get('expected_offset_delta') != delta
                    or relation.get('observed_offset_delta') != delta
                    or relation.get('alias_address') != alias or relation.get('target_address') != target
                    or relation.get('same_segment') is not True or relation.get('passed') is not True):
                raise ValueError('histogram measured alias geometry changed')


# The event records are independently declared objects; neither map adjacency nor
# the historical numeric distance supplies their extents.
PROVIDER_SPECS['source-owned:event-records'] = ('EVRECS', None,
    (('_fd_50F6_49FA', 16), ('_fd_50F6_4A0A', 16)),
    'struct Event { int what; int message; int x4; int modifiers; int h; int v; int code; int xE; }; '
    'struct Event far fd_50F6_49FA; struct Event far fd_50F6_4A0A;')
FAR_PROVIDER_MODULES.add('source-owned:event-records')
V23_STORAGE_ANCHORS = {
    '_fd_50F6_49FA': (0x49FA, ('fd_50F6_49FA',)),
    '_fd_50F6_4A0A': (0x4A0A, ('fd_50F6_4A0A',))}
V23_STORAGE_CONTRACTS = {'source-owned:event-records': ('event_records_contract', {
    'positive': 'PASS', 'positive_shifted': 'PASS',
    'wrong_wide_field': 'REJECTED: wide code moved xE to +16; Event size is 18\nPROGRAM_NONZERO',
    'wrong_narrow_field': 'REJECTED: narrow xE stays +14; packed Event size is 15\nPROGRAM_NONZERO',
    'nonzero_initializer': 'REJECTED: nonzero initialized Event at CRT entry\nPROGRAM_NONZERO',
    'base_plus_two': 'REJECTED: symbolic base mismatch\nPROGRAM_NONZERO',
    'wrong_symbol_base': 'REJECTED: symbolic base mismatch\nPROGRAM_NONZERO'})}


def _event_public_address(address):
    try:
        parts = tuple(int(v, 16) for v in address.split(':'))
        if len(parts) != 2 or any(v < 0 or v > 0xffff for v in parts):
            raise ValueError()
        return parts
    except (AttributeError, ValueError):
        raise ValueError('event storage public address malformed')


def require_v23_storage_contracts(report, profile, tool):
    """Check source ABI, full outputs, per-object OMF and symbolic pointer controls.

    Stored measurements are metadata, never ignored OBJ/EXE build inputs. The
    current provider is independently compiled and checked by verify_provider.
    """
    _require_reviewed_storage_contracts(report, profile, tool, V23_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V23_STORAGE_CONTRACTS)
    module = 'source-owned:event-records'
    if not any(r['module'] == module for r in report['translation_units']):
        return
    contract = report['event_records_contract']
    required = V23_STORAGE_CONTRACTS[module][1]
    names = ['_fd_50F6_49FA', '_fd_50F6_4A0A']
    if (contract.get('source_abi') != {'size': 16,
            'fields': ['what','message','x4','modifiers','h','v','code','xE'],
            'offsets': list(range(0,16,2))}
            or contract.get('event_code_stability_claimed') is not False
            or contract.get('historical_producer_or_placement_claimed') is not False
            or contract.get('save_rec_pointer_fixups') != []):
        raise ValueError('event record ABI or storage scope changed')
    cases = contract['cases']
    if (len(cases) != 14 or {(r['linker'],r['case']) for r in cases}
            != {(p,c) for p in ('rtlink400','rtlink610') for c in required}):
        raise ValueError('event record case matrix incomplete or duplicated')
    for row in cases:
        if row['linker'] != profile:
            continue
        raw = (required[row['case']].replace('\n','\r\n')+'\r\n').encode('ascii')
        log = row.get('runtime_log', {})
        matrix = row.get('public_address_matrix', {})
        sections = row.get('map_sections', {})
        if (row.get('runner_exit') != 0 or row.get('timed_out') is not False
                or log.get('exact_raw_bytes_hex') != raw.hex()
                or log.get('sha256') != hashlib.sha256(raw).hexdigest() or log.get('size') != len(raw)
                or set(matrix) != {'Name','Value'} or set(sections) != {'Name','Value'}
                or matrix['Name'] != matrix['Value']
                or any(set(m) != set(names) for m in matrix.values())
                or any(s.get('heading_present') is not True for s in sections.values())):
            raise ValueError('event record lacks complete raw output and both public matrices')
        addresses = {n: _event_public_address(a) for n,a in matrix['Name'].items()}
        size = {'wrong_wide_field': 18, 'wrong_narrow_field': 15}.get(row['case'],16)
        initialized = row['case'] == 'nonzero_initializer'
        shape = row.get('owner_omf', {})
        expected_commons = [_communal(n,size,1) for n in (names[:1] if initialized else names)]
        expected_publics = [{'name': names[1], 'segment': 'OWNINIT5_DATA', 'offset': 0}] if initialized else []
        expected_segments = {'OWNER_TEXT': 0, '_DATA': 0, 'CONST': 0, '_BSS': 0}
        if row['case'] in ('wrong_wide_field','wrong_narrow_field','nonzero_initializer'):
            basename = {'wrong_wide_field': 'OWNWIDE', 'wrong_narrow_field': 'OWNSHORT',
                        'nonzero_initializer': 'OWNINIT'}[row['case']]
            expected_segments = {basename+'_TEXT': 0, '_DATA': 0, 'CONST': 0, '_BSS': 0}
        if initialized:
            expected_segments['OWNINIT5_DATA'] = 16
        if (shape.get('communals') != expected_commons or shape.get('publics') != expected_publics
                or shape.get('externals') != (names[:1] if initialized else names) or shape.get('linker_fixups') != []
                or shape.get('segment_lengths') != expected_segments
                or shape.get('initialized_segment_hex') != ({'OWNINIT5_DATA': '00'*14+'0100'} if initialized else {})):
            raise ValueError('event record measured width/initializer OMF control changed')
        pointers = row.get('pointer_fixups', [])
        base = row.get('base_initializer_omf', {})
        basename = {'base_plus_two':'BADADD', 'wrong_symbol_base':'BADOTHER'}.get(row['case'],'BASES')
        if (base.get('communals') != []
                or base.get('publics') != [{'name':'_eventBases','segment':basename+'5_DATA','offset':0}]
                or base.get('externals') != (names[1:] if row['case'] == 'wrong_symbol_base' else names)
                or base.get('segment_lengths') != {basename+'_TEXT':0,'_DATA':0,'CONST':0,
                    '_BSS':0,basename+'5_DATA':8}
                or base.get('initialized_segment_hex') != {basename+'5_DATA':
                    ('0200'+'00'*6 if row['case'] == 'base_plus_two' else '00'*8)}):
            raise ValueError('event record pointer initializer shape changed')
        fixups = base.get('linker_fixups', [])
        if len(pointers) != 2 or len(fixups) != 2 or {f.get('offset') for f in fixups} != {0,4}:
            raise ValueError('event record lacks both four-byte initializer slots')
        for slot, pointer in enumerate(pointers):
            target = names[1] if row['case'] == 'wrong_symbol_base' and slot == 0 else names[slot]
            delta = 2 if row['case'] == 'base_plus_two' and slot == 0 else 0
            encoded = delta.to_bytes(2,'little').hex()+'0000'
            fixup = next(f for f in fixups if f['offset'] == 4*slot)
            seg,off = addresses[target]
            resolved = f'{seg:04X}:{off+delta:04X}'
            if (pointer.get('eventBases_far_pointer_slot_offset') != 4*slot
                    or pointer.get('pointer_width_bytes') != 4 or pointer.get('target_kind') != 'external'
                    or pointer.get('target_symbol') != target or pointer.get('encoded_addend_hex') != encoded
                    or pointer.get('resolved_far_pointer') != resolved
                    or any(fixup.get(k) != v for k,v in {'width':4,'loc':'pointer32',
                        'target_kind':'external','target':target,'frame_kind':'target','frame':target,
                        'segment':basename+'5_DATA',
                        'self_relative':False,'displacement':0,'encoded_addend':encoded}.items())):
                raise ValueError('event record symbolic base/target/addend control changed')
    shift = contract.get('positive_layout_shift', {}).get(profile, {})
    if shift.get('pad_communals') != [_communal('_aaEvent16Pad',32,1)]:
        raise ValueError('event layout shift lacks an independent 32-byte common')
    positives = {r['case']: r for r in cases if r['linker'] == profile and r['case'] in ('positive','positive_shifted')}
    for name in names:
        starts = [_event_public_address(positives[c]['public_address_matrix']['Name'][name])
                  for c in ('positive','positive_shifted')]
        if (starts[1][0]*16+starts[1][1]) - (starts[0][0]*16+starts[0][1]) != 32:
            raise ValueError('event records did not both relocate by the measured 32 bytes')


# Complete source-owned pointer, scalar and array views; no address-gap extents.
PROVIDER_SPECS['source-owned:remaining-preparestrings-string-pointers'] = ('STRREST', None, (('_fd_50F6_020A', 4), ('_fd_50F6_0218', 4), ('_fd_50F6_021C', 4), ('_fd_50F6_0234', 4), ('_fd_50F6_023A', 4), ('_fd_50F6_034C', 4), ('_fd_50F6_046C', 4), ('_fd_50F6_106E', 4), ('_fd_50F6_1078', 4), ('_fd_50F6_1086', 4), ('_fd_50F6_1096', 4), ('_fd_50F6_10A8', 4), ('_fd_50F6_10B4', 4)), 'typedef char far * far *StrList; StrList far fd_50F6_020A; StrList far fd_50F6_0218; StrList far fd_50F6_021C; StrList far fd_50F6_0234; StrList far fd_50F6_023A; StrList far fd_50F6_034C; StrList far fd_50F6_046C; StrList far fd_50F6_106E; StrList far fd_50F6_1078; StrList far fd_50F6_1086; StrList far fd_50F6_1096; StrList far fd_50F6_10A8; StrList far fd_50F6_10B4;')
FAR_PROVIDER_MODULES.add('source-owned:remaining-preparestrings-string-pointers')
PROVIDER_SPECS['source-owned:yard-init-state'] = ('YARDISCL', None, (('_fd_50F6_0220', 4), ('_fd_50F6_107E', 4), ('_fd_50F6_109C', 4), ('_fd_50F6_0202', 2), ('_fd_50F6_022C', 2), ('_fd_50F6_023E', 2), ('_fd_50F6_0244', 2), ('_fd_50F6_0246', 2), ('_fd_50F6_0364', 2), ('_fd_50F6_036E', 2), ('_fd_50F6_046A', 2), ('_fd_50F6_0470', 2), ('_fd_50F6_047A', 2), ('_fd_50F6_04BE', 2), ('_fd_50F6_04C6', 2), ('_fd_50F6_04E4', 2), ('_fd_50F6_0506', 2), ('_fd_50F6_0624', 2), ('_fd_50F6_07C2', 2), ('_fd_50F6_105C', 2), ('_fd_50F6_1066', 2), ('_fd_50F6_108C', 2), ('_fd_50F6_10A0', 2), ('_fd_50F6_10B0', 2), ('_fd_50F6_10BC', 2)), 'long far fd_50F6_0220; long far fd_50F6_107E; long far fd_50F6_109C; int far fd_50F6_0202; int far fd_50F6_022C; int far fd_50F6_023E; int far fd_50F6_0244; int far fd_50F6_0246; int far fd_50F6_0364; int far fd_50F6_036E; int far fd_50F6_046A; int far fd_50F6_0470; int far fd_50F6_047A; int far fd_50F6_04BE; int far fd_50F6_04C6; int far fd_50F6_04E4; int far fd_50F6_0506; int far fd_50F6_0624; int far fd_50F6_07C2; int far fd_50F6_105C; int far fd_50F6_1066; int far fd_50F6_108C; int far fd_50F6_10A0; int far fd_50F6_10B0; int far fd_50F6_10BC;')
FAR_PROVIDER_MODULES.add('source-owned:yard-init-state')
PROVIDER_SPECS['source-owned:yard-animation-arrays'] = ('YARDARR', None, (('_fd_50F6_0334', 24), ('_fd_50F6_38CA', 30), ('_fd_50F6_38E8', 34), ('_fd_50F6_390A', 34)), 'int far fd_50F6_0334[12]; int far fd_50F6_38CA[15]; int far fd_50F6_38E8[17]; int far fd_50F6_390A[17];')
FAR_PROVIDER_MODULES.add('source-owned:yard-animation-arrays')
FAR_PROVIDER_WORD_ARRAYS['source-owned:yard-animation-arrays'] = {'_fd_50F6_38CA', '_fd_50F6_0334', '_fd_50F6_38E8', '_fd_50F6_390A'}
V24_STORAGE_ANCHORS = {'_fd_50F6_020A': (522, ('fd_50F6_020A',)), '_fd_50F6_0218': (536, ('fd_50F6_0218',)), '_fd_50F6_021C': (540, ('fd_50F6_021C',)), '_fd_50F6_0234': (564, ('fd_50F6_0234',)), '_fd_50F6_023A': (570, ('fd_50F6_023A',)), '_fd_50F6_034C': (844, ('fd_50F6_034C',)), '_fd_50F6_046C': (1132, ('fd_50F6_046C',)), '_fd_50F6_106E': (4206, ('fd_50F6_106E',)), '_fd_50F6_1078': (4216, ('fd_50F6_1078',)), '_fd_50F6_1086': (4230, ('fd_50F6_1086',)), '_fd_50F6_1096': (4246, ('fd_50F6_1096',)), '_fd_50F6_10A8': (4264, ('fd_50F6_10A8',)), '_fd_50F6_10B4': (4276, ('fd_50F6_10B4',)), '_fd_50F6_0220': (544, ('fd_50F6_0220',)), '_fd_50F6_107E': (4222, ('fd_50F6_107E',)), '_fd_50F6_109C': (4252, ('fd_50F6_109C',)), '_fd_50F6_0202': (514, ('fd_50F6_0202',)), '_fd_50F6_022C': (556, ('fd_50F6_022C',)), '_fd_50F6_023E': (574, ('fd_50F6_023E',)), '_fd_50F6_0244': (580, ('fd_50F6_0244',)), '_fd_50F6_0246': (582, ('fd_50F6_0246',)), '_fd_50F6_0364': (868, ('fd_50F6_0364',)), '_fd_50F6_036E': (878, ('fd_50F6_036E',)), '_fd_50F6_046A': (1130, ('fd_50F6_046A',)), '_fd_50F6_0470': (1136, ('fd_50F6_0470',)), '_fd_50F6_047A': (1146, ('fd_50F6_047A',)), '_fd_50F6_04BE': (1214, ('fd_50F6_04BE',)), '_fd_50F6_04C6': (1222, ('fd_50F6_04C6',)), '_fd_50F6_04E4': (1252, ('fd_50F6_04E4',)), '_fd_50F6_0506': (1286, ('fd_50F6_0506',)), '_fd_50F6_0624': (1572, ('fd_50F6_0624',)), '_fd_50F6_07C2': (1986, ('fd_50F6_07C2',)), '_fd_50F6_105C': (4188, ('fd_50F6_105C',)), '_fd_50F6_1066': (4198, ('fd_50F6_1066',)), '_fd_50F6_108C': (4236, ('fd_50F6_108C',)), '_fd_50F6_10A0': (4256, ('fd_50F6_10A0',)), '_fd_50F6_10B0': (4272, ('fd_50F6_10B0',)), '_fd_50F6_10BC': (4284, ('fd_50F6_10BC',)), '_fd_50F6_0334': (820, ('fd_50F6_0334',)), '_fd_50F6_38CA': (14538, ('fd_50F6_38CA',)), '_fd_50F6_38E8': (14568, ('fd_50F6_38E8',)), '_fd_50F6_390A': (14602, ('fd_50F6_390A',))}
V24_STORAGE_CONTRACTS = {'source-owned:remaining-preparestrings-string-pointers': ('remaining_preparestrings_contract', {'typed_far_pointer_halves_zero_and_write': 'PASS', 'independent_BYTE_pointer_storage_roundtrip': 'PASS', 'initialized_nonzero_owner_typed_zero_contrast': 'FAIL', 'initialized_nonzero_owner_BYTE_zero_contrast': 'FAIL', 'wrong_near_outer_pointer_view': 'FAIL', 'wrong_near_row_pointer_view': 'FAIL', 'wrong_pointer_depth_view': 'FAIL', 'wrong_eight_byte_array_extent_view': 'FAIL', 'wrong_plus2_shifted_base_alias': 'FAIL'}), 'source-owned:yard-init-state': ('yard_init_state_contract', {'typed_raw_startup0': 'PASS', 'unsigned_signedness_contrast': 'FAIL', 'shifted_SaveRec_base': 'FAIL', 'initialized_owner_startup_contrast': 'FAIL'}), 'source-owned:yard-animation-arrays': ('yard_animation_arrays_contract', {'positive_zero_all_elements_raw_grass_SaveRec_reset': 'PASS', 'negative_shifted_grass_base': 'FAIL', 'negative_shifted_rain_base': 'FAIL', 'negative_unsigned_handle_view': 'FAIL', 'negative_initialized_grass_owner': 'FAIL'})}


def require_v24_storage_contracts(report, profile, tool):
    """Require complete typed owners and both independently linked control matrices."""
    import dos_storage_contracts
    _require_reviewed_storage_contracts(report, profile, tool, V24_STORAGE_CONTRACTS)
    _require_clean_owner_maps(report, profile, V24_STORAGE_CONTRACTS)
    modules = {r['module'] for r in report['translation_units']}
    for module, (key, _) in V24_STORAGE_CONTRACTS.items():
        if module not in modules:
            continue
        contract = report[key]
        if (contract.get('admitted') is not True or contract.get('original_game_bytes_used') != 0
                or contract.get('historical_producer_or_placement_claimed') is not False
                or contract.get('game_lifecycle_claimed') is not False):
            raise ValueError('v24 storage contract scope or admission changed')
        dos_storage_contracts.validate(contract,
            dos_storage_contracts.policy(module, provider_communals(module)))

# Reviewed v25 natural storage owners; distinct objects, no historical layout claim.
PROVIDER_SPECS['source-owned:balloon-deadline-timers'] = ('BLNTMR', None, (('_fd_50F6_050C', 4), ('_fd_50F6_059A', 4), ('_fd_50F6_0732', 4), ('_fd_50F6_07C4', 4)), 'long far fd_50F6_050C; long far fd_50F6_059A; long far fd_50F6_0732; long far fd_50F6_07C4;')
FAR_PROVIDER_MODULES.add('source-owned:balloon-deadline-timers')
PROVIDER_SPECS['source-owned:experiment-anchor'] = ('EXPANCH', None, (('_fd_50F6_09FC', 4),), 'int far fd_50F6_09FC[2];')
FAR_PROVIDER_MODULES.add('source-owned:experiment-anchor')
FAR_PROVIDER_WORD_ARRAYS['source-owned:experiment-anchor'] = {'_fd_50F6_09FC'}
PROVIDER_SPECS['source-owned:window-clip-handles'] = ('WCLIPH', None, (('_fd_50F6_3B60', 180),), 'typedef char far * far *Handle; Handle far fd_50F6_3B60[45];')
FAR_PROVIDER_MODULES.add('source-owned:window-clip-handles')
FAR_PROVIDER_RECORD_ARRAYS['source-owned:window-clip-handles'] = {'_fd_50F6_3B60': 4}
PROVIDER_SPECS['source-owned:remaining-history-words'] = ('HISTSC25', None, (('_fd_50F6_0EAC', 2), ('_fd_50F6_0EB4', 2), ('_fd_50F6_0EF6', 2), ('_fd_50F6_0EF8', 2), ('_fd_50F6_0EFA', 2), ('_fd_50F6_0F06', 2), ('_fd_50F6_0F0C', 2), ('_fd_50F6_0F0E', 2), ('_fd_50F6_0F10', 2), ('_fd_50F6_0F12', 2), ('_fd_50F6_0F26', 2), ('_fd_50F6_0F2E', 2), ('_fd_50F6_0F34', 2), ('_fd_50F6_0F36', 2), ('_fd_50F6_0F3C', 2), ('_fd_50F6_0F44', 2), ('_fd_50F6_0F7A', 2), ('_fd_50F6_0FC0', 2)), 'int far fd_50F6_0EAC; int far fd_50F6_0EB4; int far fd_50F6_0EF6; int far fd_50F6_0EF8; int far fd_50F6_0EFA; int far fd_50F6_0F06; int far fd_50F6_0F0C; int far fd_50F6_0F0E; int far fd_50F6_0F10; int far fd_50F6_0F12; int far fd_50F6_0F26; int far fd_50F6_0F2E; int far fd_50F6_0F34; int far fd_50F6_0F36; int far fd_50F6_0F3C; int far fd_50F6_0F44; int far fd_50F6_0F7A; int far fd_50F6_0FC0;')
FAR_PROVIDER_MODULES.add('source-owned:remaining-history-words')
PROVIDER_SPECS['source-owned:mode-population-vectors'] = ('MPVOWNR', None, (('_fd_50F6_0B12', 12), ('_fd_50F6_0C2A', 12), ('_fd_50F6_0D40', 40), ('_fd_50F6_0D72', 40)), 'int far fd_50F6_0B12[6]; int far fd_50F6_0C2A[6]; int far fd_50F6_0D40[20]; int far fd_50F6_0D72[20];')
FAR_PROVIDER_MODULES.add('source-owned:mode-population-vectors')
FAR_PROVIDER_WORD_ARRAYS['source-owned:mode-population-vectors'] = {'_fd_50F6_0B12', '_fd_50F6_0D40', '_fd_50F6_0D72', '_fd_50F6_0C2A'}
PROVIDER_SPECS['source-owned:floor-task-words'] = ('FLRTSK', None, (('_DROPdir', 2), ('_Tindex', 2)), 'int far DROPdir; int far Tindex;')
FAR_PROVIDER_MODULES.add('source-owned:floor-task-words')
PROVIDER_SPECS['source-owned:ui-geometry-state'] = ('UIGEO', None, (('_fd_50F6_10D2', 8), ('_fd_50F6_110C', 8), ('_fd_50F6_1104', 8), ('_fd_50F6_392C', 8)), 'struct Rect { int left; int top; int right; int bottom; }; struct Bitmap { int width; int height; char far *bits; }; struct Rect far fd_50F6_10D2; struct Rect far fd_50F6_110C; struct Rect far fd_50F6_1104; struct Bitmap far fd_50F6_392C;')
FAR_PROVIDER_MODULES.add('source-owned:ui-geometry-state')
PROVIDER_SPECS['source-owned:remaining-world-state'] = ('WRLDSC25', None, (('_fd_50F6_0204', 4), ('_fd_50F6_0208', 2), ('_fd_50F6_0210', 2), ('_fd_50F6_0212', 2), ('_fd_50F6_0214', 4), ('_fd_50F6_0226', 2), ('_fd_50F6_0240', 2), ('_fd_50F6_0332', 2), ('_fd_50F6_037A', 2), ('_fd_50F6_0402', 2), ('_fd_50F6_0476', 2), ('_fd_50F6_047E', 2), ('_fd_50F6_0488', 2), ('_fd_50F6_048E', 2), ('_fd_50F6_0492', 2), ('_fd_50F6_049A', 2), ('_fd_50F6_04A4', 2)), 'long far fd_50F6_0204; int far fd_50F6_0208; int far fd_50F6_0210; int far fd_50F6_0212; long far fd_50F6_0214; int far fd_50F6_0226; int far fd_50F6_0240; int far fd_50F6_0332; int far fd_50F6_037A; int far fd_50F6_0402; int far fd_50F6_0476; int far fd_50F6_047E; int far fd_50F6_0488; int far fd_50F6_048E; int far fd_50F6_0492; int far fd_50F6_049A; int far fd_50F6_04A4;')
FAR_PROVIDER_MODULES.add('source-owned:remaining-world-state')
PROVIDER_SPECS['source-owned:remaining-ant-state'] = ('ANTSCL25', None, (('_fd_50F6_0A02', 4), ('_fd_50F6_0A8A', 4), ('_fd_50F6_0AA2', 4), ('_fd_50F6_0AB2', 4), ('_fd_50F6_0A06', 2), ('_fd_50F6_0A9C', 2), ('_fd_50F6_0AA6', 2), ('_fd_50F6_0ACA', 2), ('_fd_50F6_0AD8', 2), ('_fd_50F6_0AEA', 2), ('_fd_50F6_0B06', 2), ('_fd_50F6_0B08', 2), ('_fd_50F6_0C3A', 2), ('_fd_50F6_0D68', 2), ('_fd_50F6_0D6C', 2), ('_fd_50F6_0D6E', 2), ('_fd_50F6_0D70', 2), ('_fd_50F6_0C26', 4)), 'typedef struct { int x; int y; } Pnt; typedef union { long signed_view; unsigned long unsigned_view; } CountViews; Pnt far fd_50F6_0A02; Pnt far fd_50F6_0A8A; Pnt far fd_50F6_0AA2; Pnt far fd_50F6_0AB2; int far fd_50F6_0A06; int far fd_50F6_0A9C; int far fd_50F6_0AA6; int far fd_50F6_0ACA; int far fd_50F6_0AD8; int far fd_50F6_0AEA; int far fd_50F6_0B06; int far fd_50F6_0B08; int far fd_50F6_0C3A; int far fd_50F6_0D68; int far fd_50F6_0D6C; int far fd_50F6_0D6E; int far fd_50F6_0D70; CountViews far fd_50F6_0C26;')
FAR_PROVIDER_MODULES.add('source-owned:remaining-ant-state')
V25_STORAGE_ANCHORS = {'_fd_50F6_050C': (1292, ('fd_50F6_050C',)), '_fd_50F6_059A': (1434, ('fd_50F6_059A',)), '_fd_50F6_0732': (1842, ('fd_50F6_0732',)), '_fd_50F6_07C4': (1988, ('fd_50F6_07C4',)), '_fd_50F6_09FC': (2556, ('fd_50F6_09FC',)), '_fd_50F6_3B60': (15200, ('fd_50F6_3B60',)), '_fd_50F6_0EAC': (3756, ('fd_50F6_0EAC',)), '_fd_50F6_0EB4': (3764, ('fd_50F6_0EB4',)), '_fd_50F6_0EF6': (3830, ('fd_50F6_0EF6',)), '_fd_50F6_0EF8': (3832, ('fd_50F6_0EF8',)), '_fd_50F6_0EFA': (3834, ('fd_50F6_0EFA',)), '_fd_50F6_0F06': (3846, ('fd_50F6_0F06',)), '_fd_50F6_0F0C': (3852, ('fd_50F6_0F0C',)), '_fd_50F6_0F0E': (3854, ('fd_50F6_0F0E',)), '_fd_50F6_0F10': (3856, ('fd_50F6_0F10',)), '_fd_50F6_0F12': (3858, ('fd_50F6_0F12',)), '_fd_50F6_0F26': (3878, ('fd_50F6_0F26',)), '_fd_50F6_0F2E': (3886, ('fd_50F6_0F2E',)), '_fd_50F6_0F34': (3892, ('fd_50F6_0F34',)), '_fd_50F6_0F36': (3894, ('fd_50F6_0F36',)), '_fd_50F6_0F3C': (3900, ('fd_50F6_0F3C',)), '_fd_50F6_0F44': (3908, ('fd_50F6_0F44',)), '_fd_50F6_0F7A': (3962, ('fd_50F6_0F7A',)), '_fd_50F6_0FC0': (4032, ('fd_50F6_0FC0',)), '_fd_50F6_0B12': (2834, ('fd_50F6_0B12',)), '_fd_50F6_0C2A': (3114, ('fd_50F6_0C2A',)), '_fd_50F6_0D40': (3392, ('fd_50F6_0D40',)), '_fd_50F6_0D72': (3442, ('fd_50F6_0D72',)), '_DROPdir': (3898, ('DROPdir', 'fd_50F6_0F3A')), '_Tindex': (3864, ('Tindex', 'fd_50F6_0F18')), '_fd_50F6_10D2': (4306, ('fd_50F6_10D2',)), '_fd_50F6_110C': (4364, ('fd_50F6_110C',)), '_fd_50F6_1104': (4356, ('fd_50F6_1104',)), '_fd_50F6_392C': (14636, ('fd_50F6_392C',)), '_fd_50F6_0204': (516, ('fd_50F6_0204',)), '_fd_50F6_0208': (520, ('fd_50F6_0208',)), '_fd_50F6_0210': (528, ('fd_50F6_0210',)), '_fd_50F6_0212': (530, ('fd_50F6_0212',)), '_fd_50F6_0214': (532, ('fd_50F6_0214',)), '_fd_50F6_0226': (550, ('fd_50F6_0226',)), '_fd_50F6_0240': (576, ('fd_50F6_0240',)), '_fd_50F6_0332': (818, ('fd_50F6_0332',)), '_fd_50F6_037A': (890, ('fd_50F6_037A',)), '_fd_50F6_0402': (1026, ('fd_50F6_0402',)), '_fd_50F6_0476': (1142, ('fd_50F6_0476',)), '_fd_50F6_047E': (1150, ('fd_50F6_047E',)), '_fd_50F6_0488': (1160, ('fd_50F6_0488',)), '_fd_50F6_048E': (1166, ('fd_50F6_048E',)), '_fd_50F6_0492': (1170, ('fd_50F6_0492',)), '_fd_50F6_049A': (1178, ('fd_50F6_049A',)), '_fd_50F6_04A4': (1188, ('fd_50F6_04A4',)), '_fd_50F6_0A02': (2562, ('fd_50F6_0A02',)), '_fd_50F6_0A8A': (2698, ('fd_50F6_0A8A',)), '_fd_50F6_0AA2': (2722, ('fd_50F6_0AA2',)), '_fd_50F6_0AB2': (2738, ('fd_50F6_0AB2',)), '_fd_50F6_0A06': (2566, ('fd_50F6_0A06',)), '_fd_50F6_0A9C': (2716, ('fd_50F6_0A9C',)), '_fd_50F6_0AA6': (2726, ('fd_50F6_0AA6',)), '_fd_50F6_0ACA': (2762, ('fd_50F6_0ACA',)), '_fd_50F6_0AD8': (2776, ('fd_50F6_0AD8',)), '_fd_50F6_0AEA': (2794, ('fd_50F6_0AEA',)), '_fd_50F6_0B06': (2822, ('fd_50F6_0B06',)), '_fd_50F6_0B08': (2824, ('fd_50F6_0B08',)), '_fd_50F6_0C3A': (3130, ('fd_50F6_0C3A',)), '_fd_50F6_0D68': (3432, ('fd_50F6_0D68',)), '_fd_50F6_0D6C': (3436, ('fd_50F6_0D6C',)), '_fd_50F6_0D6E': (3438, ('fd_50F6_0D6E',)), '_fd_50F6_0D70': (3440, ('fd_50F6_0D70',)), '_fd_50F6_0C26': (3110, ('fd_50F6_0C26',))}
V25_STORAGE_CONTRACTS = {'source-owned:balloon-deadline-timers': ('balloon_deadline_timers_contract', {'startup_zero': 'PASS', 'typed_signed_roundtrip': 'PASS', 'raw_byte_view_roundtrip': 'PASS', 'wrong_width_consumer_view': 'FAIL', 'unsigned_view_sign_contrast': 'FAIL', 'initialized_owner_startup': 'FAIL', 'wrong_shifted_alias': 'FAIL'}), 'source-owned:experiment-anchor': ('experiment_anchor_contract', {'positive_crt_zero_all_slots_typed_and_byte_views': 'PASS', 'wrong_test_base_plus_two_bytes': 'REJECTED_BASE', 'wrong_initialized_data_owner': 'REJECTED_CRT_ZERO', 'wrong_unsigned_consumer_view': 'REJECTED_UNSIGNED_VIEW'}), 'source-owned:window-clip-handles': ('window_clip_handles_contract', {'typed_full_180_and_fmemset': 'PASS_TYPED_45_180_FMEMSET', 'independent_byte_full_180_and_fmemset': 'PASS_BYTE_180_FMEMSET', 'wrong_alias_base_plus_zero_control': 'FAIL_ALIAS_GEOMETRY'}), 'source-owned:remaining-history-words': ('remaining_history_words_contract', {'typed_raw_zero_write_and_known_SaveRec_pointers': 'PASS', 'unsigned_signedness_contrast': 'FAIL', 'deliberate_four_byte_long_control': 'PASS', 'initialized_owner_startup_contrast': 'FAIL', 'plus2_pointer_to_separate_backing': 'PASS'}), 'source-owned:mode-population-vectors': ('mode_population_vectors_contract', {'typed_raw_SaveRec_startup_zero': 'PASS', 'wrong_element_type_same_extent': 'FAIL', 'wrong_SaveRec_base_B12_plus_one_word': 'FAIL', 'wrong_SaveRec_base_C2A_plus_one_word': 'FAIL'}), 'source-owned:floor-task-words': ('floor_task_words_contract', {'typed_raw_positive': 'PASS_TYPED_RAW_ZERO_SIGNED', 'wrong_unsigned_consumer': 'WRONG_UNSIGNED_CONSUMER_DETECTED', 'wrong_width_consumer': 'WRONG_WIDTH_LONG_OWNER_DETECTED', 'initialized_consumer': 'INITIALIZED_NONZERO_OWNER_DETECTED', 'shifted_alias_consumer': 'SHIFTED_ALIAS_SEPARATE_BACKING_DETECTED'}), 'source-owned:ui-geometry-state': ('ui_geometry_state_contract', {'positive': 'PASS', 'unsigned_fields': 'PROGRAM_NONZERO', 'base_plus2': 'PROGRAM_NONZERO', 'nonzero_initializer': 'PROGRAM_NONZERO'}), 'source-owned:remaining-world-state': ('remaining_world_state_contract', {'typed_raw_startup_saverec_pointer32': 'PASS_TYPED_RAW_STARTUP_SAVEREC_POINTER32', 'source_unsigned_long_zero_views': 'PASS_SOURCE_UNSIGNED_LONG_ZERO_VIEWS', 'wrong_unsigned_consumer_of_signed_int': 'WRONG_UNSIGNED_VIEW_DETECTED', 'initialized_nonzero_owner': 'INITIALIZED_NONZERO_OWNER_DETECTED', 'plus2_independent_saverec_backing': 'PLUS2_INDEPENDENT_BACKING_DETECTED'}), 'source-owned:remaining-ant-state': ('remaining_ant_state_contract', {'positive18': 'PASS_18_TYPED_RAW_SIGNED_SAVE_ZERO', 'wide_control': 'WRONG_FOUR_BYTE_SCALAR_OWNER_DETECTED', 'unsigned_control': 'WRONG_UNSIGNED_SCALAR_VIEW_DETECTED', 'initialized_control': 'INITIALIZED_NONZERO_OWNER_DETECTED', 'shift_plus2_control': 'SHIFTED_PLUS_TWO_SAVE_BASE_DETECTED'})}

def require_v25_storage_contracts(report, profile, tool):
    """Both independent links, complete output and natural owner/control geometry."""
    import dos_storage_contracts
    import dos_storage_policies_v25
    _require_reviewed_storage_contracts(report, profile, tool, V25_STORAGE_CONTRACTS)
    modules = {r['module'] for r in report['translation_units']}
    for module, (key, _) in V25_STORAGE_CONTRACTS.items():
        if module not in modules:
            continue
        contract = report[key]
        if (contract.get('admitted') is not True or contract.get('original_game_bytes_used') != 0
                or contract.get('historical_producer_or_placement_claimed') is not False
                or contract.get('game_lifecycle_claimed') is not False):
            raise ValueError('v25 storage contract scope or admission changed')
        dos_storage_contracts.validate(contract,
            dos_storage_policies_v25.policy(module, provider_communals(module)))
