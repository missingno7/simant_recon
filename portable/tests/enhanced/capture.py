"""Capture actual native-world scenarios and make phone-sized review PNGs.

Only ordinary replay input and the existing N05 semantic action are used.
Scent setup retains the hybrid control until the original proximity selection
finishes; the test-only wrapper then enables the native view. No game writes.
"""
from pathlib import Path
import argparse,concurrent.futures,json,os,re,shutil,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from portable.tests.enhanced.common import check_build,probe_link

def scenario(build,exe,out,name,script,ms,mode='native',scale=1):
    d=out/name;d.mkdir();(d/'input.txt').write_text(script)
    env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_TEST_'))}
    env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_TEST=mode)
    if name=='speech':env['SIMANT_ENHANCED_CAPTURE']=str(d/'selected.bmp')
    if name=='spider':env['SIMANT_ENHANCED_DUMP_ASSETS']=str(d/'catalog.bin')
    scratch=ROOT/'build/workers/enhanced-menus/temporary';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='p1',dir=scratch) as folder:
        shutil.copytree(build/'runtime-assets',folder,dirs_exist_ok=True)
        cmd=[str(exe),'--headless','--deterministic','--windows','--scale='+str(scale),'--seed','0',
            '--assets',folder,'--input-script',str(d/'input.txt'),'--smoke-ms',str(ms),
            '--frame',str(d/'frame.bmp'),'--diagnostics-dir',str(d/'diagnostics')]
        process=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=180)
    log=(process.stdout+process.stderr).decode(errors='replace');(d/'run.log').write_text(log)
    scene=re.findall(r'^ENHANCED_SCENE (.*)$',log,re.M);capture=re.findall(r'^ENHANCED_CAPTURE (.*)$',log,re.M)
    scent=re.findall(r'^ENHANCED_SCENT (.*)$',log,re.M)
    if process.returncode or not scene or 'Source-main smoke frame captured;' not in log:raise RuntimeError(name+' incomplete; see '+str(d/'run.log'))
    return dict(name=name,code=process.returncode,scene=json.loads(scene[-1]),capture=json.loads(capture[-1]),scent=json.loads(scent[-1]),command=cmd)

