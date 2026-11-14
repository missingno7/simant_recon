"""Optional Windows instruction-pointer sampler for a joined native child.

Suspend only while copying the context; always resume in finally. No guest
memory is written. Samples include waits, so percentages are wall samples.
"""
import ctypes as C
from ctypes import wintypes as W
import json
import struct
import subprocess
import threading
import time
from collections import Counter


def sampled_run(command, cwd, env, log, timeout, destination):
    k = C.WinDLL('kernel32', use_last_error=True)
    for name in ('CreateToolhelp32Snapshot', 'OpenThread'):
        getattr(k, name).restype = W.HANDLE
    k.OpenThread.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.CloseHandle.argtypes = [W.HANDLE]
    k.SuspendThread.argtypes = k.ResumeThread.argtypes = [W.HANDLE]
    k.GetThreadContext.argtypes = [W.HANDLE, C.c_void_p]
    class ThreadEntry(C.Structure):
        _fields_ = [(n, W.DWORD) for n in ('size', 'usage', 'tid', 'pid', 'priority', 'delta', 'flags')]
    class ModuleEntry(C.Structure):
        _fields_ = [('size', W.DWORD), ('id', W.DWORD), ('pid', W.DWORD),
                    ('global_usage', W.DWORD), ('usage', W.DWORD), ('base', C.c_void_p),
                    ('bytes', W.DWORD), ('module', W.HMODULE), ('name', W.WCHAR*256), ('path', W.WCHAR*260)]
    samples = Counter(); errors = Counter(); modules = []
    stop = threading.Event()
    with subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT) as child:
        def sample():
            handle = None
            try:
                # The loader must publish the module list before Toolhelp can
                # snapshot it (Popen returns before process initialization).
                stop.wait(.1)
                snap = k.CreateToolhelp32Snapshot(8 | 16, child.pid)
                entry = ModuleEntry(); entry.size = C.sizeof(entry)
                if k.Module32FirstW(snap, C.byref(entry)):
                    while True:
                        modules.append(dict(name=entry.name, base=entry.base, size=entry.bytes, path=entry.path))
                        if not k.Module32NextW(snap, C.byref(entry)): break
                k.CloseHandle(snap)
                snap = k.CreateToolhelp32Snapshot(4, 0)
                entry = ThreadEntry(); entry.size = C.sizeof(entry)
                if k.Thread32First(snap, C.byref(entry)):
                    while True:
                        if entry.pid == child.pid:
                            handle = k.OpenThread(0x0002 | 0x0008 | 0x0040, False, entry.tid)
                            break
                        if not k.Thread32Next(snap, C.byref(entry)): break
                k.CloseHandle(snap)
                if not handle: errors['open_thread'] += 1; return
                # AMD64 CONTEXT is 1232 bytes, aligned to 16; Rip offset 248.
                raw = C.create_string_buffer(1248)
                address = (C.addressof(raw)+15) & ~15
                while not stop.wait(.01):
                    C.memset(address, 0, 1232)
                    C.c_uint32.from_address(address+48).value = 0x100001
                    if k.SuspendThread(handle) == 0xffffffff: break
                    try:
                        if k.GetThreadContext(handle, address):
                            samples[C.c_uint64.from_address(address+248).value] += 1
                        else: errors['context'] += 1
                    finally: k.ResumeThread(handle)
            finally:
                if handle: k.CloseHandle(handle)
        worker = threading.Thread(target=sample)
        worker.start()
        try:
            code = child.wait(timeout=timeout)
        except BaseException:
            child.kill(); child.wait(); raise
        finally:
            stop.set(); worker.join()
            destination.write_text(json.dumps(dict(interval_seconds=.01, samples={hex(pc): n for pc,n in samples.items()},
                                                   modules=modules, errors=dict(errors)), indent=2)+'\n')
    return code
