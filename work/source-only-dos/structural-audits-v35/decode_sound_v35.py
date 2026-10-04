#!/usr/bin/env python3
"""Read-only SOUND database/song-stream research using the reconstructed DOS parser rules.

Emits metadata and counts only. Never saves record payloads, decoded strings, or resource bytes.
"""
from __future__ import annotations
import collections, hashlib, json, pathlib, re, struct
ROOT = pathlib.Path(__file__).resolve().parents[3]
ASSET_NDX = ROOT / 'assets/SOUND.NDX'
ASSET_DAT = ROOT / 'assets/SOUND.DAT'
SOURCE_PATHS = [
    'src/root/m0000.c', 'src/root/m284A.c', 'src/root/m19A9.c',
    'src/root/m277E.c', 'src/root/m295C.c', 'src/root/m290D.c',
    'src/root/m00DF.c', 'src/data/d55B3_0064.c', 'src/data/d55B3_00B8.c',
]
DATA_LEN = [2,2,2,2,1,1,2] # exact g_75A4 initializer; type 7 indexes past it
INF = 0x7fffffff

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def u16be(b,p): return struct.unpack_from('>H',b,p)[0]
def i16be(b,p): return struct.unpack_from('>h',b,p)[0]
def u32be(b,p): return struct.unpack_from('>I',b,p)[0]
def i32(v):
    v &= 0xffffffff
    return v-0x100000000 if v & 0x80000000 else v
def i16(v):
    v &= 0xffff
    return v-0x10000 if v & 0x8000 else v
def source_long_be(b,p):
    v=0
    for k in range(4): v=i32((v<<8)+b[p+k])
    return v