def phone(path,out,title):
    from PIL import Image,ImageDraw,ImageFont
    image=Image.open(path).convert('RGB');height=round(image.height*1280/image.width)
    canvas=Image.new('RGB',(1280,height+72),(22,27,32));canvas.paste(image.resize((1280,height),Image.Resampling.NEAREST),(0,72))
    draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',30)
    draw.text((20,18),title,fill='white',font=font);canvas.save(out)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--regressions',type=Path,required=True)
    a=p.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    check_build(build);exe=probe_link(build,out/'probe');quick=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text()
    large='17000 size@0000 1280 720\n'
    surface=quick+'15000 menu FD26\n16000 menu FD41\n'+large
    black=quick+'16000 menu FD41\n'+large
    red=quick+'15000 menu FD28\n16000 menu FD41\n'+large
    spider=quick+'24000 menu FD41\n'
    scent=quick+'15000 menu FD26\n16000 move@0000 24 150\n16100 mouse-down@0000 Left 24 150\n17000 move@0600 40 45\n17200 mouse-up@0600 Left 40 45\n18000 menu FD41\n18300 size@0000 1280 720\n'
    speech=quick+'15000 menu FD36\n35000 menu FD41\n'
    cases=[('surface-100',surface,19000,'native',1),('surface-300',surface+'18000 wheel@0000 640 360 2\n',19000,'native',1),
        ('black-nest',black,19000,'native',1),('red-nest',red,19000,'native',1),('spider',spider,25000,'spider',2),
        ('speech',speech,36000,'spider',2),('scent',scent,19500,'scent',1)]
    for name,cmd in [('yard',0xfd21),('house',0xfd22),('strategic',0xfd23),('graphic',0xfd24)]:
        cases.append((name,quick+f'16000 menu {cmd:04X}\n18000 menu FD41\n',19500,'native',2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows=list(pool.map(lambda c:scenario(build,exe,out,*c),cases))
    by_name={r['name']:r for r in rows}
    assert by_name['surface-100']['scene']['plane']==1 and by_name['surface-300']['scene']['plane']==1
    assert by_name['black-nest']['scene']['plane']==2 and by_name['red-nest']['scene']['plane']==3
    assert by_name['spider']['scene']['art'] and by_name['spider']['scene']['lines']
    assert by_name['speech']['capture']['captured']==1
    assert by_name['scent']['scene']['layer']>=0 and by_name['scent']['scent']['changed_surface_cells']>0
    assert by_name['yard']['scene']['yard_actors']>0
    from portable.tests.enhanced.assets import compare
    assets=compare(out/'spider/catalog.bin');(out/'assets.json').write_text(json.dumps(assets,indent=2)+'\n')
    screens=out.parent/'screens';screens.mkdir(exist_ok=True)
    captions={
        'surface-100':'Surface at 100% (16 px cells before phone scaling).',
        'surface-300':'The same surface at 300% nearest-neighbor zoom.',
        'black-nest':'Black nest, native terrain and ant imagery.',
        'red-nest':'Red nest, native terrain and ant imagery.',
        'spider':'Source-selected spider body, legs and palps.',
        'speech':'Actual source-selected spider speech; Silly enabled through FD36.',
        'scent':'Black-nest scent selected through the original proximity menu.',
        'yard':'Yard art and source-selected animated actors.',
        'house':'House world art and source-selected actors.',
        'strategic':'Native strategic yard projection from published populations.',
        'graphic':'Native graphic yard view from published populations.'}
    for name,caption in captions.items():
        frame=out/name/('selected.bmp.0000.bmp' if name=='speech' else 'frame.bmp.1900.bmp' if name in ('yard','house','strategic','graphic') else 'frame.bmp.0000.bmp')
        phone(frame,screens/(name+'.png'),caption)
    regress=a.regressions.resolve();result=json.loads((regress/'result.json').read_text())
    assert result['checks']['rebirth_semantic_world_equal']
    for name,folder,title in [('before-hybrid','rebirth-hybrid','Before: hybrid at the music-enabled rebirth wait'),('after-native','rebirth','After: native view at the identical semantic world')]:
        phone(regress/folder/'frame.bmp.0000.bmp',screens/(name+'.png'),title)
        captions[name]=title+'.'
    from PIL import Image,ImageDraw,ImageFont
    world=Image.open(regress/'rebirth/frame.bmp.0000.bmp').convert('RGB');dialog=Image.open(regress/'rebirth/frame.bmp.1A00.bmp').convert('RGB')
    canvas=Image.new('RGB',(1280,820),(22,27,32));draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28)
    draw.text((20,18),'Rebirth wait: native ants remain visible; source dialog is open',fill='white',font=font)
    canvas.paste(world.resize((860,round(world.height*860/world.width)),Image.Resampling.NEAREST),(10,88))
    canvas.paste(dialog.resize((384,round(dialog.height*384/dialog.width)),Image.Resampling.NEAREST),(884,88))
    draw.text((884,420),'Active source dialog',fill='white',font=font);canvas.save(screens/'rebirth-dialog.png')
    captions['rebirth-dialog']='Simultaneous native world and active source dialog, placed side by side for phone review.'
    (screens/'README.md').write_text('# Phase 1 captures\n\nActual renderer readbacks, normalized to 1280 px wide with nearest-neighbor phone scaling. Titles are review annotations. The rebirth composite places two simultaneous surfaces side by side; it is not a desktop screenshot. Dialog presentation remains phase 5. No game pixels are tracked in git.\n\n'+''.join(f'- [{name}.png]({name}.png) — {caption}\n' for name,caption in captions.items())+f'\nRecipes, source preconditions and executable identity: `../{out.name}/result.json`.\n',encoding='utf-8')
    (out/'result.json').write_text(json.dumps(dict(passed=True,cases=rows,assets=assets,rebirth_same_world=True,surface_zoom_same_world=by_name['surface-100']['scene']['world_hash']==by_name['surface-300']['scene']['world_hash']),indent=2)+'\n')
    print(json.dumps(dict(passed=True,screens=str(screens),cases=len(rows),assets=assets)))
if __name__=='__main__':main()

