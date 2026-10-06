# Filename storage: real DOS path boundary

The canonical filename import remains unresolved. A DOS 8.3 directory name
alone does not ensure that `FileSelect`'s `path[67]` stays in bounds.

The source-built fixture links the unchanged complete canonical Goldman module
`src/root/m1F66.asm`, MSC 6.00AX helper code, pinned stock CRT libraries and real
RTLink 4.00. It runs under the pinned DOSBox-X. It contains no original executable
bytes and does not run the game. Every source, runtime library, historical tool
and runner is checked through the existing pinned toolchain machinery; its
receipt records the particular helper sources and runtime identities.

`f_1F66_00AF` writes the three-character drive prefix then calls DOS INT 21h/AH=47h
at destination+3. The fixture gives it a safe 256-byte buffer, calls the real
helper at each directory depth, and applies the source's conditional separator
append. This exposes required capacity without corrupting the fixture stack.

| Directory | Returned path | After separator append | Required bytes |
| --- | ---: | ---: | ---: |
| Seven nested `AAAAAAAA` components | 65 characters | 66 characters | 67: fits source local |
| Same directory plus child `A` | 67 characters | 68 characters | 69: exceeds source local |

Both directory-service calls succeed. The second path would already put its NUL
at offset 67, outside the source's 67-byte local; appending the separator needs
two further bytes. This is a concrete DOSBox-X hosted-directory negative, not
a theorem about every MS-DOS release, DOSBox backend or filesystem. No full
`FileSelect`, resource/widget, failure or gameplay execution is claimed.

The exact extension leaf `o09_35F5_0D2B` advances at most eight bytes before
copying `.ant` including its NUL, so a valid input component becomes at most
12 characters. Exploratory execution of 360 original-instruction delimiter
controls corroborated a maximum write offset 12. Conditional on a valid path
still fitting `path[67]`, the completed selector pathname requires at most
66 + 12 + 1 = 79 bytes. The condition is essential: the directory helper does
not enforce it, and the fixture above falsifies an automatic DOS path bound.
Neither `name[100]`, the neighboring original address nor a COMDEF compile
control grants unconditional filename allocation authority.

No owner, clamp, path truncation, capacity, initializer or canonical algorithm
is admitted. Keep `_fd_50F6_3862` unresolved until its supported path domain,
source-owned footprint and lifetime are reviewed together. The dangerous path
predates the global copy, so increasing only the global buffer cannot resolve it.

```powershell
python evidence/canonical/filename-domain/replay.py --out build/workers/state_extent/filename-boundary
```

The output must be fresh and strictly below `build/`. The replay asserts both
the fitting positive control and the overflowing negative and records `RUN.LOG`.
