"""Independent policy from typed Rect semantics and the declared controls.

This module never reads a candidate receipt or object. Integer encoding describes
the source-built controls; no historical image or opaque payload is consulted.
"""
from copy import deepcopy
from struct import pack

MODULE = 'source-owned:screen-clip-list'
CASES = {name: ('PASS' if name == 'positive' else 'FAIL') for name in (
    'positive', 'far_data_owner', 'wrong_fields', 'wrong_order', 'partial_sentinel',
    'wide_fields', 'wrong_static_handle', 'wrong_active_pointer',
    'wrong_segment_alias', 'wrong_rect_alias')}
RECT = (0, 0, 349, 639)
END = (-32768,) * 4

def data_control(stem, symbol, fields, segment='_DATA', width=2, fixups=(), external=False):
    lengths = {stem + '_TEXT': 0, '_DATA': 0, 'CONST': 0, '_BSS': 0}
    payload = pack('<' + ('h' if width == 2 else 'l') * len(fields), *fields).hex()
    lengths[segment] = len(payload) // 2
    publics = [dict(name=symbol, segment=segment, offset=0)]
    result = dict(module_name=stem + '.C', owner_names=[symbol],
        owner_communals=[], owner_publics=publics, segment_lengths=lengths,
        initialized_data_hex={segment: payload}, linker_fixups=list(fixups),
        full_communals=True, all_communals=[], full_publics=True, all_publics=publics,
        full_segment_lengths=True, all_segment_lengths=lengths,
        full_initialized_data=True, all_initialized_data_hex={segment: payload},
        no_external_fixups=not external, data_only=not external)
    return result

def pointer_fixup(addend=0):
    return dict(segment='_DATA', offset=0, width=4, loc='pointer32', self_relative=False,
        target_kind='external', target='_g_5A9C', frame_kind='target', frame='_g_5A9C',
        displacement=0, encoded_addend=pack('<HH', addend, 0).hex())

CONTROLS = {
    'positive': data_control('SCPOS', '_g_5A9C', RECT + END),
    'far_data_owner': data_control('SCFAR', '_g_5A9C', RECT + END, 'SCFAR5_DATA'),
    'wrong_fields': data_control('SCFLD', '_g_5A9C', (0, 0, 639, 349) + END),
    'wrong_order': data_control('SCORD', '_g_5A9C', END + RECT),
    'partial_sentinel': data_control('SCSEN', '_g_5A9C', RECT + (0, -32768, 0, 0)),
    'wide_fields': data_control('SCWID', '_g_5A9C', RECT + (32768,) * 4, width=4),
    'static_handle_correct': data_control('HNDOK', '_g_574E', (0, 0),
        fixups=[pointer_fixup()], external=True),
    'static_handle_wrong_target': data_control('HNDWR', '_g_574E', (8, 0),
        fixups=[pointer_fixup(8)], external=True),
    'active_pointer_null': data_control('ACTOK', '_g_5AAC', (0, 0)),
    'active_pointer_wrong_initialization': data_control('ACTWR', '_g_5AAC', (0, 0),
        fixups=[pointer_fixup()], external=True),
}

def policy():
    aliases = {case: [dict(alias='_g_5AAE', target='_g_5AAC',
                    delta=4 if case == 'wrong_segment_alias' else 2),
                dict(alias='_fd_55B3_5AA0', target='_g_5A9C',
                    delta=6 if case == 'wrong_rect_alias' else 4)] for case in CASES}
    return deepcopy(dict(module=MODULE, communals=[], owners=['_g_5A9C', '_g_574E', '_g_5AAC'],
        required_cases=CASES, control_outcomes=CASES, linkers=['rtlink400', 'rtlink610'],
        aliases=aliases, compiler_controls=CONTROLS, save_rec_pointer_fixups=[]))
