"""Exact audio OUT sequences between consecutive DoAntSim entry snapshots.

Both observers write the same observation-only format::

    SIMANT_AUDIO_COMMANDS 1
    W service_ordinal step phase port_hex byte_hex
    E service_ordinal step phase

A write at step k belongs to the interval ending at entry k+1. Empty intervals
participate too. Port/value order decides command equality; service coordinates
are retained and compared separately, since a hosted timer may deliver at the
next sampled service. No writes, registers, arguments or DMA setup are masked.
Decoded names are diagnostics; the raw sequence remains the acceptance input.
"""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct


HEADER = 'SIMANT_AUDIO_COMMANDS 1'
PORT_RANGES = ((0x388, 0x38b), (0x220, 0x22f), (0, 0xf), (0x80, 0x8f))


@dataclass(frozen=True)
class Write:
    ordinal: int
    step: int
    phase: int
    port: int
    value: int

    @property
    def entry(self):
        return self.step + 1

    def record(self):
        return dict(service_ordinal=self.ordinal, step=self.step, phase=self.phase,
                    port=f'{self.port:04X}', value=f'{self.value:02X}')


def _coordinate(fields):
    ordinal, step, phase = map(int, fields)
    if ordinal < 0 or step < 0 or phase not in (0, 1) or (phase and not step):
        raise ValueError('Invalid audio service coordinate')
    if ordinal < 2 * step - phase:
        raise ValueError('Audio ordinal precedes its entry/return services')
    return ordinal, step, phase


def read_commands(path):
    """Read a complete raw capture, rejecting missing trailers and malformed rows."""
    path = Path(path)
    writes, end, previous = [], None, (0, 0, 0)
    with path.open(encoding='ascii') as source:
        if source.readline().strip() != HEADER:
            raise ValueError('Missing audio command contract: ' + str(path))
        for number, line in enumerate(source, 2):
            fields = line.split()
            if not fields:
                continue
            try:
                if end is not None:
                    raise ValueError('Rows after audio trailer')
                if fields[0] not in ('W', 'E') or len(fields) != (6 if fields[0] == 'W' else 4):
                    raise ValueError('Malformed audio row')
                coordinate = _coordinate(fields[1:4])
                ordinal, step, phase = coordinate
                if ordinal < previous[0] or 2 * step - phase < 2 * previous[1] - previous[2]:
                    raise ValueError('Audio coordinates move backwards')
                previous = coordinate
                if fields[0] == 'E':
                    end = dict(service_ordinal=ordinal, step=step, phase=phase)
                else:
                    port, value = (int(v, 16) for v in fields[4:])
                    if not any(lo <= port <= hi for lo, hi in PORT_RANGES) or not 0 <= value <= 255:
                        raise ValueError('Unsupported audio port or non-byte OUT')
                    writes.append(Write(ordinal, step, phase, port, value))
            except ValueError as error:
                raise ValueError(f'{path}:{number}: {error}') from error
    if end is None:
        raise ValueError('Missing audio completion trailer: ' + str(path))
    return writes, end


# The provider's mode-6 path uses 10 (direct DAC), D1 and D3. Additional
# parameter lengths below cover the SB commands needed to diagnose DMA starts
# (pinned DOSBox-X src/hardware/sblaster.cpp DSP_cmd_len_sb/sb16 tables).
# Unknown commands stay opaque; a reset reestablishes decoding synchronization.
DSP_ARGUMENTS = {0x10: 1, 0x14: 2, 0x15: 2, 0x16: 2, 0x17: 2, 0x1c: 0,
                 0x24: 2, 0x2c: 0, 0x40: 1, 0x41: 2, 0x42: 2,
                 0x48: 2, 0x80: 2, 0x90: 0, 0x91: 0, 0x98: 0, 0x99: 0,
                 0xd0: 0, 0xd1: 0, 0xd3: 0, 0xd4: 0, 0xd5: 0,
                 0xd6: 0, 0xd8: 0, 0xd9: 0, 0xda: 0,
                 0xe0: 1, 0xe1: 0, 0xe2: 1, 0xe3: 0, 0xe4: 1, 0xe8: 0,
                 0xf2: 0}
