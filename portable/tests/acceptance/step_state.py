"""Common ordered fingerprint schema for DOS capture and native observation."""
import hashlib
import json
import re
import struct
from pathlib import Path
try:
    from .state_schema import ROOT, acceptance, inventory, original_layout
except ImportError:
    from state_schema import ROOT, acceptance, inventory, original_layout


def fingerprint(data, sentinel=False):
    if sentinel:
        stop = next((i+2 for i in range(0, len(data)-1, 2) if data[i:i+2] == b'\0\x80'), len(data))
        data = data[:stop]
    value = 2166136261
    for b in data:
        value = ((value ^ b) * 16777619) & 0xffffffff
    return value


def schema(build, dos_report=None, executable=None):
    if __package__:
        from .native_schema import native_views
    else:
        from native_schema import native_views
    specs = inventory(native_build=build, dos_report=dos_report)
    native = native_views(executable or build/'simant-canonical.exe', specs, build/'semantic-spans.json')
    original = original_layout()
    policy = json.loads((Path(__file__).parent/'runtime_views.json').read_text())
    if set(policy) != set(specs):
        raise ValueError('Runtime view inventory changed: classify new/removed views explicitly')
    owners = []
    for name, view in native.items():
        spec = specs[name]
        if view['status'] == 'OK' and spec.get('owner', name) == name and '::' not in name and not spec.get('native_expr'):
            owners.append((spec['dos_address'], view['bytes'], view['address'], name))
    items = []
    for index, _, length, _, expression in acceptance.save_schema():
        match = re.fullmatch(r'\((\w+) \+ (\d+)\)', expression)
        name, extra = (match[1], int(match[2])) if match else (expression, 0)
        start = specs[name]['dos_address'] + extra
        cursor, end, slices = start, start+length, []
        while cursor < end:
            covering = [(a, n, p, owner) for a, n, p, owner in owners if a <= cursor < a+n]
            if not covering:
                raise ValueError('Unobserved SaveRec owner at ' + str((index, expression, cursor)))
            # All overlapping owner views must name identical native storage.
            if len({p+cursor-a for a, n, p, owner in covering}) != 1:
                raise ValueError('Conflicting SaveRec native owners at '+str(index))
            stop = min(end, min(a+n for a, n, p, owner in covering))
            stop = min([stop]+[a for a, n, p, owner in owners if cursor < a < stop])
            slices.append([covering[0][2]+cursor-covering[0][0], stop-cursor])
            cursor = stop
        items.append(dict(name='save:'+str(index)+':'+expression, bytes=length, verdict=True,
                          category='game_state', original_address=original[name]['dos_address']+extra,
                          canonical_address=start, slices=slices, sentinel=False))
    excluded = {}
    for name, spec in specs.items():
        view = native[name]
        if view['status'] != 'OK' or name not in original:
            excluded[name] = dict(view, policy=policy[name], original_available=name in original)
            continue
        category=policy[name].get('raw_category',policy[name]['category'])
        if policy[name].get('coverage')=='live_only_unavailable':
            excluded[name+':live']=dict(status='UNAVAILABLE_LIVE_VIEW',policy=policy[name])
        item = dict(name=name, bytes=view['bytes'], verdict=category=='game_state',
                    category=category, original_address=original[name]['dos_address'],
                    canonical_address=spec['dos_address'], slices=[[view['address'], view['bytes']]],
                    sentinel=name=='clip_window_z_order')
        items.append(item)
        if item['sentinel']:
            # Keep the raw suffix differences visible beside the policy hash.
            items.append(dict(item, name=name+':raw', verdict=False, sentinel=False))
    stable = [{k: v for k, v in item.items() if k not in ('slices','canonical_address')} for item in items]
    identity = hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()
    return dict(identity=identity, items=items, excluded=excluded)


def read_hashes(path, count):
    raw = path.read_bytes()
    if len(raw) % (4*count):
        raise ValueError('Truncated fingerprints: '+str(path))
    values = struct.unpack('<'+'I'*(len(raw)//4), raw)
    return [values[i:i+count] for i in range(0, len(values), count)]


def bind_reference_policy(current, reference):
    """Verify a reference against freshly resolved locations; take the verdict
    policy from the current runtime_views.json.

    Every view is fingerprinted at every entry whatever its category, so the
    category only decides the verdict. The reference's identity is checked with
    the policy it was recorded under; the verdict then follows the tracked,
    reviewed classification. Views whose category differs from the recorded one
    are listed in current['policy_changes'] so the change stays visible.
    Layout/order/width/sentinel changes still require new observations.
    """
    if len(current['items'])!=len(reference['items']):raise ValueError('Reference schema changed')
    policy=[]
    for live,stored in zip(current['items'],reference['items']):
        fields=set(live)-{'slices','canonical_address','verdict','category'}
        if any(live[k]!=stored[k] for k in fields):raise ValueError('Reference schema changed')
        policy.append((live['verdict'],live['category']))
        live['verdict']=stored['verdict'];live['category']=stored['category']
    stable=[{k:v for k,v in item.items() if k not in ('slices','canonical_address')} for item in current['items']]
    current['identity']=hashlib.sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest()
    if current['identity']!=reference['identity']:raise ValueError('Invalid reference policy identity')
    changes=[]
    for live,(verdict,category) in zip(current['items'],policy):
        if (verdict,category)!=(live['verdict'],live['category']):
            changes.append(dict(name=live['name'],recorded=live['category'],current=category))
        live['verdict'],live['category']=verdict,category
    current['policy_changes']=changes
    return current


def split_frame(path, items):
    raw = path.read_bytes()
    if len(raw) != sum(i['bytes'] for i in items):
        raise ValueError('Truncated full frame: '+str(path))
    result, at = {}, 0
    for item in items:
        result[item['name']] = raw[at:at+item['bytes']]
        at += item['bytes']
    return result
