"""Independent literal word-control policy; no candidate evidence is loaded."""
from copy import deepcopy

MODULE = 'source-owned:remaining-far-state-words'
NAMES = ['_fd_50F6_' + suffix for suffix in ('04C0', '0B20', '0F38', '0FB6', '0FFA')]
COMMUNALS = [dict(name=name, kind='far', count=2, element_size=1, length=2) for name in NAMES]
CASES = dict(typed_raw_startup0='PASS', typed_raw_boundary_guard='PASS',
    unsigned_signedness_contrast='FAIL', initialized_owner_startup_contrast='FAIL')

def control(stem, wide=False, initialized=False):
    communals = deepcopy(COMMUNALS)
    publics = []
    data = {}
    lengths = {stem + '_TEXT': 0, '_DATA': 0, 'CONST': 0, '_BSS': 0}
    if wide:
        communals[0].update(count=4, length=4)
    if initialized:
        communals.pop(0)
        segment = stem + '5_DATA'
        lengths[segment] = 2
        data[segment] = '0100'
        publics = [dict(name=NAMES[0], segment=segment, offset=0)]
    return dict(module_name=stem + '.C', owner_names=NAMES,
        owner_communals=communals, owner_publics=publics,
        segment_lengths=lengths, initialized_data_hex=data, linker_fixups=[],
        full_communals=True, all_communals=communals,
        full_publics=True, all_publics=publics,
        full_segment_lengths=True, all_segment_lengths=lengths,
        full_initialized_data=True, all_initialized_data_hex=data,
        data_only=True, no_external_fixups=True)

def policy():
    return dict(module=MODULE, communals=deepcopy(COMMUNALS), owners=NAMES,
        required_cases=CASES, control_outcomes=CASES, linkers=['rtlink400', 'rtlink610'],
        aliases={case: [] for case in CASES}, save_rec_pointer_fixups=[],
        compiler_controls={stem: control(stem, wide=stem == 'WIDV35', initialized=stem == 'INITV35')
            for stem in ('OWNV35', 'WIDV35', 'SIGV35', 'INITV35')})
