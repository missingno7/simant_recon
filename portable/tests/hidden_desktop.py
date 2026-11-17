"""Fail-closed Windows test desktop. No SwitchDesktop or screen capture.

Use: python portable/tests/hidden_desktop.py RUNNER.py [arguments...]
All subprocesses inherit the private desktop, including nested test runners.
Enhanced runners also install this policy through their common module.
"""
import atexit
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import time
import uuid

_installed = False


def _desktop_name(u):
    """Name of the calling thread's desktop."""
    buf = C.create_unicode_buffer(256); needed = W.DWORD()
    u.GetThreadDesktop.restype = W.HANDLE
    if not u.GetUserObjectInformationW(W.HANDLE(u.GetThreadDesktop(C.windll.kernel32.GetCurrentThreadId())), 2, buf,
                                       C.sizeof(buf), C.byref(needed)):
        raise OSError(C.get_last_error(), 'Cannot read the current desktop name')
    return buf.value


def _relaunch_on_private_desktop(u):
    """Run this same Python command again on a new private desktop and exit with its code.

    CPython's subprocess ignores STARTUPINFO.lpDesktop, so a child started through it lands on the
    parent's (visible) desktop. The relaunched process is created with CreateProcessW and
    lpDesktop; everything it starts inherits that desktop. All of its processes run in a
    kill-on-close job. While it runs, any window of a job process on the input desktop is a
    violation: the job is terminated and this process exits 97.
    """
    k = C.WinDLL('kernel32', use_last_error=True)

    class StartupInfo(C.Structure):
        _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR), ('lpDesktop', W.LPWSTR), ('lpTitle', W.LPWSTR),
                    ('dwX', W.DWORD), ('dwY', W.DWORD), ('dwXSize', W.DWORD), ('dwYSize', W.DWORD),
                    ('dwXCountChars', W.DWORD), ('dwYCountChars', W.DWORD), ('dwFillAttribute', W.DWORD),
                    ('dwFlags', W.DWORD), ('wShowWindow', W.WORD), ('cbReserved2', W.WORD),
                    ('lpReserved2', C.c_void_p), ('hStdInput', W.HANDLE), ('hStdOutput', W.HANDLE),
                    ('hStdError', W.HANDLE)]

    class ProcessInformation(C.Structure):
        _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE), ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]

    class BasicLimits(C.Structure):
        _fields_ = [('PerProcessUserTimeLimit', C.c_int64), ('PerJobUserTimeLimit', C.c_int64),
                    ('LimitFlags', W.DWORD), ('MinimumWorkingSetSize', C.c_size_t),
                    ('MaximumWorkingSetSize', C.c_size_t), ('ActiveProcessLimit', W.DWORD),
                    ('Affinity', C.c_size_t), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]

    class ExtendedLimits(C.Structure):
        _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', C.c_uint64 * 6),
                    ('ProcessMemoryLimit', C.c_size_t), ('JobMemoryLimit', C.c_size_t),
                    ('PeakProcessMemoryUsed', C.c_size_t), ('PeakJobMemoryUsed', C.c_size_t)]

    u.CreateDesktopW.argtypes = [W.LPCWSTR, W.LPCWSTR, C.c_void_p, W.DWORD, W.DWORD, C.c_void_p]
    u.CreateDesktopW.restype = W.HANDLE
    u.OpenInputDesktop.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    u.OpenInputDesktop.restype = W.HANDLE
    u.CloseDesktop.argtypes = [W.HANDLE]
    callback = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    u.EnumDesktopWindows.argtypes = [W.HANDLE, callback, W.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
    k.CreateJobObjectW.restype = W.HANDLE
    k.CreateJobObjectW.argtypes = [C.c_void_p, W.LPCWSTR]
    k.SetInformationJobObject.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD]
    k.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
    k.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
    k.IsProcessInJob.argtypes = [W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)]
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]; k.OpenProcess.restype = W.HANDLE
    k.CloseHandle.argtypes = [W.HANDLE]
    k.GetStdHandle.restype = W.HANDLE
    k.SetHandleInformation.argtypes = [W.HANDLE, W.DWORD, W.DWORD]
    k.CreateProcessW.argtypes = [W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD, C.c_void_p,
                                 W.LPCWSTR, C.POINTER(StartupInfo), C.POINTER(ProcessInformation)]
    k.ResumeThread.argtypes = [W.HANDLE]
    k.TerminateProcess.argtypes = [W.HANDLE, W.UINT]
    k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]; k.WaitForSingleObject.restype = W.DWORD
    k.GetExitCodeProcess.argtypes = [W.HANDLE, C.POINTER(W.DWORD)]

    name = 'SimAntTests_' + uuid.uuid4().hex
    desktop = u.CreateDesktopW(name, None, None, 0, 0x01ff, None)
    if not desktop:
        raise OSError(C.get_last_error(), 'CreateDesktop failed; visible fallback forbidden')
    job = k.CreateJobObjectW(None, None)
    limits = ExtendedLimits(); limits.BasicLimitInformation.LimitFlags = 0x2000   # KILL_ON_JOB_CLOSE
    if not job or not k.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)):
        raise OSError(C.get_last_error(), 'Cannot create the test job')
    os.environ['SIMANT_TEST_DESKTOP'] = name
    si = StartupInfo(); si.cb = C.sizeof(si); si.lpDesktop = 'winsta0\\' + name; si.dwFlags = 0x100  # USESTDHANDLES
    handles = [k.GetStdHandle(n) for n in (-10, -11, -12)]
    for h in handles:
        if h and h != W.HANDLE(-1).value:
            k.SetHandleInformation(h, 1, 1)
    si.hStdInput, si.hStdOutput, si.hStdError = handles
    sys.stdout.flush(); sys.stderr.flush()
    command = C.create_unicode_buffer(subprocess.list2cmdline([sys.executable, *sys.orig_argv[1:]]))
    pi = ProcessInformation()
    if not k.CreateProcessW(None, command, None, None, True, 0x08000000 | 0x4, None, None, C.byref(si), C.byref(pi)):
        raise OSError(C.get_last_error(), 'CreateProcess on the private desktop failed; visible fallback forbidden')
    if not k.AssignProcessToJobObject(job, pi.hProcess):
        error = C.get_last_error(); k.TerminateProcess(pi.hProcess, 99)
        raise OSError(error, 'Cannot place the test process in its job')
    k.ResumeThread(pi.hThread)

    def windows_on_input_desktop():
        found, membership = [], {}
        screen = u.OpenInputDesktop(0, False, 0x0041)
        if not screen:
            raise OSError(C.get_last_error(), 'Cannot audit the input desktop')

        @callback
        def visit(hwnd, unused):
            pid = W.DWORD(); u.GetWindowThreadProcessId(hwnd, C.byref(pid))
            if pid.value not in membership:
                inside = W.BOOL(False); h = k.OpenProcess(0x1000, False, pid.value)
                if h:
                    k.IsProcessInJob(h, job, C.byref(inside)); k.CloseHandle(h)
                membership[pid.value] = bool(inside.value)
            if membership[pid.value]:
                found.append((pid.value, int(hwnd)))
            return True
        try:
            u.EnumDesktopWindows(screen, visit, 0)
        finally:
            u.CloseDesktop(screen)
        return found

    violations = []
    while k.WaitForSingleObject(pi.hProcess, 25) == 0x102:   # WAIT_TIMEOUT
        violations = windows_on_input_desktop()
        if violations:
            k.TerminateJobObject(job, 97)
            break
    k.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)
    code = W.DWORD(); k.GetExitCodeProcess(pi.hProcess, C.byref(code))
    k.TerminateJobObject(job, 98)   # descendants left behind by the runner
    for h in (pi.hThread, pi.hProcess, job):
        k.CloseHandle(h)
    u.CloseDesktop(desktop)
    if violations:
        sys.stderr.write('Test process window appeared on the input desktop: %r\n' % violations)
        os._exit(97)
    os._exit(code.value)


