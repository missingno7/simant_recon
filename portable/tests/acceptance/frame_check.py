"""Exact checkpoint scanout comparison, independent of game-state verdicts.

SAF7: 24 little-endian u32s, 16 attribute bytes, 256 RGB DAC entries,
256 validity bytes, 16 projected RGB8 entries, 32 INT33 mask words, 640x480
4-bit indexed pixels stored one per byte. No pixels are masked.
"""
import hashlib
import json
import struct
from pathlib import Path

HEADER = ('magic width height mode display_start stride pel_panning addr_shift '
          'line_compare plane_enable dac_bits pel_mask color_select attribute_mode '
          'driver_hidden driver_x driver_y driver_hotx driver_hoty driver_inhibit '
          'driver_background driver_page bytes_skip hlines_skip').split()
SIZE = 96+16+768+256+48+64+640*480


def comment_checkpoints(script):
    """First entry after the first command of each comment-delimited section."""
    pending=[];result=[]
    for line in script.splitlines():
        line=line.strip()
        if line.startswith('#'):pending.append(line[1:].strip())
        elif line:
            if pending:
                result.append((int(line.split()[0]),' '.join(pending)))
                pending=[]
    return result


def read_screen(path):
    import numpy as np
    raw=path.read_bytes()
    if len(raw)!=SIZE:raise ValueError('Truncated/oversized checkpoint: '+str(path))
    header=dict(zip(HEADER,struct.unpack('<24I',raw[:96])))
    if (header['magic'],header['width'],header['height'],header['mode'])!=(0x37464153,640,480,0x12):
        raise ValueError('Unsupported checkpoint geometry/mode: '+str(path))
    a=np.frombuffer(raw,dtype=np.uint8)
    if (a[1248:]>=16).any():raise ValueError('Non-planar checkpoint pixel index: '+str(path))
    return dict(header=header,attribute=a[96:112],dac=a[112:880].reshape(256,3),
                valid=a[880:1136],rgb=a[1136:1184].reshape(16,3),
                driver_masks=a[1184:1248],pixels=a[1248:].reshape(480,640))


def frame_manifest(directory,limit,interval,script):
    times=[]
    for line in (directory/'observer.txt').read_text().splitlines():
        p=line.split()
        if p and p[0]=='S':times.append((int(p[3]),float(p[1])))
    comments=[]
    entries={1,limit,*range(interval,limit+1,interval)}
    for ms,text in comment_checkpoints(script):
        entry=next((s for s,t in times if t>=ms),None)
        comments.append(dict(milliseconds=ms,comment=text,entry=entry))
        if entry:entries.add(entry)
    found=sorted(int(p.name.rsplit('.',1)[1]) for p in directory.glob('observer.txt.screen.*'))
    if found!=sorted(entries):raise ValueError('Checkpoint coverage differs: '+str((found,sorted(entries))))
    drivers=[]
    for s in found:
        frame=read_screen(directory/f'observer.txt.screen.{s}')
        h=frame['header']
        if h['driver_background'] or not h['driver_hidden'] and not h['driver_inhibit']:
            raise ValueError('INT33 visible: no corresponding native driver cursor; explicit coverage failure')
        drivers.append(dict(entry=s,**h))
    return dict(contract='indexed-vga-v7',entries=found,interval=interval,comments=comments,
                cursor_rule='Full aperture including game software cursor; INT33 driver hidden/inhibited, checked at every checkpoint; no masks.',
                driver_states=drivers)


def bounding_boxes(mask):
    """Exact bounding extent and per-row runs of changed extents (no masking)."""
    import numpy as np
    ys,xs=np.nonzero(mask)
    if not len(xs):return None,[]
    box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    bands=[]
    for y in np.unique(ys):
        xx=xs[ys==y];span=[int(xx.min()),int(y),int(xx.max()+1),int(y+1)]
        if bands and bands[-1][0]==span[0] and bands[-1][2]==span[2] and bands[-1][3]==span[1]:bands[-1][3]=span[3]
        else:bands.append(span)
    return box,bands


def compare_pair(dos_path,native_path,out,entry):
    import numpy as np
    from PIL import Image
    d,n=read_screen(dos_path),read_screen(native_path)
    changed=d['pixels']!=n['pixels']
    rgb_d=d['rgb'][d['pixels']];rgb_n=n['rgb'][n['pixels']]
    visible=np.any(rgb_d!=rgb_n,axis=2)
    dac=np.flatnonzero(np.any(d['dac']!=n['dac'],axis=1)).tolist()
    rgb=np.flatnonzero(np.any(d['rgb']!=n['rgb'],axis=1)).tolist()
    attr=np.flatnonzero(d['attribute']!=n['attribute']).tolist()
    bounds,bands=bounding_boxes(changed)
    vb,_=bounding_boxes(visible)
    row=dict(entry=entry,pixel_count=int(changed.sum()),bounding_box=bounds,bounding_boxes=bands,
             visible_pixel_count=int(visible.sum()),visible_bounding_box=vb,palette_indices=dac,
             projected_palette_indices=rgb,attribute_indices=attr,
             native_unwritten_dac_indices=np.flatnonzero(n['valid']==0).tolist())
    row['status']='FRAME_DIFFERENCE' if row['pixel_count'] or dac or rgb or attr else 'FRAME_EQUAL'
    if row['status']=='FRAME_DIFFERENCE':
        # A DAC-only difference still writes a review triple; amber marks
        # index-only differences, magenta marks a rendered RGB difference.
        diff=np.zeros((480,640,3),dtype=np.uint8)
        diff[changed]=[255,192,0];diff[visible]=[255,0,255]
        names=[]
        for suffix,array in [('dos',rgb_d),('native',rgb_n),('diff',diff)]:
            path=out/f'frame-{entry:05d}-{suffix}.png'
            Image.fromarray(array).save(path,compress_level=1);names.append(path.name)
        row['png_triple']=names
    row['dos_sha256']=hashlib.sha256(dos_path.read_bytes()).hexdigest()
    row['native_sha256']=hashlib.sha256(native_path.read_bytes()).hexdigest()
    return row


def compare_frames(reference,out,entries):
    rows=[];missing=[]
    for s in entries:
        path=out/f'native.screen.{s}'
        if path.is_file():rows.append(compare_pair(reference/'capture'/f'observer.txt.screen.{s}',path,out,s))
        else:missing.append(s)
    first=next((r for r in rows if r['status']!='FRAME_EQUAL'),None)
    result=dict(status='FRAME_DIFFERENCE' if first else 'FRAME_INCOMPLETE' if missing else 'FRAME_EQUAL',
                frames_compared=len(rows),requested_frames=len(entries),first_differing_entry=first['entry'] if first else None,
                missing_entries=missing,rows=rows,cursor_rule='include game cursor; INT33 hidden/inhibited; no masking')
    (out/'frames.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def frame_signature(frames):
    first=next((r for r in frames['rows'] if r['status']!='FRAME_EQUAL'),None)
    return dict(status=frames['status'],frames_compared=frames['frames_compared'],
                replay_complete=frames['replay_complete'],
                native_host_cursor_visible=frames.get('native_host_cursor_visible',[]),
                checkpoint_digest=hashlib.sha256(json.dumps(frames['rows'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                requested_frames=frames['requested_frames'],missing_entries=frames['missing_entries'],
                first={k:first[k] for k in ('entry','pixel_count','bounding_box','visible_pixel_count','palette_indices','projected_palette_indices','attribute_indices')} if first else None)
