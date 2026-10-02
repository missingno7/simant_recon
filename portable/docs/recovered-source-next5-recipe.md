# Selected NewGame source profile

Next5 adds the frozen S15 `SetDefaultWindows` and `NewGame` bodies to next4.
Its 25 translation units compile; all 24 inherited bodies retain their parent
hashes. State remains the next4 411-field profile. This is diagnostic source
integration, separate from behavioral acceptance.

Recreate next4 using its recipe first, then run:

```powershell
python portable/tools/recover_source_next5.py --out build/workers/recovered_source_next5/generated --compile
python portable/build.py --core-profile build/workers/recovered_source_next5/generated
build/portable/simant-sdl3.exe --live-newgame --ticks 32
```

The selected source has explicit historical 16-bit integers and 32-bit longs,
with a void win_Open signature. The two source writes to fd_3D57_02C2 address
word zero of the existing array backing. Negative compile controls reject the
unlowered array assignment and a void NewGame return. Earlier compile-only
output using host-width integers was corrected before behavioral acceptance.

NewGame uses the live source scenario modal and existing TLS, RNG and resource
services. Its EndGame continuation never calls native session initialization,
imports a DOS snapshot, or reseeds RNG. The modal-only engine API rejects calls
outside that source callback boundary. Source SetMapPlane is invoked through
its reviewed f_015B_053C alias.

An original-DOS ABI probe covers 16 tutorial cases and observes AX=0 at
the zoom-state query and, when reached, the zoom-handler entry. The actual
clip_Off body clears AX after drawing. This grounds the window-0 argument
for this caller; the native zoom implementation remains unsupported.
Event 0x0207 invokes LoadGame, which remains unsupported;
it is not the tutorial entry. MenuQuit/save and complete control-window drawing
also need their own integration evidence. A 32-tick run exercises the colony
loop, not the restart path. Controlled NewGame-flow differentials and actual
in-place RandYard execution are separate proof lanes.

The startup bridge retains the source sine-table pointer fd_50F6_0B22,
as initStuff does after loading kind-9 object 1000. This is separate from
the spider adapter's g_5AAC pointer. Actual RandYard calls fracSIN through
AddFood and requires that retained table.