def install():
    global _installed
    if _installed:
        return
    if os.name != 'nt':
        raise RuntimeError('Private Windows desktop unavailable; skip GUI registration. Visible fallback forbidden.')
    _installed = True
    u = C.WinDLL('user32', use_last_error=True)
    inherited = os.environ.get('SIMANT_TEST_DESKTOP')
    if not inherited:
        _relaunch_on_private_desktop(u)   # does not return
    if _desktop_name(u) != inherited:
        raise RuntimeError('Not on the private test desktop %r; visible fallback forbidden' % inherited)
    u.CreateDesktopW.argtypes = [W.LPCWSTR, W.LPCWSTR, C.c_void_p, W.DWORD, W.DWORD, C.c_void_p]
    u.CreateDesktopW.restype = W.HANDLE
    u.OpenInputDesktop.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    u.OpenInputDesktop.restype = W.HANDLE
    u.CloseDesktop.argtypes = [W.HANDLE]
    callback = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    u.EnumDesktopWindows.argtypes = [W.HANDLE, callback, W.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
    k = C.WinDLL('kernel32', use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD]
    k.CreateToolhelp32Snapshot.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
    class ProcessEntry(C.Structure):
        _fields_=[('size',W.DWORD),('usage',W.DWORD),('pid',W.DWORD),('heap',C.c_size_t),
                  ('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),
                  ('priority',W.LONG),('flags',W.DWORD),('exe',W.WCHAR*260)]
    k.Process32FirstW.argtypes=k.Process32NextW.argtypes=[W.HANDLE,C.POINTER(ProcessEntry)]
    # A child Python runner reuses the private desktop; it still audits its children.
    inherited = os.environ.get('SIMANT_TEST_DESKTOP')
    name = inherited or ('SimAntTests_' + uuid.uuid4().hex)
    desktop = None if inherited else u.CreateDesktopW(name, None, None, 0, 0x01ff, None)
    if not inherited and not desktop:
        raise OSError(C.get_last_error(), 'CreateDesktop failed; visible fallback forbidden')
    os.environ['SIMANT_TEST_DESKTOP'] = name
    original = subprocess.Popen
    children, records, violations = {}, [], []
    lock, stop = threading.RLock(), threading.Event()
    descendants={}
    descendant_log={}

    def created(pid):
        handle=k.OpenProcess(0x1000,False,pid)
        if not handle:return None
        times=[W.FILETIME() for _ in range(4)]
        try:
            if not k.GetProcessTimes(handle,*[C.byref(t) for t in times]):return None
            return (times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
        finally:k.CloseHandle(handle)

    def process_tree():
        with lock:return process_tree_locked()

    def process_tree_locked():
        snap=k.CreateToolhelp32Snapshot(2,0)
        if snap==C.c_void_p(-1).value:raise OSError(C.get_last_error(),'Cannot audit test descendants')
        parents={};names={};entry=ProcessEntry();entry.size=C.sizeof(entry)
        try:
            okay=k.Process32FirstW(snap,C.byref(entry))
            while okay:
                parents[entry.pid]=entry.parent
                names[entry.pid]=entry.exe
                okay=k.Process32NextW(snap,C.byref(entry))
        finally:k.CloseHandle(snap)
        with lock:roots={pid for pid,child in children.items() if child.poll() is None}
        identities={pid:created(pid) for pid in (roots|descendants.keys())&parents.keys()}
        selected={pid for pid in identities if identities[pid] is not None and (pid in roots or descendants.get(pid)==identities[pid])}
        while True:
            more={pid for pid,parent in parents.items() if parent in selected}-selected
            if not more:break
            added=set()
            for pid in more:
                stamp=created(pid)
                # A stale system-process parent PID can be reused by a compiler.
                # An older process is never that compiler's descendant.
                if stamp is not None and stamp>=identities[parents[pid]]:
                    identities[pid]=stamp;added.add(pid)
            if not added:break
            selected.update(added)
        descendants.clear();descendants.update({pid:identities[pid] for pid in selected})
        descendant_log.update({pid:dict(pid=pid,created=identities[pid],name=names.get(pid)) for pid in selected})
        return selected

    def audit():
        tested=process_tree()
        input_desktop = u.OpenInputDesktop(0, False, 0x0041)
        if not input_desktop:
            raise OSError(C.get_last_error(), 'Cannot audit input desktop')
        found = []
        @callback
        def visit(hwnd, unused):
            pid = W.DWORD()
            u.GetWindowThreadProcessId(hwnd, C.byref(pid))
            with lock:
                if pid.value in tested:
                    found.append((pid.value, int(hwnd)))
            return True
        try:
            if not u.EnumDesktopWindows(input_desktop, visit, 0):
                raise OSError(C.get_last_error(), 'EnumDesktopWindows failed')
        finally:
            u.CloseDesktop(input_desktop)
        if found:
            violations.extend(found)
            with lock:
                for pid, hwnd in found:
                    if pid in children and children[pid].poll() is None:children[pid].kill()
            raise RuntimeError('Test process window appeared on input desktop: ' + repr(found))

    audit()  # Prove enumeration works before allowing any child to start.

    class HiddenPopen(original):
        def __init__(self, *args, **kwargs):
            startup = kwargs.get('startupinfo') or subprocess.STARTUPINFO()
            startup.lpDesktop = 'winsta0\\' + name
            kwargs['startupinfo'] = startup
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
            with lock:
                children[self.pid] = self
                records.append(dict(pid=self.pid, command=str(args[0] if args else kwargs.get('args')), desktop=name))
            audit()

        def wait(self, *args, **kwargs):
            result = super().wait(*args, **kwargs)
            audit()
            return result

    subprocess.Popen = HiddenPopen

    def monitor():
        while not stop.wait(.025):
            try:
                audit()
            except Exception as error:
                violations.append(str(error))
                with lock:
                    for child in children.values():
                        if child.poll() is None:
                            child.kill()
                return

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

    def close():
        stop.set()
        thread.join()
        with lock:
            for child in children.values():
                if child.poll() is None:
                    child.kill()
                original.wait(child)
        try:audit()
        except Exception as error:violations.append(str(error))
        remaining=process_tree()
        # Every direct child has joined. Reap only a proven, still-identical
        # descendant left behind by a failing runner (never by image name).
        k.TerminateProcess.argtypes=[W.HANDLE,W.UINT]
        k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]
        for pid in remaining:
            stamp=descendants[pid]
            handle=k.OpenProcess(0x1000|0x100000|1,False,pid)
            if handle:
                try:
                    if created(pid)==stamp:k.TerminateProcess(handle,98);k.WaitForSingleObject(handle,5000)
                finally:k.CloseHandle(handle)
        destination = os.environ.get('SIMANT_DESKTOP_AUDIT')
        if destination:
            Path(destination).write_text(json.dumps(dict(desktop=name, passed=not violations,
                input_desktop_violations=violations, processes=records, descendants=list(descendant_log.values()),
                reaped_descendants=sorted(remaining),all_joined=not process_tree()), indent=2)+'\n')
        if desktop:
            u.CloseDesktop(desktop)
        if violations:
            os._exit(97)
    atexit.register(close)


if __name__ == '__main__':
    sys.modules['portable.tests.hidden_desktop']=sys.modules[__name__]
    install()
    script, *arguments = sys.argv[1:]
    script = str(Path(script).resolve())
    sys.argv = [script, *arguments]
    sys.path.insert(0, str(Path(script).resolve().parent))
    runpy.run_path(script, run_name='__main__')
