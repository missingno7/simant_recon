"""Read-only voice/content observations, independent of foreground service IDs.

Coordinates are fast PIT periods (slow IRQ=16, fast/rejected IRQ=1). S observes
completed voice setup (not the audible start); P observes each contribution at the
two-channel mix instruction. Payloads are decoded resource bytes, never replay
inputs. Raw OUT streams remain independently retained.
"""
import hashlib
import json
from pathlib import Path


def content_binding(memory, base, addresses):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    try:
        from .audio_timer import timer_binding
    except ImportError:
        from audio_timer import timer_binding
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    timer_binding(memory, base, addresses)
    lo, hi = (base + addresses[n] for n in ('snd_timer_mix_two_channels', 'snd_timer_mix_four_channels'))
    mix = list(decoder.disasm(memory[lo:hi], lo))
    output = next(i.address for i in mix if i.mnemonic == 'jmp' and i.op_str.startswith('word ptr ['))
    xlats = [i for i in mix if i.mnemonic == 'xlatb' and i.address < output]
    if len(xlats) != 2:
        raise ValueError('Expected the two-channel mixer volume lookups')
    pc = xlats[-1].address + xlats[-1].size
    if next(i for i in mix if i.address == pc).mnemonic != 'xor':
        raise ValueError('Mixer contribution observation is not before the sum')
    points = [('m', pc, 0)]
    procedures = {}
    for name, kind in [('snd_start_sample_voice', 'v'), ('snd_stop_sample_voice', 'w')]:
        start = base + addresses[name]
        body = []
        for ins in decoder.disasm(memory[start:start + 512], start):
            body.append(ins)
            if ins.mnemonic == 'retf':
                break
        if (not body or body[-1].mnemonic != 'retf' or
                [(i.mnemonic,i.op_str) for i in body[:2]] != [('push','bp'),('mov','bp, sp')]):
            raise ValueError('Unbounded voice procedure: ' + name)
        target = base + addresses['snd_sample_interrupts_enable']
        calls = [i for i in body if i.mnemonic == 'lcall' and
                 len(i.bytes) == 5 and int.from_bytes(i.bytes[1:3], 'little') +
                 16 * int.from_bytes(i.bytes[3:5], 'little') == target]
        if len(calls) != (2 if kind == 'v' else 1):
            raise ValueError('Voice enable call census differs: ' + name)
        # Last enable follows the complete setup/clear; BP still addresses
        # source arguments. The early unsuccessful-start return is excluded.
        points.append((kind, calls[-1].address, 14 if kind == 'v' else 8))
        procedures[name] = dict(start=start, size=body[-1].address + body[-1].size - start,
                               sha256=hashlib.sha256(memory[start:body[-1].address + body[-1].size]).hexdigest(),
                               instructions={i.address: bytes(i.bytes).hex() for i in body})
    return dict(contract='audio-content-v1', points=points, procedures=procedures,
                channels=base + addresses['snd_sample_channel_records'],
                volume=base + addresses['snd_volume_table_offset'],
                tick_units='fast PIT periods; slow=16, fast/rejected=1',
                mixer_instructions={i.address: bytes(i.bytes).hex() for i in mix})


def instrument_sample_unit(text):
    """Add two read-only callbacks to a TEST COPY of the generated whole TU.

    The exact converted source stays pinned in the observer receipt. Neither
    callbacks nor source copies participate in the ordinary application build.
    """
    import re
    start = 'c->owner = s;'
    stop = re.search(r'snd_sample_channel_records\[ch\]\.snd = \(?snd_sample_channel_records\[ch\]\.owner = [^;]+;', text)
    if text.count(start) != 1 or stop is None:
        raise ValueError('Converted sample voice observation sites changed')
    text = text.replace(start, start + '\n  portable_test_sample_boundary(0, ch);')
    text = text.replace(stop[0], stop[0] + '\n  portable_test_sample_boundary(1, ch);')
    return 'extern void portable_test_sample_boundary(unsigned, int);\n' + text


