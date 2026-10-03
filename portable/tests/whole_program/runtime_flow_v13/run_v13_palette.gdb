set pagination off
set confirm off
set cwd D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5
set args --headless --smoke-ms 30000 --frame D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/frame-v13-pal.bmp --seed 1 /dV --assets D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-assets --bios-fonts D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-bios-fonts --input-script D:/Prog/simant_recon/portable/tests/whole_program/application_input/quick-game-vga-v1.txt
break host_present
commands
silent
python
p=int(gdb.parse_and_eval('$r9')); d=bytes(gdb.selected_inferior().read_memory(p,48)); print('palettePtr',hex(p),'raw',d.hex()); print('rgb',[(i,tuple(d[i*3:i*3+3])) for i in range(16)]); gdb.execute('quit')
end
continue
end
run
