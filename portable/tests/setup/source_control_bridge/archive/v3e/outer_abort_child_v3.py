"""Isolated child for the external-longjmp cleanup negative control."""
import importlib.util
import json
from pathlib import Path

runner_path = Path(__file__).with_name("run_native34_v3e.py")
spec = importlib.util.spec_from_file_location("source_control_runner_v3e", runner_path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
dos = json.loads(runner.DOS.read_text(encoding="utf-8"))
row = next(x for x in dos["cases"] if x["kind"] == "mode" and x["code"] == 0x1203)
lib = runner.ct.CDLL(str(runner.DLL))
fn = lib.source_control_native_run
i16p = runner.ct.POINTER(runner.ct.c_int16)
u16p = runner.ct.POINTER(runner.ct.c_uint16)
fn.argtypes = [runner.ct.c_int, runner.ct.c_uint16, runner.ct.c_int16,
               runner.ct.c_int16, runner.ct.c_int16, i16p, u16p,
               i16p, i16p, i16p, runner.ct.c_int, runner.ct.c_int,
               runner.ct.c_int, runner.ct.c_uint16, runner.ct.c_int,
               runner.ct.c_int, runner.ct.POINTER(runner.Result)]
fn.restype = runner.ct.c_int
runner.invoke(fn, row, outer_interrupt_op=1)
