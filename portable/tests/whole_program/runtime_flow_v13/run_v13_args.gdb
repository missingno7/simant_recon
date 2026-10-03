set pagination off
set confirm off
set cwd D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5
set args --headless --smoke-ms 30000 --frame D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/frame-v13-args.bmp --seed 1 /dV --assets D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-assets --bios-fonts D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-bios-fonts --input-script D:/Prog/simant_recon/portable/tests/whole_program/application_input/quick-game-vga-v1.txt
break source_g914C_callback
commands
silent
python
fr=gdb.newest_frame(); names=[]; q=fr
while q and len(names)<8: names.append(q.name()); q=q.older()
if any('o12_384C_0B76' in (n or '') for n in names):
 print('MAP CALLBACK STACK',names)
 gdb.execute('info args')
 gdb.execute('info registers rcx rdx r8 r9')
 gdb.execute('frame 1')
 gdb.execute('info args')
 gdb.execute('info locals')
 gdb.execute('p fd_50F6_10D2')
 gdb.execute('p fd_50F6_3854')
 gdb.execute('p fd_50F6_3856')
 gdb.execute('p fd_50F6_3858')
 gdb.execute('p fd_50F6_38C0')
 gdb.execute('quit')
end
continue
end
run
