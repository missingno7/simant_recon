"""Disposable build lifecycle. Retired outputs are moved, never erased.

Default runners reuse build/current/<category>. Explicit experiment paths must
be fresh. Every move stays inside the project and is logged in ignored to_delete.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[1]


def _target(path: Path, root: Path) -> tuple[Path, Path]:
    root = root.resolve()
    original = path.absolute()
    resolved = path.resolve()
    relative = resolved.relative_to(root)
    if not relative.parts or relative.parts[0] in {'.git', 'to_delete', 'assets', 'src', 'layout'}:
        raise ValueError('protected retirement target: ' + str(path))
    if relative.parts == ('build',) or relative.parts[:2] == ('build', 'deps'):
        raise ValueError('dependency retirement requires an explicit dependency review')
    # Refuse redirects before moving anything; never operate through a junction.
    current = original
    while current != root:
        if _redirected(current):
            raise ValueError('redirected retirement target: ' + str(current))
        if current == current.parent:
            raise ValueError('retirement target is outside project')
        current = current.parent
    return resolved, relative


def _redirected(path: Path) -> bool:
    if path.is_symlink():
        return True
    # Path.is_junction is unavailable on the supported Python 3.10 runtime.
    try:
        return getattr(path.lstat(), 'st_reparse_tag', None) == getattr(
            stat, 'IO_REPARSE_TAG_MOUNT_POINT', -1)
    except FileNotFoundError:
        return False


def retire(path: Path, root: Path = ROOT) -> Path | None:
    root = root.resolve()
    resolved, relative = _target(path, root)
    if not resolved.exists():
        return None
    category = 'build' if relative.parts[0] == 'build' else 'repo'
    tail = Path(*relative.parts[1:]) if category == 'build' else relative
    destination = root / 'to_delete' / category / tail
    destination.resolve().relative_to(root / 'to_delete')
    destination.parent.mkdir(parents=True, exist_ok=True)
    index = 0
    while destination.exists():
        index += 1
        destination = destination.with_name(tail.name + f'.{index}')
    destination.resolve().relative_to(root / 'to_delete')
    resolved.rename(destination)
    record = {'source': relative.as_posix(),
              'destination': destination.relative_to(root).as_posix()}
    with (root / 'to_delete/moves.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record) + '\n')
    return destination


def prepare_output(path: Path, default: Path, root: Path = ROOT) -> Path:
    root = root.resolve()
    path, _ = _target(path, root)
    default, _ = _target(default, root)
    relative = path.relative_to(root / 'build')
    if not relative.parts or relative.parts[0] == 'deps':
        raise ValueError('output must be a disposable build child')
    if path.exists():
        if path != default:
            raise ValueError('explicit experiment output must be fresh: ' + str(path))
        retire(path, root)
    path.mkdir(parents=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path,
                        help='reviewed project paths to move into to_delete')
    args = parser.parse_args()
    # Validate the entire batch before the first move.
    for path in args.paths:
        _target(path, ROOT)
    for path in args.paths:
        print(retire(path))


if __name__ == '__main__':
    main()
