"""Run a fresh research candidate without overwriting the frozen v19 receipt."""
import importlib.util
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
import source_only_dos

denied = source_only_dos.install_input_guard()
worker = ROOT/'build/workers'
worker.mkdir(parents=True, exist_ok=True)
output = Path(tempfile.mkdtemp(prefix='dos_fheap_debt_replay-', dir=worker))
spec = importlib.util.spec_from_file_location('fheap_research', Path(__file__).with_name('probe-original.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.OUT = output
module.main()
if denied:
    raise RuntimeError('Research replay attempted denied original-image reads')
print('Fresh unadmitted research output:', output)
