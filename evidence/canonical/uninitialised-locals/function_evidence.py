from pathlib import Path
import sys,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import context,functions as fn,exe
r=json.loads((ROOT/'evidence/canonical/uninitialised-locals/census.json').read_text())
code,data=context.name_maps();receipts={}
for name in sorted({x['function'] for x in r['sites']} | {'win_GetObjRect','win_GetObjSize','win_get_obj_layout_rect','gr_BitMapSize','GetMousePos','win_GetEvent','input_pop_event','GetAntIndex','_hanim_FindObject'}):
 try:
  f=fn.get('main' if name=='dos_game_main' else name);base,raw=exe.load().unit_bytes(f['unit']);at=f['seg']*16+f['off']-base
  receipts[name]=dict(address=f"{f['unit']}:{f['seg']:04X}:{f['off']:04X}",extent=f['size'],bytes_sha256=hashlib.sha256(raw[at:at+f['size']]).hexdigest(),frame=context.frame_info(f),instructions=context.annotate(f,code,data))
 except SystemExit as e:receipts[name]=dict(open=str(e))
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(dict(oracle_sha256=exe.EXPECTED_SHA256,functions=receipts),indent=2)+'\n')
print(len(receipts),'function evidence packets')
