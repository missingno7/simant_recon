"""Single-writer lock for canonical files (manifest, sources, registries).

Every tool that rewrites a tracked layout/source file takes this lock.  It waits
(up to ``timeout`` seconds) instead of failing, so concurrent workers serialise.
A stale lock (holder PID gone) is broken automatically.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "build" / "canonical.lock"


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259  # STILL_ACTIVE
    except Exception:  # noqa: BLE001
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def atomic_write_text(path, text: str, attempts: int = 50, newline: str | None = None) -> None:
    """Write via a temp file and os.replace, retrying while a concurrent reader holds the
    target open (Windows PermissionError); never leaves a partial target or a stray temp."""
    import os
    import time
    from pathlib import Path
    path = Path(path)
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(text, newline=newline)
    for i in range(attempts):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05 * (i + 1))
    tmp.unlink(missing_ok=True)
    raise PermissionError(f"could not replace {path}")


class CanonicalLock:
    def __init__(self, timeout: float = 900.0):
        self.timeout = timeout
        self.fd = None
        self.depth = 0

    def __enter__(self):
        if os.environ.get("SIMANT_CANONICAL_LOCK_HELD") == str(os.getpid()):
            return self            # re-entrant within one process
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()
        while True:
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                os.environ["SIMANT_CANONICAL_LOCK_HELD"] = str(os.getpid())
                return self
            except FileExistsError:
                try:
                    pid = int(LOCK.read_text().strip() or 0)
                except (OSError, ValueError):
                    pid = 0
                if pid and not _alive(pid):
                    LOCK.unlink(missing_ok=True)
                    continue
                if time.time() - start > self.timeout:
                    raise SystemExit(f"timed out waiting for {LOCK} (held by pid {pid})")
                time.sleep(0.5)

    def __exit__(self, *a):
        if self.fd is not None:
            os.close(self.fd)
            LOCK.unlink(missing_ok=True)
            os.environ.pop("SIMANT_CANONICAL_LOCK_HELD", None)
            self.fd = None
