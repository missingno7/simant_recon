"""Read-only checkpoint observer loaded by GDB's Python interpreter.

Native addresses/types come from the whole-program DWARF; the comparison
inventory and SaveRec lengths come from canonical source, never ELF/PE layout.
No inferior calls or writes are used.
"""
import gdb
import json
from pathlib import Path
from save_projection import project_save

config = json.loads(Path(CONFIG_PATH).read_text())
out = Path(config['out'])
out.mkdir(parents=True, exist_ok=True)
definitions = {}
current_file = None
for line in gdb.execute('info variables', to_string=True).splitlines():
    if line.startswith('File ') and line.endswith(':'):
        current_file = line[5:-1].replace('\\','/').rsplit('/',1)[-1]
    elif current_file and ':' in line:
        for name in config['symbols']:
            owner = config['symbols'][name].get('owner',name)
            if name == 'g_8BA2': owner = 'seed'
            if owner in line.replace(';',' ').replace('[',' ').replace('(',' ').replace(')',' ').replace('*',' ').split():
                definitions[owner] = current_file

def pointers(t, prefix='', seen=None):
    t = t.strip_typedefs()
    if t.code == gdb.TYPE_CODE_PTR: return [prefix or '<value>']
    if t.code == gdb.TYPE_CODE_ARRAY: return pointers(t.target(), prefix+'[]')
    if t.code in (gdb.TYPE_CODE_STRUCT, gdb.TYPE_CODE_UNION):
        result = []
        for f in t.fields():
            if f.name: result += pointers(f.type, prefix+'.'+f.name)
        return result
    return []

def value(name, filename=None):
    if filename: return gdb.parse_and_eval("'"+filename+"'::"+name)
    if name in definitions:
        return gdb.parse_and_eval("'"+definitions[name]+"'::"+name)
    s = gdb.lookup_global_symbol(name)
    if s is None: s = gdb.lookup_static_symbol(name)
    if s is None: raise ValueError('native symbol missing: '+name)
    return s.value()

def read_symbol(name, spec):
    if spec.get('native_expr'):
        v=gdb.parse_and_eval(spec['native_expr']);n=int(v)&((1<<(8*spec['bytes']))-1)
        return dict(status='OK',bytes=spec['bytes'],data=n.to_bytes(spec['bytes'],'little').hex(),
                    native_expr=spec['native_expr'],normalization=spec['normalize'],native_bytes=int(v.type.sizeof))
    owner = spec.get('owner', name)
    if name == 'g_8BA2': owner = 'seed'
    v = value(owner,spec.get('native_file'))
    size = int(v.type.sizeof)
    ptrs = pointers(v.type)
    row = dict(owner=owner, native_bytes=size, native_type=str(v.type), pointer_fields=ptrs)
    if owner in ('db_handles','fd_50F6_10D0'):
        row.update(status='EXCLUDED_HANDLE',reason='DOS/native file descriptor identities are platform-owned; src/root/m00F8.c and m15F8.c, conversions/pointer_globals.h.')
        return row
    if ptrs:
        row.update(status='EXCLUDED_POINTER', reason='Pointer/handle or callback representation differs; no raw equality claim.')
        return row
    offset = spec.get('offset', 0)
    expected = spec.get('bytes')
    length = expected if offset and expected is not None else size-offset if size else expected
    if length is None: raise ValueError('canonical extent unavailable for incomplete native declaration')
    incomplete_array = size == 0 and v.type.strip_typedefs().code == gdb.TYPE_CODE_ARRAY and expected is not None
    if offset < 0 or length < 0 or (offset+length > size and not incomplete_array):
        row.update(status='UNSUPPORTED_EXTENT', expected_bytes=expected, offset=offset)
        return row
    address = int(v.address) + offset
    row.update(status='OK', bytes=length, data=bytes(gdb.selected_inferior().read_memory(address,length)).hex())
    return row

