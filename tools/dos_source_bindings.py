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
}

FAR_PROVIDER_MODULES = {'source-owned:memory-far-state', 'source-owned:yard-scalars',
                        'source-owned:database-index-state', 'source-owned:spider-counters',
                        'source-owned:lion-sow-pillar'}

# The compiler represents these actual word arrays by element count and width;
# singleton words use its byte-count COMDEF form. Preserve both measured shapes.
FAR_PROVIDER_WORD_ARRAYS = {'source-owned:lion-sow-pillar':
                          {'_PillarMap', '_SowDir', '_SowSave', '_SowX', '_SowY'}}

def provider_communals(module):
    spec = PROVIDER_SPECS.get(module)
    if not spec:
        raise ValueError('unreviewed functional storage provider')
    far = module in FAR_PROVIDER_MODULES
    words = FAR_PROVIDER_WORD_ARRAYS.get(module, set())
    return [{'name': name, 'kind': 'far' if far else 'near', 'length': size,
             **({'count': size // (2 if name in words else 1),
                 'element_size': 2 if name in words else 1} if far else {})} for name, size in spec[2]]


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
            '_SowSave': 0x0F28, '_SowX': 0x0EAE, '_SowY': 0x0F00})
        for name, size in spec[2]:
            anchor = symbols['data'][name[1:]]
            segment = 0x50F6 if provider['module'] in FAR_PROVIDER_MODULES else 0x55B3
            interiors = [(n, s['off'] - anchor['off']) for n, s in symbols['data'].items()
                         if s['seg'] == anchor['seg'] and anchor['off'] < s['off'] < anchor['off'] + size]
            expected_interiors = [('g_5AAE', 2)] if name == '_g_5AAC' else []
            if ((anchor['seg'], anchor['off']) != (segment, addresses[name])
                    or interiors != expected_interiors):
                raise ValueError('functional storage extent conflicts with reviewed registry')


def verify_provider(obj, provider):
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
        ('source-owned:lion-sow-pillar', 'lion_array_storage_contract', 5, 2)])


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
    if frame_checks and [fixup_key(f) for f in original_fixups] != [
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
