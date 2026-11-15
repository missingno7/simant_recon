"""Source-driver playback observations for ideal-clock, mode-6 runs.

The hooks observe successful song setup, active StopSong, and the physical OPL
voice interface. No expected event, IRQ placement or device response is input.
"""
import hashlib
import re

FAST_NS = 214 * 12 * 1_000_000_000 / 14_318_180


def instrument_provider_unit(text):
    """Observe the provider's event time in a TEST COPY, without advancing it."""
    for old in ('p->time_ns=p->irq_ns;', 'p->time_ns=target;'):
        if text.count(old)!=1:raise ValueError('Provider event-time site changed')
        text=text.replace(old,old+'portable_test_audio_game_time(p->time_ns);')
    return 'extern void portable_test_audio_game_time(unsigned long long);\n'+text


def binding(memory, base, addresses):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    points, procedures = [], {}
    for name, kind in [('snd_load_and_start_song', '1'), ('StopSong', '2'),
                       ('snd_opl_set_note_level', '3'), ('snd_opl_clear_voice_pitch', '4'),
                       ('snd_start_configured_effect', '5')]:
        start = base + addresses[name]
        # Use the next independently named code anchor as the complete extent;
        # the first RETF is the failure exit in the song loader.
        end = min(base + p for p in addresses.values() if base + p > start)
        body = list(decoder.disasm(memory[start:end], start))
        if not body or body[-1].mnemonic != 'retf':
            raise ValueError('Unbounded playback procedure: ' + name)
        if kind in ('3','4','5') and (bytes(body[0].bytes) != b'\x55' or body[1].mnemonic != 'mov' or body[1].op_str != 'bp, sp'):
            raise ValueError('Unbound playback stack ABI: ' + name)
        # Song success returns through its final RETF. All other sites read
        # untouched entry arguments at SS:SP+4 (far return address).
        points.append((kind, body[-1].address if kind == '1' else start, 0))
        procedures[name] = dict(start=start, size=end-start,
            sha256=hashlib.sha256(memory[start:end]).hexdigest(),
            instructions={i.address: bytes(i.bytes).hex() for i in body})
    return dict(contract='audio-playback-v1', points=points, procedures=procedures,
        song_number=base+addresses['midi_loaded_song_number'],
        song_state=base+addresses['midi_playback_state'])


def validate_reference(directory, manifest):
    """Rebind observation instructions, including the hash-pinned live image."""
    import json
    from pathlib import Path
    from .capture_dos_steps import capture_addresses
    from .state_schema import ROOT,sha
    from .audio_content import content_binding
    capture=directory/'capture'
    boundary=json.loads((capture/'boundary-manifest.json').read_text())
    if manifest.get('audio_playback')!='audio-playback-v1' or not boundary.get('modifier_byte_reads'):
        raise ValueError('Reference lacks playback/source-clock bindings')
    for name,expected in boundary['snapshots'].items():
        if sha(capture/name)!=expected:raise ValueError('Changed observation image: '+name)
    original=manifest['target']=='original'
    executable=ROOT/'assets/SIMANT.EXE'
    if not original:
        execution=json.loads((capture/'execution-report.json').read_text())
        pin=next(p for p in execution['inputs'] if p['path'].endswith('build-report.json'))
        executable=ROOT/json.loads((ROOT/pin['path']).read_text())['link']['candidate_executable']['path']
    if sha(executable)!=manifest['executable_sha256']:raise ValueError('Changed playback oracle executable')
    addresses=capture_addresses(original,executable)
    memory=(capture/'exec-simstep.1.bin').read_bytes();base=boundary['runtime_base']
    for key,value in [('audio_playback',binding(memory,base,addresses)),
                      ('audio_content',content_binding(memory,base,addresses))]:
        if json.loads(json.dumps(value))!=boundary.get(key):raise ValueError('Changed playback instruction binding: '+key)


def instrument_music_unit(text, source):
    """Read-only callbacks in a disposable generated TU; fail on source drift."""
    if source == 'src/sound/midi_player.c':
        old = '  snd_control_interrupts_enable();\n}'
        if text.count(old) != 1:
            raise ValueError('Song success observation changed')
        text = text.replace(old, '  snd_control_interrupts_enable();\n  portable_test_playback(1, midi_loaded_song_number, 0, 0, 0);\n}')
        old = '  if (midi_playback_state)\n  {'
        if text.count(old) != 1:
            raise ValueError('Song stop observation changed')
        text = text.replace(old, old+'\n    portable_test_playback(2, midi_loaded_song_number, 0, 0, 0);')
    elif source == 'src/sound/opl2_voices.c':
        for name, call in [('snd_opl_set_note_level', '3, instr, note, vol, voice'),
                           ('snd_opl_clear_voice_pitch', '4, voice, 0, 0, 0')]:
            pattern = r'(void '+name+r'\([^;{}]+\)\s*\{)'
            text, n = re.subn(pattern, lambda m:m[0]+'\n  portable_test_playback('+call+');', text)
            if n != 1:
                raise ValueError('OPL playback observation changed: '+name)
    elif source == 'src/sound/midi_voices.c':
        pattern = r'(void snd_start_configured_effect\(int16_t n\)\s*\{)'
        text, n = re.subn(pattern, lambda m:m[0]+'\n  portable_test_playback(5, n, 0, 0, 0);', text)
        if n != 1:
            raise ValueError('Effect observation changed')
    else:
        return text
    return 'extern void portable_test_playback(unsigned, int, int, int, int);\n'+text


def compare_events(left, right, tolerance_ns):
    """Order is strict per physical channel and song stream, not across voices."""
    def groups(capture):
        result = {}
        active = {}
        for event in capture['events']:
            kind, args = event['kind'], event['arguments']
            if kind == 'effect':
                continue  # Invocation coverage; actual output is observed below.
            if kind == 'note_on':
                channel = args[3]
                active[channel] = args[:3]
                key = 'channel:'+str(channel)
            elif kind == 'note_off':
                channel = args[0]
                if channel not in active:
                    continue  # A reset of an already silent voice plays nothing.
                args = [*active.pop(channel), channel]
                key = 'channel:'+str(channel)
            else:
                key = 'song'
            result.setdefault(key, []).append(dict(event, arguments=args))
        return result
    a, b = groups(left), groups(right)
    differences, maximum = [], 0
    for group in sorted(set(a)|set(b)):
        x, y = a.get(group, []), b.get(group, [])
        for i in range(max(len(x), len(y))):
            u, v = x[i] if i < len(x) else None, y[i] if i < len(y) else None
            detail = dict(entry=min(e['entry'] for e in (u,v) if e), group=group, index=i, dos=u, native=v,
                          layer='song-player' if group=='song' else 'voice-dispatch')
            if u is None or v is None or (u['kind'],u['arguments']) != (v['kind'],v['arguments']):
                differences.append(dict(kind='PLAYBACK_CONTENT', **detail));break
            drift = abs(u['time_ns']-v['time_ns']);maximum=max(maximum,drift)
            if drift > tolerance_ns:
                differences.append(dict(kind='PLAYBACK_PLACEMENT', nanoseconds=drift, **detail));break
    return dict(differences=differences, maximum_ns=maximum)
