"""Read symbolic MASM data declarations; never read original image bytes.

This bounded emitter reads accepted canonical sources. OMF is used only to
resolve explicit OFFSET relocation expressions in the assembler output, never
to infer allocation size or copy storage bytes. Unsupported expressions fail.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'build/portable-sdl3'
sys.path.insert(0, str(ROOT / 'tools'))
import omf


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_args(text):
    result = []; start = 0; depth = 0; quote = None
    for i, c in enumerate(text):
        if quote:
            if c == quote: quote = None
        elif c in "'\"": quote = c
        elif c == '(': depth += 1
        elif c == ')': depth -= 1
        elif c == ',' and depth == 0:
            result.append(text[start:i].strip()); start = i + 1
    result.append(text[start:].strip())
    return result


def expression(text, constants):
    text = re.sub(r'\b([0-9][0-9a-f]*)h\b', lambda m: str(int(m[1], 16)), text, flags=re.I)
    tree = ast.parse(text.strip(), mode='eval').body
    def value(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, int): return node.value
        if isinstance(node, ast.Name) and node.id in constants: return constants[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub): return -value(node.operand)
        if isinstance(node, ast.BinOp):
            left, right = value(node.left), value(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
        raise ValueError('nonconstant expression: ' + text)
    return value(tree)


def initializers(text, width, constants):
    result = []
    for arg in split_args(text):
        dup = re.fullmatch(r'(.+?)\s+dup\s*\((.*)\)', arg, re.I)
        if dup:
            result.extend(initializers(dup[2], width, constants) * expression(dup[1], constants))
        elif len(arg) >= 2 and arg[0] in "'\"" and arg[-1] == arg[0]:
            if width != 1: raise ValueError('wide MASM string requires a reviewed interpretation')
            result.extend(ord(c) for c in arg[1:-1])
        else:
            try: result.append(expression(arg, constants))
            except (ValueError, SyntaxError): result.append({'symbolic_expression': arg})
    return result


def data_facts(path):
    constants = {}; segments = {}; current = None; offset = 0
    lines = path.read_text(encoding='latin1').splitlines(); repeat = None; repeat_lines = []
    def parse(raw, lineno):
        nonlocal current, offset
        text = raw.split(';', 1)[0].strip()
        if not text: return
        declaration = re.fullmatch(r'(\w+)\s+segment\s+.*[\'\"](DATA|FAR_DATA)[\'\"]', text, re.I)
        if declaration:
            current = declaration[1]; offset = 0
            segments[current] = {'labels': {}, 'equ_views': {}, 'directives': []}; return
        if re.fullmatch(r'\w+\s+ends', text, re.I): current = None; return
        definition = re.fullmatch(r'(\w+)\s+(?:equ|=)\s+(.+)', text, re.I)
        if definition:
            try: constants[definition[1]] = expression(definition[2], constants)
            except (ValueError, SyntaxError):
                if current: segments[current]['equ_views'][definition[1]] = {'expression': definition[2], 'line': lineno}
            return
        if not current: return
        label = re.fullmatch(r'(\w+)\s+label\s+(byte|word|dword)', text, re.I)
        if label:
            segments[current]['labels'][label[1]] = {'offset': offset, 'line': lineno, 'label_width': label[2].lower()}; return
        data = re.fullmatch(r'(?:(\w+)\s+)?(db|dw|dd)\s+(.+)', text, re.I)
        if data:
            width = {'db': 1, 'dw': 2, 'dd': 4}[data[2].lower()]
            values = initializers(data[3], width, constants)
            if data[1]: segments[current]['labels'][data[1]] = {'offset': offset, 'line': lineno, 'label_width': data[2].lower()}
            segments[current]['directives'].append({'offset': offset, 'line': lineno, 'width': width, 'values': values, 'source_expression': data[3]})
            offset += width * len(values); return
        if not re.match(r'(?:extrn|public)\b', text, re.I):
            raise ValueError(f'{path}:{lineno}: unsupported data syntax: {text}')
    for lineno, raw in enumerate(lines, 1):
        text = raw.split(';', 1)[0].strip()
        if repeat is not None:
            if text.lower() == 'endm':
                for _ in range(repeat):
                    for original_line, original_raw in repeat_lines: parse(original_raw, original_line)
                repeat = None; repeat_lines = []
            else: repeat_lines.append((lineno, raw))
            continue
        m = re.fullmatch(r'rept\s+(.+)', text, re.I)
        if m and current: repeat = expression(m[1], constants); continue
        parse(raw, lineno)
    if repeat is not None: raise ValueError('unterminated REPT')
    return {'source': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'segments': segments}


def words(facts, segment, name, count=1, width=None):
    data = facts['segments'][segment]
    label = data['labels'][name]
    entries = [d for d in data['directives'] if d['offset'] >= label['offset']]
    if not entries or entries[0]['offset'] != label['offset']: raise ValueError('label does not begin data')
    if width is None: width = entries[0]['width']
    values = []; refs = []; expected = label['offset']
    for row in entries:
        if row['offset'] != expected or row['width'] != width: raise ValueError('mixed or discontiguous source data')
        values.extend(row['values']); refs.append(row['line']); expected += row['width'] * len(row['values'])
        if len(values) >= count: break
    if len(values) < count or any(not isinstance(v, int) for v in values[:count]): raise ValueError('nonconstant or short initializer')
    return values[:count], refs


def emit_mouse(facts):
    # Host spelling is a view choice, while widths/counts/values below must all
    # be justified by actual symbolic ASM declarations, never native owners.
    grouped = {'g_4336': ('int16_t', 4), 'g_53CD': ('uint8_t', 128)}
    selected = ['432A','4331','4332','4333','4334','4336','433E','4340','4342','4344','4346',
                '4348','434A','434E','4352','4356','435A','4362','4363','4364','4365','4366','4368','4369','4DA4','53BC','53BD','53CD']
    result = ['/* Generated only from src/root/m1B73.asm symbolic data directives. */', '#include <stdint.h>', '']
    receipt = []
    for suffix in selected:
        name = 'g_' + suffix; asm = '_' + name
        width = next(d['width'] for d in facts['segments']['_DATA']['directives'] if d['offset'] == facts['segments']['_DATA']['labels'][asm]['offset'])
        ctype, count = grouped.get(name, ({1:'uint8_t', 2:'uint16_t', 4:'uint32_t'}[width], 1))
        values, lines = words(facts, '_DATA', asm, count, width)
        decl = f'{ctype} {name}' + (f'[{count}]' if count > 1 else '')
        init = '{ ' + ', '.join(hex(v) for v in values) + ' }' if count > 1 else hex(values[0])
        result.append(f'{decl} = {init}; /* ASM line {lines[0]} */')
        receipt.append({'name': name, 'type': ctype, 'count': count, 'source_width': width, 'source_lines': lines, 'values': values})
    # These declarations are actual named DB/DW cells inside the ASM CODE
    # segment. Read their symbolic directives without assigning code offsets
    # or copying any instruction bytes.
    source=ROOT/facts['source']
    code_cells={'shift_state':('uint8_t','db'),
                'kbd_hook_on':('uint8_t','db'),
                'tmr_countdown':('uint16_t','dw'),
                'cursor_mode':('uint8_t','db'),
                'kbd_last_scan':('uint8_t','db'),
                'last_shift':('uint8_t','db'),
                'tick_phase':('uint16_t','dw'),
                'mouse_busy':('uint8_t','db'),
                'timer_busy':('uint8_t','db')}
    header=['#ifndef SIMANT_CANONICAL_MOUSE_INPUT_DATA_H',
            '#define SIMANT_CANONICAL_MOUSE_INPUT_DATA_H','#include <stdint.h>',
            'extern uint32_t g_434E;', 'extern uint8_t g_53CD[128];']
    for name,(ctype,directive) in code_cells.items():
        matches=[(n,re.fullmatch(r'\s*'+name+r'\s+(db|dw|dd)\s+(.+?)\s*',line.split(';',1)[0],re.I))
                 for n,line in enumerate(source.read_text(encoding='latin1').splitlines(),1)]
        matches=[(n,m) for n,m in matches if m]
        if len(matches)!=1 or matches[0][1][1].lower()!=directive:
            raise ValueError('canonical code-segment cell shape differs: '+name)
        line,match=matches[0]
        width={'db':1,'dw':2,'dd':4}[directive]
        values=initializers(match[2],width,{})
        if len(values)!=1 or not isinstance(values[0],int):
            raise ValueError('canonical code-segment initializer differs: '+name)
        result.append(f'{ctype} {name} = {hex(values[0])}; /* ASM line {line} */')
        header.append(f'extern {ctype} {name};')
        receipt.append({'name':name,'source':facts['source'],'source_lines':[line],
                        'source_width':width,'count':1,'values':values,
                        'native_type':ctype,'source_segment':'CODE'})
    header.append('#endif')
    (WORK/'canonical_mouse_input_data.h').write_text('\n'.join(header)+'\n')
    (WORK / 'canonical_mouse_data.c').write_text('\n'.join(result) + '\n')
    return receipt


def emit_mouse_queues(facts):
    """Exact SaveUnder and capacity/count/row owners from QUEUE_DATA."""
    save = facts['segments']['_DATA']['labels']['SaveUnder']
    directive = next(d for d in facts['segments']['_DATA']['directives']
                     if d['offset'] == save['offset'])
    if directive['width'] != 1 or len(directive['values']) != 2596 or any(directive['values']):
        raise ValueError('SaveUnder source shape differs')
    segment = facts['segments']['QUEUE_DATA']
    names = ['Queue0', '_fd_5071_0060', '_fd_5071_03C4', '_fd_5071_0728']
    header = ['#ifndef SIMANT_CANONICAL_MOUSE_QUEUE_DATA_H',
              '#define SIMANT_CANONICAL_MOUSE_QUEUE_DATA_H', '#include <stdint.h>',
              'extern uint8_t SaveUnder[2596];']
    definitions = ['/* Actual source SaveUnder label; no copied native values. */',
                   'uint8_t SaveUnder[2596] = {0};']
    receipts = [{'label': 'SaveUnder', 'source_line': directive['line'],
                 'source_width': 1, 'count': len(directive['values']),
                 'initializer': 0, 'native_owner': 'SaveUnder[2596]'}]
    # Source labels address count, with the capacity word immediately before.
    # Row counts below are read from DB extents, not assumed from capacity.
    shapes = []
    for index, name in enumerate(names):
        label = segment['labels'][name]
        at = label['offset']
        capacity = next(d for d in segment['directives'] if d['offset'] == at - 2)
        count = next(d for d in segment['directives'] if d['offset'] == at)
        rows = next(d for d in segment['directives'] if d['offset'] == at + 2)
        if capacity['width'] != 2 or count['width'] != 2 or len(capacity['values']) != 1 or count['values'] != [0]:
            raise ValueError('queue capacity/count words differ')
        if rows['width'] != 1 or len(rows['values']) % 18 or any(rows['values']):
            raise ValueError('queue rows differ from zero 18-byte source entries')
        nrows = len(rows['values']) // 18
        shapes.append(nrows)
        typename = f'CanonicalAsmQueue{nrows}'
        owner = f'canonical_mouse_queue{index}'
        if not any(line.startswith('typedef struct ' + typename) for line in header):
            header.append(f'typedef struct {typename} {{ uint16_t capacity,count; uint8_t records[{nrows}][18]; }} {typename};')
            header.append(f'_Static_assert(sizeof({typename}) == {4 + nrows * 18}, "source queue extent");')
        header.append(f'extern {typename} {owner};')
        definitions.append(f'{typename} {owner} = {{ {capacity["values"][0]}, 0, {{{{0}}}} }};')
        receipts.append({'label': name, 'source_count_offset': at,
                         'source_lines': [capacity['line'], count['line'], rows['line']],
                         'capacity': capacity['values'][0], 'count': 0, 'rows': nrows,
                         'row_bytes': 18, 'native_owner': owner,
                         'label_view': owner + '.count',
                         'provider_borrows': ['&' + owner + '.capacity', '&' + owner + '.count', owner + '.records'],
                         'source_byte_extent': 4 + len(rows['values'])})
    if shapes != [5, 48, 48, 10]:
        raise ValueError('source queue groups differ')
    tail_offset = segment['labels'][names[-1]]['offset'] + 2 + shapes[-1] * 18
    tail = next(d for d in segment['directives'] if d['offset'] == tail_offset)
    if tail['width'] != 2 or tail['values'] != [5]:
        raise ValueError('QUEUE_DATA trailing word differs')
    header.append('extern uint16_t canonical_mouse_queue_trailing_word;')
    definitions.append('uint16_t canonical_mouse_queue_trailing_word = 5;')
    receipts.append({'source_line': tail['line'], 'source_width': 2,
                     'native_owner': 'canonical_mouse_queue_trailing_word', 'value': 5,
                     'view_status': 'Unknown source consumer; retained actual declared cell.'})
    header.extend(['#endif', ''])
    (WORK / 'canonical_mouse_queue_data.h').write_text('\n'.join(header))
    with (WORK / 'canonical_mouse_data.c').open('a') as out:
        out.write('\n#include "canonical_mouse_queue_data.h"\n' + '\n'.join(definitions) + '\n')
    return receipts


def byte_range(facts, segment, name, length):
    """Flatten constants from source directives, not object storage bytes."""
    data = facts['segments'][segment]; start = data['labels'][name]['offset']
    result = []; refs = []; expected = start
    for row in data['directives']:
        if row['offset'] < start: continue
        if row['offset'] != expected: raise ValueError('discontiguous source byte range')
        for value in row['values']:
            if not isinstance(value, int): raise ValueError('symbolic source byte range')
            result.extend((value & ((1 << (8 * row['width'])) - 1)).to_bytes(row['width'], 'little'))
        refs.append(row['line']); expected += row['width'] * len(row['values'])
        if len(result) >= length: return result[:length], refs
    raise ValueError('short source byte range')


def emit_numeric(facts):
    """Emit only numeric cells or proven null pointer initializers.

    Adjacent field groups are explicit reviewed view choices. This scratch C
    file is a recipe; callers must share its point/word/pointer ABI and retire
    all prior native owners of the generated names.
    """
    by_source = {f['source']:f for f in facts}
    result = ['/* Generated from accepted canonical symbolic ASM declarations. */',
              '#include <stdint.h>', '#include <stddef.h>',
              'typedef struct CanonicalAsmPoint { int16_t x, y; } CanonicalAsmPoint;', '']
    receipt = []
    def emit(source, name, ctype, count=1, initializer=None, source_width=None):
        f = by_source[source]; label = '_' + name
        if source_width is None:
            data = f['segments']['_DATA']; offset = data['labels'][label]['offset']
            source_width = next(d['width'] for d in data['directives'] if d['offset'] == offset)
        source_count=2 if initializer=='NULL' and source_width==2 else count
        values, lines = words(f, '_DATA', label, source_count, source_width)
        if initializer=='NULL' and any(values):raise ValueError('native null initializer requires source all-zero pointer bits')
        if initializer is None:
            initializer = '{ ' + ', '.join(hex(v) for v in values) + ' }' if count > 1 else hex(values[0])
        result.append(f'{ctype} {name}' + (f'[{count}]' if count>1 else '') + f' = {initializer}; /* {source}:{lines[0]} */')
        receipt.append({'name':name,'source':source,'source_lines':lines,'source_width':source_width,'source_count':source_count,'native_count':count,'values':values,'native_type':ctype})
    graphics = 'src/root/m1B4E.asm'
    emit(graphics, 'g_3D20', 'char', 128)
    point, lines = words(by_source[graphics], '_DATA', '_g_3DA0', 2, 2)
    result.append('CanonicalAsmPoint g_3DA0 = { ' + ', '.join(hex(v) for v in point) + ' };')
    receipt.append({'name':'g_3DA0','source':graphics,'source_lines':lines,'values':point,'view':'g_3DA0 scalar consumers address x; Point/Pt consumers address x/y'})
    emit(graphics, 'g_3DA4', 'char *', initializer='NULL')
    emit(graphics, 'g_3DA8', 'char *', 1, initializer='NULL', source_width=2)
    if words(by_source[graphics], '_DATA', '_g_3DA8', 2, 2)[0] != [0,0]: raise ValueError('font pointer is not all-zero')
    for name in ['g_3DB2','g_3DB4','g_3DB6','g_3DD2','g_3DD4','g_3DDA','g_3DDC','g_3DDE','fd_55B3_3DE6','fd_55B3_3DE8']:
        emit(graphics,name,'int16_t')
    emit(graphics,'g_41C0','uint8_t',16)
    data=by_source[graphics]['segments']['_DATA']
    start=data['labels']['_g_41D0']['offset']
    end=max(d['offset']+d['width']*len(d['values']) for d in data['directives'])
    count=end-start
    if data['labels']['_g_4220']['offset']-start!=80:
        raise ValueError('canonical g4220 pattern view differs')
    values,lines=byte_range(by_source[graphics],'_DATA','_g_41D0',count)
    result.append('uint8_t g_41D0['+str(count)+'] = { '+', '.join(hex(v) for v in values)+' };')
    receipt.append({'name':'g_41D0','source':graphics,'source_lines':lines,
                    'source_width':1,'source_count':count,'native_count':count,
                    'values':values,'native_type':'uint8_t',
                    'interior_view':{'g_4220':'g_41D0+80'},
                    'native_consumed_domain':'S00 pattern index&15,16bytes each;first256bytes'})
    receipt.append({'name':'g_3DA2','source':graphics,'source_lines':[19],'no_storage':'same second DW already owned by g_3DA0 Point.y','native_view':'g_3DA0.y'})
    for name in ['g_3DE0','g_3DE2','g_3DE4']:
        values, lines = byte_range(by_source[graphics], '_DATA', '_' + name, 2)
        result.append(f'int16_t {name} = {values[0] | values[1]<<8}; /* two source DB cells, lines {lines} */')
        receipt.append({'name':name,'source':graphics,'source_lines':lines,'values':values,'view':'word over labelled low byte and next labelled high byte; byte consumers select representation byte 0'})
    ems='src/root/m195A.asm'
    emit(ems,'fd_55B3_360C','int8_t')
    emit(ems,'fd_55B3_360E','char *',initializer='NULL')
    emit(ems,'fd_55B3_3612','int16_t'); emit(ems,'fd_55B3_3614','int16_t')
    for name in ['fd_55B3_6770','fd_55B3_6772']:emit('src/root/m2650.asm',name,'int16_t')
    emit('src/S02/m3126.asm','g_21A4','uint16_t')
    bitmap, lines=byte_range(by_source['src/root/m1FBD.asm'],'_DATA','_g_5ABE',1280)
    if any(bitmap):raise ValueError('bitmap source group has nonzero initializer')
    result.append('char g_5ABE[1280] = {0}; /* actual 1040 + 79 + 1 + 160 contiguous zero-byte directives */')
    receipt.append({'name':'g_5ABE','source':'src/root/m1FBD.asm','source_lines':lines,'count':1280,'view':'whole clear/write span groups g_5ABE[1040],g_5ECE[79],g_5F1D[1],anonymous[160]; no storage guessed'})
    (WORK/'canonical_asm_numeric_data.c').write_text('\n'.join(result)+'\n')
    return receipt


def emit_audio(facts):
    """Numeric ASM words, proven sample null records and real byte tables.

    OFFSET selectors remain DOS numeric selector words. The accepted assembler
    fixup's displacement resolves each explicit source OFFSET expression.
    Storage sizes and ordinary initializers always come from source directives.
    """
    f=next(x for x in facts if x['source']=='src/root/m28BC.asm')
    object_path=AUDIO_OBJECT
    object_source=AUDIO_SOURCE
    if object_source.read_bytes()!= (ROOT/f['source']).read_bytes():
        raise ValueError('assembler OFFSET witness was not built from current canonical source')
    obj=omf.OmfReader().read_file(object_path)
    public={x['name']:x for x in obj.publics_in('_DATA')}
    fixes={x['offset']:x for x in obj.fixups_in('_DATA')}
    result=['/* Generated source-derived ASM state; OFFSET values are DOS metadata, never host pointers. */',
            '#include <stdint.h>',
            '#include "portable/whole_program/platform/audio_state.h"', '']
    receipt=[]
    for name in ['g_693C','fd_55B3_6B42','fd_55B3_6B4A','fd_55B3_6BA0']:
        values,lines=words(f,'_DATA','_'+name)
        result.append(f'int16_t {name} = {hex(values[0])}; /* canonical ASM line {lines[0]} */')
        receipt.append({'name':name,'source_lines':lines,'source_values':values,'native_type':'int16_t'})
    for name in ['fd_55B3_6B9C','fd_55B3_74AD','fd_55B3_74AF','fd_55B3_74B1','fd_55B3_74B3',
                 'fd_55B3_74B5','fd_55B3_74B7','fd_55B3_74B9']:
        label=f['segments']['_DATA']['labels']['_'+name]
        row=next(x for x in f['segments']['_DATA']['directives'] if x['offset']==label['offset'])
        if row['width']!=2 or len(row['values'])!=1 or not isinstance(row['values'][0],dict):raise ValueError('not one OFFSET word')
        expression=row['values'][0]['symbolic_expression']
        if not re.fullmatch(r'offset\s+\w+',expression,re.I):raise ValueError('not direct symbolic code OFFSET')
        if public['_'+name]['offset']!=label['offset']:raise ValueError('source/object symbol offset disagrees')
        fix=fixes[label['offset']]
        if fix['target']!='TIMER_TEXT' or fix['loc']!='offset16':raise ValueError('not near code selector')
        enum='CANONICAL_DOS_AUDIO_'+expression.split()[-1].upper()
        result.append(f'int16_t {name} = {hex(fix["displacement"])}; /* {expression}, symbolic assembler displacement */')
        receipt.append({'name':name,'source_lines':[row['line']],'source_expression':expression,'assembler_fixup':fix,'native_meaning':'DOS near-code selector; host never dereferences this numeric word'})
    # Four actual contiguous 20-byte zero records; this is the only owner.
    values,lines=byte_range(f,'_DATA','_fd_55B3_6B4C',4*20)
    if any(values):raise ValueError('sample records have nonzero source initializer')
    result.append('PortableWholeAudioRuntimeSample fd_55B3_6B4C[4] = {{0}};')
    receipt.append({'name':'fd_55B3_6B4C','source_lines':lines,'source_byte_extent':80,'record_stride':20,'count':4,'native_type':'PortableWholeAudioRuntimeSample[4]','initializer':'every source record field is zero/null','no_owner_for':'fd_55B3_6B4E EQU g_6B4C+2; consumer fields are typed views'})
    # Its source value is an OFFSET relocation; the target DGROUP placement
    # provides historical logical address metadata, without host-address casts.
    label=f['segments']['_DATA']['labels']['_fd_55B3_6B9E']; fix=fixes[label['offset']]
    if fix['target']!='_DATA' or fix['loc']!='offset16':raise ValueError('volume base not DATA OFFSET')
    manifest=json.loads((ROOT/'layout/manifest.json').read_text())
    module=manifest['modules']['root:28BC']
    placements=module.get('placements',{})
    # Manifest shape is checked rather than assumed below.
    placement=next(x for x in placements if x['segment']=='_DATA') if isinstance(placements,list) else placements['_DATA']
    base=placement['off']
    logical=base+fix['displacement']
    result.append(f'uint16_t fd_55B3_6B9E = {hex(logical)}; /* OFFSET DGROUP:vol_tab; canonical source logical address */')
    receipt.append({'name':'fd_55B3_6B9E','source_expression':'offset DGROUP:vol_tab','assembler_fixup':fix,'canonical_DATA_placement_offset':base,'DOS_logical_address':logical,'native_meaning':'arithmetic source word; no host pointer'})
    start=f['segments']['_DATA']['labels']['_fd_55B3_6BA4']['offset']; end=f['segments']['_DATA']['labels']['vol_tab']['offset']
    levels,lines=byte_range(f,'_DATA','_fd_55B3_6BA4',end-start)
    # fd6BA4 remains an actual byte owner. Its word-read-then-low-byte source
    # view is a load of fd6BA4[2*vol]; header and consumer conversion must use
    # that explicit byte-index view, never allocate a second word table.
    result.append(f'uint8_t fd_55B3_6BA4[{len(levels)}] = {{')
    for i in range(0,len(levels),16):result.append('    '+', '.join(hex(v) for v in levels[i:i+16])+',')
    result.append('};')
    receipt.append({'name':'fd_55B3_6BA4','source_lines':lines,'source_byte_extent':len(levels),'native_type':'uint8_t[255]','consumer_view':'m2815 low byte of int16 element vol => fd_55B3_6BA4[2*vol]','header_change_required':'extern uint8_t fd_55B3_6BA4[255];'})
    volume, volume_lines = byte_range(f, '_DATA', 'vol_tab', 2048)
    result.append('uint8_t portable_canonical_volume_tables[2048] = {')
    for i in range(0, len(volume), 16):
        result.append('    ' + ', '.join(hex(v) for v in volume[i:i+16]) + ',')
    result.append('};')
    receipt.append({'name': 'portable_canonical_volume_tables', 'source_lines': volume_lines,
                    'source_byte_extent': 2048, 'native_type': 'uint8_t[2048]'})
    (WORK/'canonical_audio_data.c').write_text('\n'.join(result)+'\n')
    return {'source_sha256':f['sha256'],'assembler_offset_witness':{'source':str(object_source),'source_sha256':sha(object_source),'object':str(object_path),'object_sha256':sha(object_path)},'emission':receipt}
