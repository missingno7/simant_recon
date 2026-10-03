set pagination off
set confirm off
set cwd D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5
set args --headless --smoke-ms 30000 --frame D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/frame-v13-stack.bmp --seed 1 /dV --assets D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-assets --bios-fonts D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-bios-fonts --input-script D:/Prog/simant_recon/portable/tests/whole_program/application_input/quick-game-vga-v1.txt
break source_g914C_callback
commands
silent
python
fr=gdb.newest_frame(); q=fr; ns=[]
while q and len(ns)<8: ns.append(q.name()); q=q.older()
if any('o12_384C_0B76' in (n or '') for n in ns):
 print('MAP STACK',ns)
 gdb.execute('info registers rcx rdx r8 r9 rsp')
 gdb.execute('x/10gx $rsp')
 gdb.execute('disassemble source_g914C_callback')
 gdb.execute('quit')
end
continue
end
run