DMA_STARTS = {0x14, 0x15, 0x16, 0x17, 0x1c, 0x24, 0x2c, 0x90, 0x91, 0x98, 0x99}


def decoded_commands(writes):
    """Yield diagnostic events, retaining every contributing raw-write index.

    DMA unmask means the controller was enabled, not that a transfer happened.
    dsp_dma_start means a DSP transfer command was issued; it makes no claim
    about actual DMA reads, memory contents, duration or audible output.
    """
    indices = [None, None]
    pending, opaque, reset = None, False, 0
    for i, write in enumerate(writes):
        port, value = write.port, write.value
        base = dict(raw_indices=[i], service_ordinal=write.ordinal,
                    entry=write.entry, step=write.step, phase=write.phase)
        if 0x388 <= port <= 0x38b:
            bank = (port - 0x388) // 2
            if not port & 1:
                indices[bank] = value
                yield dict(base, kind='opl_select', bank=bank, register=value)
                continue
            yield dict(base, kind='opl_register', bank=bank,
                       register=indices[bank], value=value)
        elif port == 0x226:
            if reset and not value:
                pending, opaque = None, False
            reset = value
            yield dict(base, kind='dsp_reset', value=value)
        elif port == 0x22c:
            if opaque:
                yield dict(base, kind='dsp_opaque_byte', value=value)
                continue
            if pending is None:
                length = 3 if 0xb0 <= value <= 0xcf else DSP_ARGUMENTS.get(value)
                pending = dict(base, kind='dsp_command', command=value,
                               arguments=[], expected_arguments=length)
                if length is None:
                    opaque = True
            else:
                pending['arguments'].append(value)
                pending['raw_indices'].append(i)
            if pending['expected_arguments'] is None or len(pending['arguments']) == pending['expected_arguments']:
                command = pending['command']
                if command in DMA_STARTS or 0xb0 <= command <= 0xcf:
                    pending['kind'] = 'dsp_dma_start'
                yield pending
                pending = None
        elif port <= 0xf or 0x80 <= port <= 0x8f:
            kind = 'dma_unmask' if port == 0x0a and not value & 4 else 'dma_program'
            yield dict(base, kind=kind, port=f'{port:04X}', value=value,
                       **(dict(channel=value & 3) if port == 0x0a else {}))
        else:
            yield dict(base, kind='sb_port', port=f'{port:04X}', value=value)
    if pending:
        yield dict(pending, incomplete=True)


def _group(writes, entries):
    grouped = [[] for _ in range(entries)]
    for write in writes:
        if write.entry <= entries:
            grouped[write.entry - 1].append(write)
    return grouped


def _descriptions(writes, targets):
    result = {index: writes[index].record() for index in targets}
    # Decoding starts at capture start, so register selectors and DSP arguments
    # may span entry boundaries without being reset by the comparison grouping.
    for event in decoded_commands(writes):
        for index in event['raw_indices']:
            if index in result:
                result[index]['decoded'] = event
    return result


def _raw_digest(writes):
    digest = hashlib.sha256()
    for write in writes:
        digest.update(struct.pack('<HB', write.port, write.value))
    return digest.hexdigest()


def _summary(writes):
    kinds = Counter(event['kind'] for event in decoded_commands(writes))
    return dict(raw_writes=len(writes), raw_sha256=_raw_digest(writes),
                decoded_counts=dict(sorted(kinds.items())),
                raw_ports=dict(sorted(Counter(f'{w.port:04X}' for w in writes).items())))