def trunc_div(a,b):
    return (abs(a)//abs(b)) * (-1 if (a<0) != (b<0) else 1)
def vlq(b,p,end):
    v=0; start=p
    while True:
        if p >= end: raise ValueError('VLQ reads beyond track data')
        c=b[p]; p+=1
        v=i32((v<<7)+(c&0x7f))
        if not c&0x80: return v,p,p-start

def read_db():
    ndx=ASSET_NDX.read_bytes(); dat=ASSET_DAT.read_bytes()
    count=struct.unpack_from('<h',ndx,0)[0]
    if count < 0 or 20+count*8 > len(ndx): raise ValueError('bad SOUND.NDX source-readable prefix')
    rows=[]
    for i in range(count):
        off,obj,kind,flags=struct.unpack_from('<IhBB',ndx,20+8*i)
        if off+24>len(dat): raise ValueError(f'record header out of DAT at row {i}')
        recid,rtype,rflags,size,extra=struct.unpack_from('<5h',dat,off+14)
        start=off+24; end=start+size
        if end>len(dat): raise ValueError(f'record payload exceeds DAT at row {i}')
        if flags & 1: raise ValueError(f'compressed SOUND record at row {i}; no resource decompressor assumed')
        rows.append({'row':i,'id':obj&0xffff,'kind':kind,'flags':flags,'off':off,
                     'record_header':[recid,rtype,rflags,size,extra],
                     'payload':dat[start:end]})
    return ndx,dat,rows

def source_maps():
    desc=(ROOT/'src/data/d55B3_0064.c').read_text(encoding='utf-8')
    m=re.search(r'static struct Song g_0068\s*=\s*\{\s*\{([^}]*)\}\s*,\s*\{([^}]*)\}',desc,re.S)
    if not m: raise ValueError('cannot read the effective Song initializer')
    nums=lambda s:[int(x,0) for x in re.findall(r'-?\d+',s)]
    programs,banks=nums(m.group(1)),nums(m.group(2))
    if len(programs)!=14 or len(banks)!=14: raise ValueError('Song initializer is not the expected 14+14 words')
    src=(ROOT/'src/data/d55B3_00B8.c').read_text(encoding='utf-8')
    samples={}
    for name,body in re.findall(r'static struct Sample\s+(s_\w+)\s*=\s*\{([^}]*)\}',src,re.S):
        vals=re.findall(r'(?<![A-Za-z_])(?:-?\d+|0x[0-9a-fA-F]+)',body)
        # Initializer contains a quoted name between fields and object id; parse final integer.
        samples[name]=int(vals[-1],0)
    maps={}
    for table in ('fd_55B3_0C42','fd_55B3_0EE2'):
        mt=re.search(r'struct Instr\s+'+table+r'\[56\]\s*=\s*\{(.*?)\n\};',src,re.S)
        if not mt: raise ValueError(f'missing instrument table {table}')
        entries=re.findall(r'\{\s*(SND_\w+)\s*,\s*(?:&([A-Za-z_]\w*)|0)\s*\}',mt.group(1))
        if len(entries)==55: entries.append(('SND_NONE',None)) # implicit zero-initialized C tail
        if len(entries)!=56: raise ValueError(f'{table}: expected 55 explicit plus implicit row, saw {len(entries)}')
        maps[table]=[{'kind':kind,'sample_id':samples.get(name) if name else None} for kind,name in entries]
    return programs,banks,maps

def db_payloads(rows,kind):
    d={}
    for r in rows:
        if r['kind']==kind:
            if r['id'] in d: raise ValueError(f'duplicate SOUND kind {kind} id {r["id"]:04x}')
            d[r['id']]=r
    return d

def parse_stream(sid,b):
    # Mirrors f_284A_0256/f_284A_0199: fixed offsets, big-endian lengths, per-track VLQ state.
    if len(b)<14 or b[:4]!=b'MThd': raise ValueError('not an MThd stream')
    declared_header_len=source_long_be(b,4) # f_284A_0151 returns signed 32-bit long
    if declared_header_len<0: raise ValueError('negative source MThd length')
    ntracks=u16be(b,10)
    division=u16be(b,12)
    offs=i16(declared_header_len+8) # f_284A_0199 receives this as a 16-bit int
    tracks=[]; track_layout=[]; access_max=13; vlq_max_bytes=0; vlq_max_value=0; int_offsets=[0,4,8,10,12]
    for ti in range(ntracks):
        if offs+8>len(b) or b[offs:offs+4]!=b'MTrk': raise ValueError(f'track {ti}: missing MTrk at source-computed offset')
        n=source_long_be(b,offs+4)
        if n<0: raise ValueError(f'track {ti}: negative source long length')
        start=i16(offs+8); end=start+n
        if end>len(b): raise ValueError(f'track {ti}: MTrk extent outside resource')
        first_delta,p,nvlq=vlq(b,start,end)
        int_offsets.extend((start,p-1))
        vlq_max_bytes=max(vlq_max_bytes,nvlq); vlq_max_value=max(vlq_max_value,first_delta)
        if p>=end: raise ValueError(f'track {ti}: missing first status')
        tracks.append({'start':start,'end':end,'pos':p,'status':b[p], 'time':first_delta,'done':False})
        access_max=max(access_max,p)
        track_layout.append({'start':start,'end':end})
        int_offsets.extend((offs,offs+4,start,end))
        offs=i16(offs+n+8) # f_284A_0199 narrows each updated offset back to int
    if not tracks: raise ValueError('zero-track song unsupported by current sequencer setup')
    # Source f_284A_02E4 always starts with track 0 at absolute time zero, irrespective of its first delta.
    cur=0; abs_time=0; tempo=500000; scale=tick_scale(tempo,480); event_n=0
    max_tempo=tempo; max_tempo_intermediate=trunc_div(tempo,1000)*1194; min_scale=max_scale=scale
    track_time_overflow_count=0; max_abs_track_time=max(abs(t['time']) for t in tracks)
    bursts=[]; total_events=collections.Counter(); total_channels=collections.defaultdict(collections.Counter)
    burst_events=collections.Counter(); burst_channels=collections.defaultdict(collections.Counter)
    burst_dispatches=0; burst_actions=0; per_track=collections.Counter()
    legacy_burst_dispatches=0; legacy_bursts=[]; exact_boundaries=[]; legacy_boundaries=[]
    warning=None; maxsteps=1_000_000; negative_returns=0; max_abs_return=0; max_abs_unwrapped_product=0
    product_overflow_count=0; boundary_predicate_disagreements=0
    raw_note_on_velocities=collections.Counter(); note_calls_by_type=collections.Counter()
    while event_n<maxsteps:
        t=tracks[cur]; p=t['pos']; end=t['end']; status=t['status']; typ=None; channel=None; note=None; velocity=None; event_class='other'
        if p>=end: warning=f'track {cur}: source parser reads past MTrk after {event_n} dispatches'; break
        if b[p]&0x80:
            status=b[p]; t['status']=status; p+=1
            access_max=max(access_max,p-1)
            int_offsets.append(p)
        if status in (0xF0,0xF7):
            length,p,nvlq=vlq(b,p,end); vlq_max_bytes=max(vlq_max_bytes,nvlq); vlq_max_value=max(vlq_max_value,length); access_max=max(access_max,p-1,p+length-1)
            p+=length
            if p>end: warning=f'track {cur}: sysex extent leaves MTrk'; break
            event_class='sysex'
        elif status==0xFF:
            if p>=end: warning=f'track {cur}: missing meta type'; break
            meta=b[p]
            access_max=max(access_max,p)
            if meta==0x2F:
                t['status']=0x2F; p-=1; event_class='end'
            elif meta==0x51:
                p+=2
                if p+3>end: warning=f'track {cur}: truncated tempo meta'; break
                tempo=(b[p]<<16)|(b[p+1]<<8)|b[p+2]; p+=3
                access_max=max(access_max,p-1)
                max_tempo=max(max_tempo,tempo)
                max_tempo_intermediate=max(max_tempo_intermediate,trunc_div(tempo,1000)*1194)
                scale=tick_scale(tempo,division); min_scale=min(min_scale,scale); max_scale=max(max_scale,scale); event_class='tempo'
            else:
                p+=1; length,p,nvlq=vlq(b,p,end); vlq_max_bytes=max(vlq_max_bytes,nvlq); vlq_max_value=max(vlq_max_value,length); access_max=max(access_max,p-1,p+length-1); p+=length
                if p>end: warning=f'track {cur}: meta extent leaves MTrk'; break
                event_class='meta'
        else:
            typ=(status&0x70)>>4; channel=status&0x0f
            if typ>=len(DATA_LEN):
                warning=f'track {cur}: event type {typ} indexes beyond g_75A4; exact source continuation depends on adjacent data'
                break
            width=DATA_LEN[typ]
            if p+width>end: warning=f'track {cur}: event type {typ} data leaves MTrk'; break
            access_max=max(access_max,p+width-1)
            if typ in (0,1):
                note=b[p]; velocity=b[p+1] if width>1 else 0
                event_class='note_on' if typ==1 and velocity else 'note_off'
                if channel<14:
                    total_channels[channel][event_class]+=1
                    total_channels[channel]['note_actions']+=1
                    burst_channels[channel][event_class]+=1
                    burst_channels[channel]['note_actions']+=1
                    burst_actions+=1
                    note_calls_by_type[f'type{typ}']+=1
                    if typ==1 and velocity: raw_note_on_velocities[velocity]+=1
            else:
                event_class=f'type{typ}'
            p+=width
        t['pos']=p; int_offsets.append(p)
        event_n+=1; burst_dispatches+=1; legacy_burst_dispatches+=1; total_events[event_class]+=1
        burst_events[event_class]+=1; per_track[cur]+=1
        # f_284A_038F: mark EOT infinite, otherwise add the next delta before choosing the earliest track.
        if t['status']!=0x2F:
            try: delta,t['pos'],nvlq=vlq(b,t['pos'],end)
            except ValueError as e: warning=f'track {cur}: {e}'; break
            vlq_max_bytes=max(vlq_max_bytes,nvlq); vlq_max_value=max(vlq_max_value,delta)
            access_max=max(access_max,t['pos']-1)
            int_offsets.append(t['pos'])
            raw_track_time=t['time']+delta
            t['time']=i32(raw_track_time)
            if t['time']!=raw_track_time: track_time_overflow_count+=1
            max_abs_track_time=max(max_abs_track_time,abs(t['time']))
        else: t['time']=INF
        best=0
        for i in range(1,len(tracks)):
            if tracks[best]['time']>tracks[i]['time'] and tracks[i]['status']!=0x2F: best=i
        if tracks[best]['status']==0x2F or tracks[best]['time']==INF:
            bursts.append({'dispatches':burst_dispatches,'note_event_actions':burst_actions,'r':0,'ended':True,
                           'event_counts':dict(burst_events),
                           'channel_counts':{str(k):dict(v) for k,v in burst_channels.items()}})
            legacy_bursts.append(legacy_burst_dispatches)
            break
        nexttime=tracks[best]['time']; delta=i32(nexttime-abs_time); abs_time=nexttime; cur=best
        unwrapped_product=scale*delta
        product=i32(unwrapped_product)
        if product!=unwrapped_product: product_overflow_count+=1
        max_abs_unwrapped_product=max(max_abs_unwrapped_product,abs(unwrapped_product))
        legacy_wait=unwrapped_product >> 8
        wait=i16(product >> 8)
        if (legacy_wait>0)!=(wait!=0): boundary_predicate_disagreements+=1
        if wait<0: negative_returns+=1
        max_abs_return=max(max_abs_return,abs(wait))
        # f_067F loops only for r==0; any signed-16 nonzero return ends this callback.
        if wait!=0:
            exact_boundaries.append(event_n)
            bursts.append({'dispatches':burst_dispatches,'note_event_actions':burst_actions,'r':wait,'ended':False,
                           'event_counts':dict(burst_events),
                           'channel_counts':{str(k):dict(v) for k,v in burst_channels.items()}})
            burst_events=collections.Counter(); burst_channels=collections.defaultdict(collections.Counter)
            burst_dispatches=0; burst_actions=0
        if legacy_wait>0:
            legacy_boundaries.append(event_n)
            legacy_bursts.append(legacy_burst_dispatches)
            legacy_burst_dispatches=0
    else: warning='event dispatch limit exceeded'
    summary=bursts
    return {'stream_id':sid,'payload_size':len(b),'declared_header_len':declared_header_len,'tracks':ntracks,'division':division,
            'trailing_payload_bytes':len(b)-offs,
            'dispatches_before_end_or_stop':event_n,'warning':warning,'bursts':summary,
            'max_burst_dispatches':max((x['dispatches'] for x in summary),default=0),
        'max_burst_note_event_actions':max((x['note_event_actions'] for x in summary),default=0),
            'total_note_event_actions':sum(v['note_actions'] for v in total_channels.values()),
            'negative_callback_returns':negative_returns,'max_abs_callback_return':max_abs_return,
        'max_abs_unwrapped_scale_delta':max_abs_unwrapped_product,'product_overflow_count':product_overflow_count,
            'boundary_predicate_disagreements':boundary_predicate_disagreements,
            'exact_boundary_count':len(exact_boundaries),'legacy_boundary_count':len(legacy_boundaries),
            'max_legacy_burst_dispatches':max(legacy_bursts,default=0),
            'max_vlq_bytes':vlq_max_bytes,
            'max_vlq_value':vlq_max_value,'max_source_int_offset':max(access_max,offs-1),
            'max_signed16_cursor':max(int_offsets),'min_signed16_cursor':min(int_offsets),
            'source_int_offsets_signed16_safe':min(int_offsets)>=-0x8000 and max(int_offsets)<0x8000,
            'max_tempo':max_tempo,'min_tempo_scale':min_scale,'max_tempo_scale':max_scale,
            'max_tempo_intermediate':max_tempo_intermediate,
            'track_time_overflow_count':track_time_overflow_count,'max_abs_track_time':max_abs_track_time,
            'declared_track_extent_trailing_bytes':len(b)-offs,
            'track_end_markers':len(track_layout),
            'bytes_from_backed_up_eot_status_to_track_end':sum(tr['end']-t['pos'] for tr,t in zip(track_layout,tracks) if t['status']==0x2f),
            'unread_bytes_after_eot_meta_type':sum(tr['end']-(t['pos']+2) for tr,t in zip(track_layout,tracks) if t['status']==0x2f),
            'channel_event_counts':{str(k):dict(v) for k,v in total_channels.items()},
            'dispatch_event_counts':dict(total_events),'note_event_calls_to_04C9_by_type':dict(note_calls_by_type),
            'raw_nonzero_note_on_velocity_count':sum(raw_note_on_velocities.values()),
            'raw_type1_zero_velocity_count':note_calls_by_type.get('type1',0)-sum(raw_note_on_velocities.values()),
            'raw_nonzero_note_on_velocity_1_count':raw_note_on_velocities.get(1,0),
            'initial_127_volume_scaled_nonzero_type1_count':sum(n for vel,n in raw_note_on_velocities.items() if ((127*vel)&0xffff)>>7),
            'minimum_raw_nonzero_note_on_velocity':min(raw_note_on_velocities,default=None)}

def tick_scale(tempo,division):
    # f_284A_0325: tempo/1000*1194/division/13, with integer division after each operation.
    if division==0: return 0
    v=trunc_div(tempo,1000)
    v=i32(v*1194)
    v=trunc_div(v,division)
    return trunc_div(v,13)

def main():
    ndx,dat,rows=read_db(); headers=db_payloads(rows,0x12); streams=db_payloads(rows,0x14)
    programs,banks,maps=source_maps()
    used={}; song_headers=[]
    for sid,r in sorted(headers.items()):
        p=r['payload']
        if len(p)<8: raise ValueError(f'{sid:04x}: kind-12 header shorter than fields used by f_0000_0193')
        stream_id=u16be(p,0); transpose=i16be(p,6)
        if stream_id not in streams: raise ValueError(f'{sid:04x}: kind-12 header names missing kind-14 object {stream_id:04x}')
        song_headers.append({'requested_song_id':f'{sid:04X}','stream_id':f'{stream_id:04X}','transpose':transpose})
        used.setdefault(stream_id,streams[stream_id]['payload'])
    results=[]
    for sid,payload in sorted(used.items()): results.append(parse_stream(sid,payload))
    # Add the accepted descriptor's fixed bank/program and both observed DAC selector maps.
    channel_map=[]
    for ch,(program,bank) in enumerate(zip(programs,banks)):
        entry={ 'channel':ch,'program_priority':program,'bank_device':bank }
        for table,short in [('fd_55B3_0C42','mode1'),('fd_55B3_0EE2','mode7')]:
            row=maps[table][bank]
            entry[short]={'instrument_kind':row['kind'],'sample_object_id':row['sample_id']}
        channel_map.append(entry)
    # Resource-wide active channels across all decoded unique streams.
    active=set()
    for res in results:
        # parse_stream counters are reset at callback boundaries; accumulate from burst summaries.
        for burst in res['bursts']:
            active.update(int(ch) for ch in burst.get('channel_counts',{}))
    compact_streams=[]
    for res in results:
        bursts=res['bursts']
        longest=max(bursts,key=lambda x:x['dispatches'],default=None)
        most_notes=max(bursts,key=lambda x:x['note_event_actions'],default=None)
        compact_streams.append({
          'stream_id':f"{res['stream_id']:04X}",'payload_size':res['payload_size'],
          'tracks':res['tracks'],'division':res['division'],'trailing_payload_bytes':res['trailing_payload_bytes'],
          'dispatches':res['dispatches_before_end_or_stop'],
          'events':res['dispatch_event_counts'],'note_event_actions':res['total_note_event_actions'],
          'active_channels':sorted(int(k) for k in res['channel_event_counts']),
          'channel_events':res['channel_event_counts'],'warning':res['warning'],
          'max_burst_dispatches':res['max_burst_dispatches'],
          'longest_burst':None if longest is None else {
             'dispatches':longest['dispatches'],'note_event_actions':longest['note_event_actions'],'r':longest['r'],
             'event_counts':longest['event_counts'],'channels':sorted(int(k) for k in longest['channel_counts'])},
          'max_burst_note_event_actions':res['max_burst_note_event_actions'],
          'largest_note_burst':None if most_notes is None else {
             'dispatches':most_notes['dispatches'],'note_event_actions':most_notes['note_event_actions'],'r':most_notes['r'],
             'event_counts':most_notes['event_counts'],'channels':sorted(int(k) for k in most_notes['channel_counts'])},
          'negative_callback_returns':res['negative_callback_returns'],
          'product_overflow_count':res['product_overflow_count'],
          'boundary_predicate_disagreements':res['boundary_predicate_disagreements'],
          'exact_boundary_count':res['exact_boundary_count'],'legacy_boundary_count':res['legacy_boundary_count'],
          'max_legacy_burst_dispatches':res['max_legacy_burst_dispatches'],
          'max_signed16_cursor':res['max_signed16_cursor'],
          'max_tempo':res['max_tempo'],'tempo_scale_range':[res['min_tempo_scale'],res['max_tempo_scale']],
          'max_tempo_intermediate':res['max_tempo_intermediate'],
          'track_time_overflow_count':res['track_time_overflow_count'],'max_abs_track_time':res['max_abs_track_time'],
          'max_abs_unwrapped_scale_delta':res['max_abs_unwrapped_scale_delta'],
          'max_vlq_bytes':res['max_vlq_bytes'],'max_vlq_value':res['max_vlq_value'],
          'source_int_offsets_signed16_safe':res['source_int_offsets_signed16_safe'],
          'declared_track_extent_trailing_bytes':res['declared_track_extent_trailing_bytes'],
          'bytes_from_backed_up_eot_status_to_track_end':res['bytes_from_backed_up_eot_status_to_track_end'],
          'unread_bytes_after_eot_meta_type':res['unread_bytes_after_eot_meta_type'],
          'note_event_calls_to_04C9_by_type':res['note_event_calls_to_04C9_by_type'],
          'raw_nonzero_note_on_velocity_count':res['raw_nonzero_note_on_velocity_count'],
          'raw_type1_zero_velocity_count':res['raw_type1_zero_velocity_count'],
          'raw_nonzero_note_on_velocity_1_count':res['raw_nonzero_note_on_velocity_1_count'],
          'initial_127_volume_scaled_nonzero_type1_count':res['initial_127_volume_scaled_nonzero_type1_count'],
          'minimum_raw_nonzero_note_on_velocity':res['minimum_raw_nonzero_note_on_velocity'],
        })
    sample_ids_kind5={r['id'] for r in rows if r['kind']==5}
    mode_samples={}
    for table,short in [('fd_55B3_0C42','mode1'),('fd_55B3_0EE2','mode7')]:
        ids=sorted({maps[table][bank]['sample_id'] for bank in banks if maps[table][bank]['kind']=='SND_DAC'})
        mode_samples[short]={'descriptor_sample_object_ids':ids,
                             'all_exist_as_SOUND_kind5':all(x in sample_ids_kind5 for x in ids),
                             'SFX_18_47_overlap':sorted(set(ids)&{18,47})}
    max_dispatch=max(compact_streams,key=lambda x:x['max_burst_dispatches'])
    max_notes=max(compact_streams,key=lambda x:x['max_burst_note_event_actions'])
    out={
      'scope':'read-only SOUND.NDX/SOUND.DAT domain analysis; no bytes or strings emitted',
      'asset_pins':{'SOUND.NDX':{'size':len(ndx),'sha256':sha(ASSET_NDX)},'SOUND.DAT':{'size':len(dat),'sha256':sha(ASSET_DAT)},
                    'source_hashes':{p:sha(ROOT/p) for p in SOURCE_PATHS}},
      'index':{'count':len(rows),'ndx_size':len(ndx),'source_prefix_bytes':20+8*len(rows),
               'ignored_suffix_bytes':len(ndx)-(20+8*len(rows)),
               'kinds':{str(k):v for k,v in sorted(collections.Counter(r['kind'] for r in rows).items())},
               'flags_by_kind':{str(k):dict(collections.Counter(str(r['flags']) for r in rows if r['kind']==k)) for k in sorted(set(r['kind'] for r in rows))}},
      'song_header_count':len(headers),'kind14_stream_count':len(streams),'song_headers':song_headers,
      'song_descriptor_channels':channel_map,'mode_sample_domain':mode_samples,
      'decoded_unique_streams':compact_streams,
      'burst_extrema':{'max_dispatch_stream':max_dispatch['stream_id'],'max_dispatch_count':max_dispatch['max_burst_dispatches'],
                       'max_note_stream':max_notes['stream_id'],'max_note_count':max_notes['max_burst_note_event_actions'],
                       'negative_callback_returns':sum(x['negative_callback_returns'] for x in compact_streams),
                       'product_overflow_count':sum(x['product_overflow_count'] for x in compact_streams),
                       'boundary_predicate_disagreements':sum(x['boundary_predicate_disagreements'] for x in compact_streams),
                       'legacy_boundary_count':sum(x['legacy_boundary_count'] for x in compact_streams),
                       'exact_boundary_count':sum(x['exact_boundary_count'] for x in compact_streams),
                       'max_legacy_burst_dispatches':max(x['max_legacy_burst_dispatches'] for x in compact_streams),
                       'max_abs_unwrapped_scale_delta':max(x['max_abs_unwrapped_scale_delta'] for x in compact_streams),
                       'max_vlq_bytes':max(x['max_vlq_bytes'] for x in compact_streams),
                       'max_vlq_value':max(x['max_vlq_value'] for x in compact_streams),
                       'max_tempo':max(x['max_tempo'] for x in compact_streams),
                       'max_tempo_intermediate':max(x['max_tempo_intermediate'] for x in compact_streams),
                       'track_time_overflow_count':sum(x['track_time_overflow_count'] for x in compact_streams),
                       'max_abs_track_time':max(x['max_abs_track_time'] for x in compact_streams),
                       'min_tempo_scale':min(x['tempo_scale_range'][0] for x in compact_streams),
                       'max_tempo_scale':max(x['tempo_scale_range'][1] for x in compact_streams),
                       'max_source_int_offset':max(x['max_signed16_cursor'] for x in compact_streams),
                       'total_note_event_actions':sum(x['note_event_actions'] for x in compact_streams),
                       'note_event_calls_to_04C9_by_type':{typ:sum(x['note_event_calls_to_04C9_by_type'].get(typ,0) for x in compact_streams) for typ in ('type0','type1')},
                       'raw_nonzero_note_on_velocity_count':sum(x['raw_nonzero_note_on_velocity_count'] for x in compact_streams),
                       'raw_type1_zero_velocity_count':sum(x['raw_type1_zero_velocity_count'] for x in compact_streams),
                       'raw_nonzero_note_on_velocity_1_count':sum(x['raw_nonzero_note_on_velocity_1_count'] for x in compact_streams),
                       'initial_127_volume_scaled_nonzero_type1_count':sum(x['initial_127_volume_scaled_nonzero_type1_count'] for x in compact_streams),
                       'total_bytes_from_backed_up_eot_status_to_track_end':sum(x['bytes_from_backed_up_eot_status_to_track_end'] for x in compact_streams),
                       'total_unread_bytes_after_eot_meta_type':sum(x['unread_bytes_after_eot_meta_type'] for x in compact_streams),
                       'all_declared_track_extents_end_at_payload_end':all(x['declared_track_extent_trailing_bytes']==0 for x in compact_streams),
                       'all_source_int_offsets_signed16_safe':all(x['source_int_offsets_signed16_safe'] for x in compact_streams),
                       'all_streams_completed':all(not x['warning'] for x in compact_streams)},
      'sound_effect_contrasts':{'SFX_0x12':{'bank_device':18,'priority':2,'mode1_sample_object_id':maps['fd_55B3_0C42'][18]['sample_id'],'mode7_sample_object_id':maps['fd_55B3_0EE2'][18]['sample_id']},
                                'SFX_0x2F':{'bank_device':47,'priority':3,'mode1_sample_object_id':maps['fd_55B3_0C42'][47]['sample_id'],'mode7_sample_object_id':maps['fd_55B3_0EE2'][47]['sample_id']},
                                'active_song_channels_across_all_streams':sorted(active)},
      'limits':['Only SOUND index rows read by OpenIndex and records selected by their kind-12/14 IDs were interpreted.',
                'Every SOUND index flag is checked; compressed records are refused rather than guessed.',
                'The source starts the first event at track 0, uses its seven-entry g_75A4 table, and reuses the descriptor program/bank arrays; event type 7 is reported as unresolved table overread.',
                'Parser dispatch counts are not allocator counts: f_284A_04C9 scales note-on velocity using g_7570 and may route it to f_295C_02E8 instead of f_295C_01EC; runtime volume is unresolved.',
                'Track extents were structurally traversed to EOT; source f_284A_05C5 backs the pointer onto the EOT value, so extent tiling is distinct from post-EOT cursor consumption.',
                'No hardware timing, driver busy transition, actual runtime sequence, or count-39 schedule is inferred.']}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
