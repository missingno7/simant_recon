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
    grouped = {'cursor_alternate_rect_left': ('int16_t', 4), 'kbd_scan_code_state': ('uint8_t', 128)}
    selected = ['g_432A', 'cursor_drawn_flag', 'g_4332', 'cursor_update_lock', 'cursor_alternate_rect_active', 'cursor_alternate_rect_left', 'g_433E', 'cursor_drawn_left', 'cursor_drawn_top', 'cursor_drawn_bottom', 'cursor_drawn_right', 'cursor_bitmap_width', 'cursor_bitmap_height', 'g_434E', 'g_4352', 'g_4356', 'g_435A', 'g_4362', 'g_4363', 'g_4364', 'cursor_show_level', 'g_4366', 'g_4368', 'g_4369', 'g_4DA4', 'g_53BC', 'g_53BD', 'kbd_scan_code_state']
    result = ['/* Generated only from src/platform/input_timer.asm symbolic data directives. */', '#include <stdint.h>', '']
    receipt = []
    for name in selected:
        asm = '_' + name
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
            'extern uint32_t g_434E;', 'extern uint8_t kbd_scan_code_state[128];']
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
              '#include "canonical_graphics_data.h"', '']
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
    graphics = 'src/platform/video/bios_bitmap.asm'
    emit(graphics, 'gfx_row_scratch', 'char', 128)
    point, lines = words(by_source[graphics], '_DATA', '_gfx_text_pen_x', 2, 2)
    result.append('CanonicalAsmPoint gfx_text_pen_x = { ' + ', '.join(hex(v) for v in point) + ' };')
    receipt.append({'name':'gfx_text_pen_x','source':graphics,'source_lines':lines,'values':point,'view':'gfx_text_pen_x scalar consumers address x; Point/Pt consumers address x/y'})
    emit(graphics, 'gfx_secondary_font', 'char *', initializer='NULL')
    emit(graphics, 'gfx_primary_font_offset', 'char *', 1, initializer='NULL', source_width=2)
    if words(by_source[graphics], '_DATA', '_gfx_primary_font_offset', 2, 2)[0] != [0,0]: raise ValueError('font pointer is not all-zero')
    for name in ['gfx_screen_width_pixels','gfx_screen_height_pixels','gfx_screen_row_bytes','g_3DD2','gfx_cursor_draw_lock','gfx_font_glyph_stride','gfx_font_height_pixels','fontWidth','gfx_clip_left_pixels','gfx_clip_right_pixels']:
        emit(graphics,name,'int16_t')
    emit(graphics,'gfx_colour_translation','uint8_t',16)
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
    receipt.append({'name':'gfx_text_pen_y','source':graphics,'source_lines':[19],'no_storage':'same second DW already owned by gfx_text_pen_x Point.y','native_view':'gfx_text_pen_x.y'})
    for name in ['_foreColor','g_3DE2','g_3DE4']:
        values, lines = byte_range(by_source[graphics], '_DATA', '_' + name, 2)
        result.append(f'int16_t {name} = {values[0] | values[1]<<8}; /* two source DB cells, lines {lines} */')
        receipt.append({'name':name,'source':graphics,'source_lines':lines,'values':values,'view':'word over labelled low byte and next labelled high byte; byte consumers select representation byte 0'})
    ems='src/memory/ems.asm'
    emit(ems,'ems_version','int8_t')
    emit(ems,'ems_page_frame_pointer','char *',initializer='NULL')
    emit(ems,'ems_free_page_count','int16_t'); emit(ems,'ems_total_page_count','int16_t')
    for name in ['source_bitmap_width','dest_bitmap_width']:emit('src/graphics/glyph_blit.asm',name,'int16_t')
    emit('src/platform/video/vga8_raster.asm','g_21A4','uint16_t')
    text_source='src/graphics/bitmap_text.asm'
    text_facts=by_source[text_source]
    text_data=text_facts['segments']['_DATA']
    text_labels=text_data['labels']
    text_start=text_labels['_text_bitmap_pixels']['offset']
    text_end=text_start+1280
    pixel_count=text_labels['_text_bitmap_string_copy']['offset']-text_start
    string_count=text_labels['_g_5F1D']['offset']-text_labels['_text_bitmap_string_copy']['offset']
    terminator=next(d for d in text_data['directives']
                    if d['offset']==text_labels['_g_5F1D']['offset'])
    if terminator['width']!=1 or len(terminator['values'])!=1:
        raise ValueError('g_5F1D source terminator shape differs')
    tail_count=text_end-(terminator['offset']+terminator['width'])
    if (text_labels['_text_bitmap_height']['offset']!=text_labels['_text_bitmap_width']['offset']+2 or
        text_start!=text_labels['_text_bitmap_width']['offset']+4 or
        pixel_count!=1040 or string_count!=79 or tail_count!=160):
        raise ValueError('canonical text owner/alias layout differs from the reviewed ASM span')
    bitmap, lines=byte_range(text_facts,'_DATA','_text_bitmap_pixels',text_end-text_start)
    if any(bitmap):raise ValueError('bitmap source group has nonzero initializer')
    width_values,width_lines=words(text_facts,'_DATA','_text_bitmap_width',1,2)
    height_values,height_lines=words(text_facts,'_DATA','_text_bitmap_height',1,2)
    result.append(f'uint16_t text_bitmap_width = {hex(width_values[0])}; /* canonical source line {width_lines[0]} */')
    result.append(f'uint16_t text_bitmap_height = {hex(height_values[0])}; /* canonical source line {height_lines[0]} */')
    result.append('CanonicalTextBitmapStorage text_bitmap_pixels = {0}; /* one 1280-byte clear span with exact ASM interior views */')
    result.append(f'__asm__(".globl text_bitmap_string_copy; .set text_bitmap_string_copy, text_bitmap_pixels+{pixel_count}");')
    result.append(f'__asm__(".globl g_5F1D; .set g_5F1D, text_bitmap_pixels+{pixel_count+string_count}");')
    result.append('_Static_assert(sizeof(text_bitmap_pixels) == 1280u, "source text clear extent");')
    result.append(f'_Static_assert(offsetof(CanonicalTextBitmapAliases, text_bitmap_string_copy) == {pixel_count}u, "source text string alias offset");')
    result.append(f'_Static_assert(offsetof(CanonicalTextBitmapAliases, g_5F1D) == {pixel_count+string_count}u, "source text terminator alias offset");')
    result.append(f'_Static_assert(offsetof(CanonicalTextBitmapAliases, anonymous) == {pixel_count+string_count+1}u, "source text trailing extent");')
    receipt.append({'name':'text_bitmap_pixels','source':text_source,'source_lines':lines,'count':1280,'native_type':'CanonicalTextBitmapStorage','view':'text_bitmap_pixels.clear_span covers the exact 1040 + 79 + 1 + 160 source span','alias_layout':{'width':'text_bitmap_width','height':'text_bitmap_height','pixels':{'field':'aliases.text_bitmap_pixels','offset':0,'count':pixel_count},'string':{'field':'aliases.text_bitmap_string_copy','offset':pixel_count,'count':string_count},'terminator':{'field':'aliases.g_5F1D','offset':pixel_count+string_count,'count':1},'anonymous':{'field':'aliases.anonymous','offset':pixel_count+string_count+1,'count':tail_count}}})
    receipt.append({'name':'text_bitmap_width','source':text_source,'source_lines':width_lines,'count':1,'native_type':'uint16_t','owner':'canonical ASM text width cell'})
    receipt.append({'name':'text_bitmap_height','source':text_source,'source_lines':height_lines,'count':1,'native_type':'uint16_t','owner':'canonical ASM text height cell'})
    receipt.append({'name':'text_bitmap_string_copy','source':text_source,'source_lines':[text_labels['_text_bitmap_string_copy']['line']],'count':string_count,'native_view':'text_bitmap_pixels.aliases.text_bitmap_string_copy','native_symbol':'text_bitmap_string_copy','native_symbol_offset':pixel_count,'owner':'text_bitmap_pixels'})
    receipt.append({'name':'g_5F1D','source':text_source,'source_lines':[text_labels['_g_5F1D']['line']],'count':1,'native_view':'text_bitmap_pixels.aliases.g_5F1D','native_symbol':'g_5F1D','native_symbol_offset':pixel_count+string_count,'owner':'text_bitmap_pixels'})
    (WORK/'canonical_asm_numeric_data.c').write_text('\n'.join(result)+'\n')
    return receipt