def compare_commands(dos_path, native_path, out=None, entries=None, replay_complete=True):
    """Compare complete files; optionally write audio-commands.json under out.

    Missing/malformed captures report INCOMPLETE, never equal. `entries` selects
    an explicit prefix of longer captures. Replay completion is an independent
    caller-supplied premise, not inferred from matching audio writes.
    """
    captures, errors = {}, {}
    for label, path in (('dos', dos_path), ('native', native_path)):
        try:
            captures[label] = read_commands(path)
        except (ValueError, OSError) as error:
            errors[label] = str(error)
    result = dict(contract='raw-audio-commands-v1', status='AUDIO_COMMANDS_INCOMPLETE',
                  replay_complete=bool(replay_complete), first_differing_entry=None,
                  entries_compared=0, rows=[], capture_errors=errors)
    if not errors:
        dos, de = captures['dos']
        native, ne = captures['native']
        requested = entries if entries is not None else max(de['step'], ne['step'])
        if not isinstance(requested, int) or requested < 1:
            raise ValueError('Requested audio entries must be a positive integer')
        count = min(requested, de['step'], ne['step'])
        groups = [_group(writes, count) for writes in (dos, native)]
        first, drift, offsets = None, None, [0, 0]
        targets = [set(), set()]
        drift_count = 0
        for entry, (a, b) in enumerate(zip(*groups), 1):
            index = next((i for i, (x, y) in enumerate(zip(a, b))
                          if (x.port, x.value) != (y.port, y.value)), min(len(a), len(b)))
            equal = index == len(a) == len(b)
            row = dict(entry=entry, status='AUDIO_COMMANDS_EQUAL' if equal else 'AUDIO_COMMANDS_DIFFERENCE',
                       raw_writes=[len(a), len(b)], raw_sha256=[_raw_digest(a), _raw_digest(b)])
            if not equal:
                left = offsets[0] + index if index < len(a) else None
                right = offsets[1] + index if index < len(b) else None
                if left is not None:
                    targets[0].add(left)
                if right is not None:
                    targets[1].add(right)
                row['first_difference'] = dict(write_index=index,
                                               dos=left, native=right)
                if first is None:
                    first = row
            else:
                for i, (x, y) in enumerate(zip(a, b)):
                    if (x.ordinal, x.phase) != (y.ordinal, y.phase):
                        drift_count += 1
                        if drift is None:
                            drift = dict(entry=entry, write_index=i, dos=x.record(), native=y.record())
            result['rows'].append(row)
            offsets[0] += len(a)
            offsets[1] += len(b)
        descriptions = [_descriptions(writes, target) for writes, target in zip((dos, native), targets)]
        for row in result['rows']:
            if 'first_difference' in row:
                for label, lookup in zip(('dos', 'native'), descriptions):
                    index = row['first_difference'][label]
                    row['first_difference'][label] = lookup[index] if index is not None else None
        complete = count == requested and bool(replay_complete)
        result.update(status='AUDIO_COMMANDS_DIFFERENCE' if first else
                      'AUDIO_COMMANDS_EQUAL' if complete else 'AUDIO_COMMANDS_INCOMPLETE',
                      requested_entries=requested, entries_compared=count,
                      capture_complete=count == requested,
                      first_differing_entry=first['entry'] if first else None,
                      first_difference=first.get('first_difference') if first else None,
                      coordinates_status='ORDINAL_DRIFT' if drift else 'ORDINAL_UNALIGNED' if first else
                                         'ORDINAL_EQUAL' if complete else 'ORDINAL_INCOMPLETE',
                      coordinate_drift_writes=drift_count, first_coordinate_drift=drift,
                      endpoints=dict(dos=de, native=ne),
                      summaries=dict(dos=_summary([w for w in dos if w.entry <= count]),
                                     native=_summary([w for w in native if w.entry <= count])))
    result['scope'] = ('Exact byte OUT order per interval ending at each entry; service ordinal/phase drift is separate. '
                       'OPL, SB DSP and low DMA/page ports; no PCM, elapsed-time or DMA-memory equality claim.')
    if out is not None:
        (Path(out) / 'audio-commands.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def command_signature(result):
    """Stable compact pin covering every entry's counts and first differences."""
    keys = ('status', 'replay_complete', 'first_differing_entry', 'entries_compared',
            'requested_entries', 'capture_complete', 'coordinates_status',
            'coordinate_drift_writes', 'first_coordinate_drift')
    signature = {key: result.get(key) for key in keys}
    signature['rows_sha256'] = hashlib.sha256(json.dumps(result['rows'], sort_keys=True,
                                                        separators=(',', ':')).encode()).hexdigest()
    return signature
