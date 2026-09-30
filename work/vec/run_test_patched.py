"""Run patched tests/test_data_gates.py against patched match/modules (repo state otherwise)."""
import sys, importlib.util, unittest
from pathlib import Path
here = Path(__file__).resolve().parent; repo = here.parents[2]
sys.path.insert(0, str(repo / 'tools')); sys.path.insert(0, str(repo / 'tests'))
for name in ('match', 'modules'):
    spec = importlib.util.spec_from_file_location(name, here / 'patched' / 'tools' / f'{name}.py')
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
spec = importlib.util.spec_from_file_location('test_data_gates', here / 'patched' / 'tests' / 'test_data_gates.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(t))
sys.exit(not r.wasSuccessful())
