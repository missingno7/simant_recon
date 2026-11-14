"""Audit generic resource-hook calls, including the non-PCM diagnostic path."""
from pathlib import Path


def read_calls(path, ids=None, service_limit=None):
    rows = []
    end = None
    previous = 0
    with Path(path).open(encoding='ascii') as source:
        if source.readline().strip() != 'SIMANT_SOUND_CALLS 1':
            raise ValueError('Missing sound-call diagnostic header')
        for line in source:
            fields = line.split()
            if not fields:
                continue
            if end is not None or fields[0] not in ('C', 'E'):
                raise ValueError('Invalid sound-call diagnostic row')
            if len(fields) != (7 if fields[0] == 'C' else 4):
                raise ValueError('Malformed sound-call diagnostic coordinate')
            ordinal, step, phase = map(int, fields[1:4])
            if ordinal < previous or phase not in (0, 1) or step < 0 or (not step and phase) or ordinal < 2*step-phase:
                raise ValueError('Invalid sound-call diagnostic order')
            previous = ordinal
            if fields[0] == 'E':
                end = dict(service_ordinal=ordinal, step=step, phase=phase)
            else:
                obj, kind = map(int, fields[4:6])
                caller = int(fields[6], 16)
                if not 0 <= obj <= 65535 or not 0 <= kind <= 65535 or caller < 0:
                    raise ValueError('Invalid source sound-call argument')
                rows.append(dict(service_ordinal=ordinal, step=step, phase=phase,
                                 object=obj, type=kind, caller=caller, qualified=kind == 5))
    if end is None:
        raise ValueError('Missing sound-call diagnostic trailer')
    if ids is not None and sum(row['qualified'] for row in rows) != bytes(ids).count(20):
        raise ValueError('PCM diagnostic calls differ from checked sound entries')
    selected = rows if service_limit is None else [row for row in rows if row['service_ordinal'] < service_limit]
    return dict(calls=len(selected), pcm_calls=sum(row['qualified'] for row in selected),
                nonpcm_calls=sum(not row['qualified'] for row in selected), rows=selected, endpoint=end)
