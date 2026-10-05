"""Original reclaim/type/free probe for the Ralloc discard-template pointer."""
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.path.insert(0,str(ROOT / 'tools'))
import behavior as b
import exe
import functions
from behavior_suites import memory as m


def original_discard(correct_pointer):
    vm = b.Machine(SimpleNamespace(function=functions.get('f_171C_0BE2'),
        vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors},candidate_entries={}))
    initial = m.heap_case('discard-premise/reclaim',[(8,3,{'age':7}),(32,0x80)],
        handles=[0],args=[0])
    # Explicit template/pointer contrasts, independent of the fixture under test.
    initial.writes += [(m.DISCARD_HEADER_SEG*16,m.header(0,5,size=0,name=b'')),
        (b.symbol_address('fd_50F6_3948'),m.far(0,m.DISCARD_HEADER_SEG if correct_pointer else m.DISCARD_DATA_SEG))]
    reclaim = vm.run(initial)
    slot = m.HANDLE_SEG*16+m.MASTER_FIRST
    pointer = int.from_bytes(vm.read(slot,4),'little')
    header_at = (pointer>>16)*16-32
    looked = vm.run(b.Case(label='discard-premise/type-lookup',
        args=[m.MASTER_FIRST,m.HANDLE_SEG]),preserve=True,
        original_entry=functions.get('f_171C_1686'))
    before = {o:vm.word(m.dga(o)) for o in (0x2F3C,0x2F3E,0x2F42,0x2F44)}
    head_before = int.from_bytes(vm.read(m.dga(0x91AC),4),'little')
    freed = vm.run(b.Case(label='discard-premise/free',args=[m.MASTER_FIRST,m.HANDLE_SEG],
        return_kind='void'),preserve=True,original_entry=functions.get('f_171C_13E4'))
    after = {o:vm.word(m.dga(o)) for o in before}
    head_after = int.from_bytes(vm.read(m.dga(0x91AC),4),'little')
    return {'correct_pointer':correct_pointer,'reclaim_return':reclaim['return'],
        'discarded_master_pointer':pointer,'resolved_header_address':header_at,
        'type_return':looked['return'],'free_equal_counter_fields':{
            hex(o):before[o]==after[o] for o in (0x2F3C,0x2F3E,0x2F42)},
        'live_handles_before':before[0x2F44],'live_handles_after':after[0x2F44],
        'master_slot_cleared':vm.read(slot,4)==bytes(4),
        'free_head_before':head_before,'free_head_after':head_after,
        'nonstack_written_addresses':freed['written_addresses']}


def original_discard_resize():
    vm = b.Machine(SimpleNamespace(function=functions.get('f_171C_125C'),
        vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors},candidate_entries={}))
    initial=m.heap_case('discard-resize/first-public-allocation',[(256,0x80)],
        args=[160,0,3,0,0xB200],result='farptr',extra=[(0xB2000,b'soft-live\0')])
    first=vm.run(initial)['return']
    second=vm.run(b.Case(label='discard-resize/second-public-allocation',
        args=[32,0,3,0,0xB200],return_kind='farptr'),preserve=True)['return']
    for index in range(2):
        reclaimed=vm.run(b.Case(label=f'discard-resize/reclaim-{index}',args=[0]),
            preserve=True,original_entry=functions.get('f_171C_0BE2'))
        assert reclaimed['return']==1
    slot=lambda handle:(handle>>16)*16+(handle&65535)
    pointers_before=[int.from_bytes(vm.read(slot(h),4),'little') for h in (first,second)]
    assert pointers_before==[m.DISCARD_DATA_SEG<<16]*2
    sizes_before = [vm.run(b.Case(label='discard-resize/original-size',
        args=[h&65535,h>>16],return_kind='s32'),preserve=True,
        original_entry=functions.get('f_171C_1C1C'))['return'] for h in (first,second)]
    assert sizes_before == [0,0]
    resized=vm.run(b.Case(label='discard-resize/resize-first-original',
        args=[first&65535,first>>16,100,0,1],return_kind='farptr',
        observe=[b.Range('discard_template',m.DISCARD_HEADER_SEG*16,32)],
        callbacks={'f_171C_0EEA':b.Callback(6)}),preserve=True,
        original_entry=functions.get('f_171C_18A6'))
    assert resized['return']==first
    payload=int.from_bytes(vm.read(slot(first),4),'little')
    header_at=(payload>>16)*16-32
    assert vm.word(header_at)==first&65535
    assert vm.read(header_at+8,1)==b'\x01'
    assert int.from_bytes(vm.read(header_at+2,4),'little')==100
    other_type=vm.run(b.Case(label='discard-resize/other-type',args=[second&65535,second>>16]),
        preserve=True,original_entry=functions.get('f_171C_1686'))['return']
    other_discarded=vm.run(b.Case(label='discard-resize/other-discard-status',args=[second&65535,second>>16]),
        preserve=True,original_entry=functions.get('f_171C_1794'))['return']
    assert other_type==5 and other_discarded==1
    entry_types=[bytes.fromhex(t['state_at_entry']['discard_template'])[8] for t in resized['trace']]
    assert entry_types==[0]
    assert vm.read(m.DISCARD_HEADER_SEG*16+8,1)==b'\x05'
    return {'scope':'actual original allocation/reclaim/18A6 resize over initialized bounded free heap; no native or gameplay reachability claim',
        'first_handle':first,'second_handle':second,'shared_discarded_pointers_before_resize':pointers_before,
        'original_discarded_sizes':sizes_before,
        'resize_size_bytes':100,'resize_type':1,'original_resize_return':resized['return'],
        'resized_payload':payload,'resized_block_handle_word':vm.word(header_at),
        'resized_block_type':vm.read(header_at+8,1)[0],
        'other_handle_type_after':other_type,'other_handle_discard_status_after':other_discarded,
        'template_type_at_actual_0EEA_entry':entry_types[0],'template_type_restored_after':5,
        'public_live_handle_count':vm.word(m.dga(0x2F44))}