def read_content(path, entries=None):
    """Reject incomplete/invalid captures; keep complete per-voice byte streams."""
    result = dict(opl={}, voices=[], checkpoints={}, progress=[], controls=[], mixed=[])
    active = [None, None]
    ended = False
    previous = (0, 0)
    contribution = None
    with Path(path).open(encoding='ascii') as source:
        if source.readline().strip() != 'SIMANT_AUDIO_CONTENT 1':
            raise ValueError('Missing audio content header')
        for number, line in enumerate(source, 2):
            fields = line.split()
            if len(fields) < 5 or ended:
                raise ValueError(f'Invalid content row {number}')
            tag = fields[0]
            tick, ordinal, step, phase = map(int, fields[1:5])
            if (min(tick, ordinal, step) < 0 or phase not in (0, 1) or (phase and not step)
                    or tick < previous[0] or ordinal < previous[1]):
                raise ValueError(f'Content coordinates go backwards at {number}')
            previous = tick, ordinal
            coordinate = dict(tick=tick, service_ordinal=ordinal, step=step, phase=phase,
                              entry=step if tag == 'C' else step + 1)
            data = fields[5:]
            if tag == 'C' and (not step or phase!=1):
                raise ValueError('Progress checkpoint is not a simulation entry')
            if tag == 'E':
                if data:
                    raise ValueError('Content trailer has arguments')
                result['end'] = coordinate
                ended = True
            if entries is not None and (step > entries or step == entries and tag not in ('C', 'E')):
                continue
            if tag == 'O':
                if len(data) != 3:
                    raise ValueError('Malformed OPL content')
                bank, register, value = map(int, data)
                if bank not in (0, 1) or not 0 <= register <= 255 or not 0 <= value <= 255:
                    raise ValueError('OPL content outside byte range')
                channel = opl_channel(register)
                group = f'{bank}:channel:{channel}' if channel is not None else f'{bank}:global'
                result['opl'].setdefault(group, []).append(dict(coordinate, register=register, value=value))
            elif tag == 'K':
                if len(data) != 2:
                    raise ValueError('Malformed device control')
                port, value = map(int, data)
                if port != 0x226 and not (port == 0x22c and value in (0xd1, 0xd3)):
                    raise ValueError('Unsupported device control')
                result['controls'].append(dict(coordinate, port=port, value=value))
            elif tag == 'U':
                raise ValueError('Audio profile outside observed direct-DAC/OPL contract')
            elif tag == 'S':
                if len(data) != 9:
                    raise ValueError('Malformed sample start')
                ch, obj, rate, volume, end, loop, flags, size = map(int, data[:8])
                payload = bytes.fromhex(data[8])
                if (ch not in (0, 1) or len(payload) != size or volume not in range(8) or flags not in (0,128)
                        or any(not 0<=v<=65535 for v in (obj,rate,end,loop,size))):
                    raise ValueError('Invalid sample start/payload')
                if active[ch] is not None:
                    active[ch]['stop'] = dict(coordinate, reason='replaced')
                voice = dict(start=coordinate, channel=ch, object=obj, rate=rate, volume=volume,
                             end=end, loop=loop, flags=flags, size=size,
                             payload_sha256=hashlib.sha256(payload).hexdigest(), output=[])
                result['voices'].append(voice)
                active[ch] = voice
            elif tag == 'X':
                if len(data) != 1 or int(data[0]) not in (0, 1):
                    raise ValueError('Malformed sample stop')
                ch = int(data[0])
                if active[ch] is not None:
                    active[ch]['stop'] = dict(coordinate, reason='stopped')
                    active[ch] = None
            elif tag == 'P':
                if len(data) != 4:
                    raise ValueError('Malformed channel output')
                ch, obj, position, value = map(int, data)
                if ch not in (0, 1) or not 0 <= value <= 255 or not 0 <= position <= 65535:
                    raise ValueError('Invalid channel output')
                if ch == 0:
                    if contribution is not None:
                        raise ValueError('Unpaired mixer contribution')
                    contribution = (tick, value)
                else:
                    if contribution is None or contribution[0] != tick:
                        raise ValueError('Unpaired mixer contribution')
                    result['mixed'].append((tick, (contribution[1] + value) // 2))
                    contribution = None
                if obj >= 0:
                    if active[ch] is None or active[ch]['object'] != obj:
                        raise ValueError(f'Channel output lacks its sample start at line {number}')
                    active[ch]['output'].append((position, value, tick, step + 1))
            elif tag in ('C', 'Q'):
                hashes = tuple(int(x, 16) for x in data)
                if not hashes or any(x > 0xffffffff for x in hashes):
                    raise ValueError('Missing/invalid progress fingerprints')
                row = dict(coordinate, hashes=hashes)
                result['progress'].append(row)
                if tag == 'C':
                    if step in result['checkpoints']:
                        raise ValueError('Duplicate progress entry')
                    result['checkpoints'][step] = row
            elif tag != 'E':
                raise ValueError('Unknown content observation ' + tag)
    if not ended:
        raise ValueError('Audio content capture lacks completion trailer')
    if contribution is not None:
        raise ValueError('Truncated mixer contribution pair')
    terminal = result['checkpoints'].get(entries, result['end']) if entries else result['end']
    for voice in active:
        if voice is not None:
            voice['stop'] = dict(terminal, reason='run_end')
    return result


def opl_channel(register):
    """OPL2 operator slot wiring; all writes on one channel retain their order."""
    for base in (0xa0, 0xb0, 0xc0):
        if base <= register <= base + 8:
            return register - base
    if register & 0xe0 in (0x20, 0x40, 0x60, 0x80, 0xe0):
        offset = register & 0x1f
        if offset // 8 < 3 and offset % 8 < 6:
            return offset // 8 * 3 + offset % 8 % 3
    return None


def compare_content(dos_path, native_path, entries, tolerance=1, replay_complete=True, out=None,
                    raw_dos_path=None, raw_native_path=None, progress_names=None):
    """Full-run, ordered content verdict; no cross-device interleaving test.

    The tolerance is in fast PIT periods, NOT simulation entries or host time.
    Voice output sequences must match exactly through their common duration.
    Only a bounded terminal suffix can differ in duration when stop/run-end
    placement differs. Interior substitutions/insertions cannot be aligned away.
    """
    captures, errors = {}, {}
    for label, path in [('dos', dos_path), ('native', native_path)]:
        try:
            captures[label] = read_content(path, entries)
            if progress_names is not None and any(len(r['hashes'])!=len(progress_names) for r in captures[label]['progress']):
                raise ValueError('Progress vector does not match the pinned audio view census')
            raw_path = raw_dos_path if label == 'dos' else raw_native_path
            if raw_path is not None:
                try:
                    from .audio_commands import read_commands, decoded_commands
                except ImportError:
                    from audio_commands import read_commands, decoded_commands
                writes, endpoint = read_commands(raw_path)
                dac = [e['arguments'][0] for e in decoded_commands(writes)
                       if e['entry'] <= entries and e['kind'] == 'dsp_command' and e['command'] == 16
                       and not e.get('incomplete')]
                if dac != [v for tick, v in captures[label]['mixed']]:
                    raise ValueError('Observed channel contributions do not reproduce actual DAC bytes')
        except (OSError, ValueError) as error:
            errors[label] = str(error)
    result = dict(contract='audio-content-v1', tick_tolerance=tolerance,
                  tick_units='fast PIT periods (214/1193181.667 seconds); slow IRQ=16',
                  status='AUDIO_INCOMPLETE', first_difference=None, capture_errors=errors,
                  replay_complete=bool(replay_complete), entries_compared=0)
    differences = []
    maximum = dict(opl=0, start=0, stop=0, output=0, progress=0)
    setup_drift=0

    def difference(kind, a, b, **detail):
        entry = min([x.get('entry', entries) for x in (a, b) if x] or [entries])
        differences.append(dict(kind=kind, entry=entry, dos=a, native=b, **detail))

    if not errors:
        a, b = captures['dos'], captures['native']
        for i in range(max(len(a['controls']), len(b['controls']))):
            x = a['controls'][i] if i < len(a['controls']) else None
            y = b['controls'][i] if i < len(b['controls']) else None
            if x is None or y is None or (x['port'], x['value']) != (y['port'], y['value']):
                difference('DEVICE_CONTROL', x, y, index=i)
                break
            if abs(x['tick'] - y['tick']) > tolerance:
                difference('DEVICE_CONTROL_PLACEMENT', x, y, index=i)
                break
        for group in sorted(set(a['opl']) | set(b['opl'])):
            left, right = a['opl'].get(group, []), b['opl'].get(group, [])
            for i in range(max(len(left), len(right))):
                x, y = left[i] if i < len(left) else None, right[i] if i < len(right) else None
                if x is None or y is None or (x['register'], x['value']) != (y['register'], y['value']):
                    difference('OPL_CONTENT', x, y, group=group, index=i)
                    break
                drift = abs(x['tick'] - y['tick'])
                maximum['opl'] = max(maximum['opl'], drift)
                if drift > tolerance:
                    difference('OPL_PLACEMENT', x, y, group=group, index=i, ticks=drift)
                    break
        left, right = a['voices'], b['voices']
        metadata = ('object', 'rate', 'volume', 'end', 'loop', 'flags', 'size', 'payload_sha256')
        for i in range(max(len(left), len(right))):
            x, y = left[i] if i < len(left) else None, right[i] if i < len(right) else None
            if x is None or y is None or any(x[k] != y[k] for k in metadata):
                difference('SAMPLE_IDENTITY_OR_CONTENT', x['start'] if x else None, y['start'] if y else None,
                           index=i, metadata={label: {k: v[k] for k in metadata} if v else None
                                              for label, v in [('dos', x), ('native', y)]})
                break
            # The setup callback precedes the final enable/PIT call. Pending
            # replay IRQs can drain at that next service without producing any
            # sample yet. Audible boundaries are the actual first/last emitted
            # contributions, independent of this compiler/instruction placement.
            setup_drift=max(setup_drift,abs(x['start']['tick']-y['start']['tick']))
            if bool(x['output']) != bool(y['output']):
                difference('SAMPLE_OUTPUT_PRESENCE', x['start'], y['start'], index=i)
            elif x['output'] and y['output']:
                for key, at in [('start',0),('stop',-1)]:
                    u,v=x['output'][at],y['output'][at]
                    drift=abs(u[2]-v[2]);maximum[key]=max(maximum[key],drift)
                    if drift>tolerance:
                        difference('SAMPLE_'+key.upper()+'_PLACEMENT',dict(entry=u[3],tick=u[2]),
                                   dict(entry=v[3],tick=v[2]),index=i,ticks=drift)
            for j, (u, v) in enumerate(zip(x['output'], y['output'])):
                if u[:2] != v[:2]:
                    difference('SAMPLE_OUTPUT_BYTE', dict(entry=u[3], tick=u[2]), dict(entry=v[3], tick=v[2]),
                               index=i, output_index=j, bytes=[u[:2], v[:2]], object=x['object'])
                    break
                drift = abs(u[2] - v[2])
                maximum['output'] = max(maximum['output'], drift)
                if drift > tolerance:
                    difference('SAMPLE_OUTPUT_PLACEMENT', dict(entry=u[3], tick=u[2]), dict(entry=v[3], tick=v[2]),
                               index=i, output_index=j, ticks=drift)
                    break
            count_delta = abs(len(x['output']) - len(y['output']))
            stop_delta = abs(x['output'][-1][2] - y['output'][-1][2]) if x['output'] and y['output'] else 0
            if count_delta > min(tolerance, stop_delta):
                difference('SAMPLE_OUTPUT_LENGTH', x['stop'], y['stop'], index=i,
                           counts=[len(x['output']), len(y['output'])], object=x['object'])
        progress = compare_progress(a, b, entries, tolerance, progress_names)
        differences.extend(progress['differences'])
        maximum['progress'] = progress['max_tick_distance']
        complete = replay_complete and len(a['checkpoints']) == len(b['checkpoints']) == entries
        result.update(status='AUDIO_INCOMPLETE' if not complete else 'AUDIO_DIFFERENCE' if differences else 'AUDIO_EQUAL',
                      entries_compared=min(len(a['checkpoints']), len(b['checkpoints'])),
                      maximum_tick_distance=maximum, setup_tick_distance_diagnostic=setup_drift,progress=progress,
                      counts={label: dict(opl=sum(map(len, v['opl'].values())), samples=len(v['voices']),
                                         sample_bytes=sum(len(s['output']) for s in v['voices']))
                              for label, v in captures.items()})
    result['first_difference'] = min(differences, key=lambda d: d['entry']) if differences else None
    result['difference_count'] = len(differences)
    result['differences'] = differences
    if progress_names is not None:
        result['progress_views'] = list(progress_names)
    if out is not None:
        (Path(out) / 'audio-content.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def compare_progress(a, b, entries, tolerance, names=None):
    """Symmetric per-entry progress comparison against nearby observed states."""
    import bisect
    def states(capture):
        ranges = {}
        rows = capture['progress']
        for i, row in enumerate(rows):
            end = max(row['tick'], rows[i + 1]['tick'] - 1) if i + 1 < len(rows) else capture['end']['tick']
            ranges.setdefault(row['hashes'], []).append((row['tick'], end))
        return ranges
    ranges = [states(v) for v in (a, b)]
    differences, maximum = [], 0
    for entry in range(1, entries + 1):
        x, y = a['checkpoints'].get(entry), b['checkpoints'].get(entry)
        if not x or not y:
            continue  # completeness is checked independently
        if abs(x['tick']-y['tick'])>tolerance:
            differences.append(dict(kind='MUSIC_CHECKPOINT_PLACEMENT',entry=entry,dos=x,native=y))
            continue
        if x['hashes'] == y['hashes']:
            continue
        distances = []
        for row, lookup in [(x, ranges[1]), (y, ranges[0])]:
            spans = lookup.get(row['hashes'], [])
            # Short vectors occur rarely; use a binary search by their start.
            at = bisect.bisect_right(spans, (row['tick'], float('inf')))
            candidates = spans[max(0, at - 1):at + 1]
            distances.append(min((max(lo - row['tick'], row['tick'] - hi, 0) for lo, hi in candidates), default=None))
        if any(d is None or d > tolerance for d in distances):
            differences.append(dict(kind='MUSIC_PROGRESS', entry=entry, dos=x, native=y, nearest_ticks=distances,
                                    views=[names[i] if names else str(i) for i,(u,v) in enumerate(zip(x['hashes'],y['hashes'])) if u!=v]))
        else:
            maximum = max(maximum, *distances)
    return dict(status='AUDIO_PROGRESS_DIFFERENCE' if differences else 'AUDIO_PROGRESS_EQUAL',
                entries_compared=min(len(a['checkpoints']), len(b['checkpoints'])),
                requested_entries=entries, max_tick_distance=maximum,
                first_differing_entry=differences[0]['entry'] if differences else None,
                views=differences[0].get('views',[]) if differences else [],differences=differences[:1])


def content_signature(result):
    first=result.get('first_difference')
    return dict(status=result['status'],first_differing_step=first['entry'] if first else None,
                contract=result['contract'],tick_tolerance=result['tick_tolerance'],first_difference=first,
                progress=result.get('progress'),maximum_tick_distance=result.get('maximum_tick_distance'),
                counts=result.get('counts'),capture_errors=result['capture_errors'])
