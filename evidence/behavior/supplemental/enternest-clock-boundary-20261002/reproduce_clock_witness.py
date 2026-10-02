from pathlib import Path
import argparse, importlib.util, json, sys, struct, hashlib
ROOT=Path(__file__).resolve().parents[4]
archive=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument("--out",default="build/workers/behavior_sim_contracts/20261002/replayed-clock-witness-next",help="new output directory relative to repository root")
args=parser.parse_args()
out=(ROOT/args.out).resolve()
out.relative_to(ROOT/"build/workers/behavior_sim_contracts/20261002")
if out.exists(): raise SystemExit(f"refusing to overwrite existing replay directory: {out}")
# Bootstrap the workspace runtime first so cached symbols, executable identity,
# and paths resolve against the real repo. Then prove every companion source is
# byte-identical to the preserved bundle before loading its archived runner.
sys.path.insert(0,str(ROOT/"build/behavior/deps"))
sys.path.insert(0,str(ROOT/"tools"))
import behavior as current_behavior
import behavior_validate
identity=json.loads((archive/"clock-witness-report.json").read_text())["identity"]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(ROOT/"tools/behavior.py")==identity["harness_sha256"], "workspace runner differs from execution pin"
assert sha(archive/"harness/tools/behavior.py")==identity["harness_sha256"]
assert sha(ROOT/"tools/behavior_suites/spider_nest.py")==sha(archive/"suite/spider_nest.py"), "workspace suite differs from archived suite"
for rel in behavior_validate.HARNESS_COMPONENTS:
 current=ROOT/rel; saved=archive/"harness"/rel
 assert current.is_file() and saved.is_file() and sha(current)==sha(saved), f"workspace companion differs from archived component: {rel}"
# The cached current companions now have workspace roots and are byte-verified
# against the archived inputs. Load the exact archived behavior module under a
# unique import name, then publish it as `behavior` for the archived suite.
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
behavior=load("behavior_clock_snapshot",archive/"harness/tools/behavior.py")
behavior.ROOT=ROOT
sys.modules["behavior"]=behavior
behavior_ledger=load("behavior_ledger_clock_snapshot",archive/"harness/tools/behavior_ledger.py")
spider_nest=load("spider_nest",archive/"suite/spider_nest.py")
assert sha(archive/"suite/spider_nest.py")=="41fa2c46acdc8c74d033d07d4d2afcf13abd77cd9cdee80e5060a61649aa8f67"
out.mkdir(parents=True)
pair=behavior.PreparedPair("o25_3BA4_1035",source=archive/"source/EnterNest-module.c",out=out/"prepared")
helpers=("ClearMyLife","SetMyLife","DigMyTile","TryAntTheme","SetAlarmDropState")
timer=behavior.symbol_address("fd_50F6_0214")
effects=["return value","declared global/array/map state","ordered helper/callback names and arguments","final bytes across union of non-stack writes","caller-preserved register and stack ABI"]
ledger=behavior_ledger.CaseLedger(out/"clock-cases.jsonl.gz",pair,effects);rows=[]
for now in (7199,7200):
 case=next(c for c in spider_nest.make_cases("o25_3BA4_1035",directed=True,random_count=0,original_helpers=helpers) if c.label=="plane2-x-1-y0-type08")
 case.label=f"enter-clock-boundary-now-{now}";case.state["tick"]=now-37;case.writes.append((timer,struct.pack("<H",0)));case.metadata["domain"]["tick_now"]=now;case.metadata["domain"]["last_theme_tick"]=0
 result=pair.compare(case);record=ledger.record(case,result,lane="directed");events=result.original["trace"];names=[event["name"] for event in events]
 assert result.equal and (("myBeginSong" in names)==(now>=7200))
 rows.append({"case_id":case.label,"equal":result.equal,"input_sha256":record["input_sha256"],"observation_sha256":record["original_observation_sha256"],"calls":events,"song_count":names.count("myBeginSong"),"song_request_role":"bounded modeled audio-intent notification; only request/call order is asserted"})
ledger_result=ledger.finalize()
ledger_result["path"]=(out/"clock-cases.jsonl.gz").relative_to(ROOT).as_posix()
report={"schema":"EnterNest-clock-boundary-replay-v1","identity":pair.identity,"cases":rows,"ledger":ledger_result,"companion_checks":"PASS: all current HARNESS_COMPONENTS byte-equal archived pins before archived runner load"}
(out/"clock-replay-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
