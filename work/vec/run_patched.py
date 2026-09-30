"""Run a tool with the patched match.py/modules.py preloaded: python run_patched.py tools/search.py ARGS..."""
import sys, runpy, importlib.util
from pathlib import Path
here = Path(__file__).resolve().parent
repo = here.parents[2]
sys.path.insert(0, str(repo / 'tools'))
for name in ('match', 'modules'):
    spec = importlib.util.spec_from_file_location(name, here / 'patched' / 'tools' / f'{name}.py')
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
script = sys.argv[1]; sys.argv = sys.argv[1:]
runpy.run_path(str(repo / script), run_name='__main__')