def emit_audio(facts):
    """Numeric ASM words, proven sample null records and real byte tables.

    OFFSET selectors remain DOS numeric selector words. The accepted assembler
    fixup's displacement resolves each explicit source OFFSET expression.
    Storage sizes and ordinary initializers always come from source directives.
    """
    f=next(x for x in facts if x['source']=='src/sound/sample_timer.asm')
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
    for name in ['snd_lpt_dac_port','midi_service_countdown','snd_dac_io_base','snd_sb_dsp_write_port']:
        values,lines=words(f,'_DATA','_'+name)
        result.append(f'int16_t {name} = {hex(values[0])}; /* canonical ASM line {lines[0]} */')
        receipt.append({'name':name,'source_lines':lines,'source_values':values,'native_type':'int16_t'})
    for name in ['snd_sample_output_routine','snd_speaker_output_pointer','snd_adlib_output_pointer','snd_lpt_output_pointer','snd_port200_output_pointer',
                 'snd_sb_output_pointer','snd_port222_output_pointer','snd_based_dac_output_pointer']:
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
    values,lines=byte_range(f,'_DATA','_snd_sample_channel_records',4*20)
    if any(values):raise ValueError('sample records have nonzero source initializer')
    result.append('PortableWholeAudioRuntimeSample snd_sample_channel_records[4] = {{0}};')
    receipt.append({'name':'snd_sample_channel_records','source_lines':lines,'source_byte_extent':80,'record_stride':20,'count':4,'native_type':'PortableWholeAudioRuntimeSample[4]','initializer':'every source record field is zero/null','no_owner_for':'fd_55B3_6B4E EQU g_6B4C+2; consumer fields are typed views'})
    # Its source value is an OFFSET relocation; the target DGROUP placement
    # provides historical logical address metadata, without host-address casts.
    label=f['segments']['_DATA']['labels']['_snd_volume_table_offset']; fix=fixes[label['offset']]
    if fix['target']!='_DATA' or fix['loc']!='offset16':raise ValueError('volume base not DATA OFFSET')
    manifest=json.loads((ROOT/'layout/manifest.json').read_text())
    module=manifest['modules']['root:28BC']
    placements=module.get('placements',{})
    # Manifest shape is checked rather than assumed below.
    placement=next(x for x in placements if x['segment']=='_DATA') if isinstance(placements,list) else placements['_DATA']
    base=placement['off']
    logical=base+fix['displacement']
    result.append(f'uint16_t snd_volume_table_offset = {hex(logical)}; /* OFFSET DGROUP:vol_tab; canonical source logical address */')
    receipt.append({'name':'snd_volume_table_offset','source_expression':'offset DGROUP:vol_tab','assembler_fixup':fix,'canonical_DATA_placement_offset':base,'DOS_logical_address':logical,'native_meaning':'arithmetic source word; no host pointer'})
    start=f['segments']['_DATA']['labels']['_snd_opl_volume_curve']['offset']; end=f['segments']['_DATA']['labels']['vol_tab']['offset']
    levels,lines=byte_range(f,'_DATA','_snd_opl_volume_curve',end-start)
    # fd6BA4 remains an actual byte owner. Its word-read-then-low-byte source
    # view is a load of fd6BA4[2*vol]; header and consumer conversion must use
    # that explicit byte-index view, never allocate a second word table.
    result.append(f'uint8_t snd_opl_volume_curve[{len(levels)}] = {{')
    for i in range(0,len(levels),16):result.append('    '+', '.join(hex(v) for v in levels[i:i+16])+',')
    result.append('};')
    receipt.append({'name':'snd_opl_volume_curve','source_lines':lines,'source_byte_extent':len(levels),'native_type':'uint8_t[255]','consumer_view':'m2815 low byte of int16 element vol => snd_opl_volume_curve[2*vol]','header_change_required':'extern uint8_t snd_opl_volume_curve[255];'})
    volume, volume_lines = byte_range(f, '_DATA', 'vol_tab', 2048)
    result.append('uint8_t portable_canonical_volume_tables[2048] = {')
    for i in range(0, len(volume), 16):
        result.append('    ' + ', '.join(hex(v) for v in volume[i:i+16]) + ',')
    result.append('};')
    receipt.append({'name': 'portable_canonical_volume_tables', 'source_lines': volume_lines,
                    'source_byte_extent': 2048, 'native_type': 'uint8_t[2048]'})
    (WORK/'canonical_audio_data.c').write_text('\n'.join(result)+'\n')
    return {'source_sha256':f['sha256'],'assembler_offset_witness':{'source':str(object_source),'source_sha256':sha(object_source),'object':str(object_path),'object_sha256':sha(object_path)},'emission':receipt}