def snapshot(label,ms):
        symbols = {}
        for name, spec in config['symbols'].items():
            try: symbols[name] = read_symbol(name,spec)
            except Exception as exc: symbols[name] = dict(status='UNAVAILABLE', reason=str(exc))
        table = value('fd_4E4B_0000')
        parts = []
        records = []
        for index, offset, length, elem, name in config['save_schema']:
            rec = table[index]
            actual = int(rec['size'])*int(rec['count'])
            if actual != length: raise ValueError('SaveRec canonical/native shape differs at '+str(index))
            data = bytes(gdb.selected_inferior().read_memory(int(rec['data']),length))
            parts.append(data)
            records.append(dict(record=index,name=name,bytes=length))
        (out/(label+'.raw-save.sav')).write_bytes(b''.join(parts))
        projected, projection, errors = project_save(config['save_schema'],config['symbols'],symbols)
        if projected is not None: (out/(label+'.sav')).write_bytes(projected)
        clocks = {name:int(gdb.parse_and_eval(expr)) for name,expr in
                  [('game_ticks','app.game_clock.tick_count'),('bios_ticks','app.bios_clock.tick_count'),
                   ('outer_loops','fd_50F6_383A')]}
        for key,name in [('cycle','Cycle'),('simulation_calls','fd_50F6_0C26')]:
            item=symbols.get(name,{})
            clocks[key]=int.from_bytes(bytes.fromhex(item['data']),'little') if item.get('status')=='OK' else None
        # Calls into the inferior are deliberately prohibited; virtual_ns is
        # the host service's static clock owner and is read directly instead.
        clocks['virtual_ns'] = int(value('virtual_ns'))
        result = dict(schema='simant-native-checkpoint-v1',milliseconds=ms,
                      clocks=clocks,symbols=symbols,save_records=records,
                      stack=gdb.execute('bt 20',to_string=True),save_projection=projection,save_projection_errors=errors,
                      replay_next=int(gdb.parse_and_eval('app.replay_next')))
        (out/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print('Observed native checkpoint',ms,flush=True)

class Checkpoint(gdb.Breakpoint):
    def stop(self):
        ms = int(gdb.parse_and_eval('milliseconds'))
        snapshot('cp'+str(ms),ms)
        return False

class Failure(gdb.Breakpoint):
    def stop(self):
        if (out/'failure-stack.txt').exists(): return False
        if self.location != 'abort' and int(gdb.parse_and_eval('$rcx')) == 0: return False
        (out/'failure-stack.txt').write_text(gdb.execute('bt 30',to_string=True))
        try: snapshot('failure',int(value('virtual_ns'))//1000000)
        except Exception as exc: print('Failure observer:',exc,flush=True)
        return False

class SimulationBoundary(gdb.Breakpoint):
    def __init__(self):
        super().__init__('*DoAntSim')
        self.hits=0
    def stop(self):
        self.hits+=1
        snapshot('step'+str(self.hits),int(value('virtual_ns'))//1000000)
        if self.hits>=config['step_count']: self.enabled=False
        return False

class DumpState(gdb.Command):
    """native-state LABEL: read-only dump at any stopped inferior location."""
    def __init__(self): super().__init__('native-state',gdb.COMMAND_DATA)
    def invoke(self,arg,from_tty): snapshot(arg.strip() or 'ondemand',int(value('virtual_ns'))//1000000)

def exited(event):
    (out/'exit.json').write_text(json.dumps(dict(exit_code=getattr(event,'exit_code',None))))

gdb.execute('set pagination off')
gdb.execute('set confirm off')
gdb.execute('set print elements 0')
gdb.execute('set breakpoint pending on')
Checkpoint('portable_native_checkpoint')
if config.get('step_count',0): SimulationBoundary()
Failure('exit')
Failure('abort')
Failure('_exit')
Failure('ExitProcess')
DumpState()
gdb.events.exited.connect(exited)
gdb.execute('run')
