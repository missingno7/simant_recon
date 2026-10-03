set pagination off
set confirm off
set logging file D:/Prog/simant_recon/build/workers/behavior_text_card/caption-runtime-v1/gdb-caption-bridge-states.txt
set logging overwrite on
set logging enabled on
break portable/whole_program/text_bitmap_bridge.c:87
commands
silent
if text != 0 && (*(char*)text == 83 || *(char*)text == 89)
printf "BRIDGE ENTRY x=%d y=%d text=%p graphics_status=%d bound=%d profile=%d\\n", x,y,text,sim_graphics_source_last_status(),source_bridge.bound,source_bridge.hardware_profile
x/s text
bt 4
end
continue
end
break portable/whole_program/text_bitmap_bridge.c:118
commands
silent
if input.text != 0 && (*(char*)input.text == 83 || *(char*)input.text == 89)
printf "BRIDGE PREP text=%p w=%d h=%d glyphh=%d rows=%p rowsz=%llu inputx=%d inputy=%d\\n", input.text,input.character_width,input.cell_height,input.glyph_height,input.glyph_rows,input.glyph_rows_size,input.x,input.y
x/s input.text
end
continue
end
break portable/whole_program/text_bitmap_bridge.c:119
commands
silent
if input.text != 0 && (*(char*)input.text == 83 || *(char*)input.text == 89)
printf "BRIDGE POST status=%d draw=%d width=%d height=%d stride=%d\\n", status,result.draw_kind,result.drawn_width,result.drawn_height,result.stride_bytes
x/16bx source_bridge.state.pixels
end
continue
end
break portable/whole_program/text_bitmap_bridge.c:142
commands
silent
printf "BRIDGE CALLBACK x=%d y=%d width=%d height=%d first16=", x,y,result.drawn_width,result.drawn_height
x/16bx source_bridge.bitmap
bt 4
continue
end
run --assets D:/Prog/simant_recon/build/workers/behavior_text_card/caption-runtime-v1/assets --bios-fonts D:/Prog/simant_recon/build/workers/behavior_text_card/caption-runtime-v1/fonts --input-script D:/Prog/simant_recon/build/workers/behavior_text_card/caption-runtime-v1/full-game-vga-v1.txt --seed 0x5A31 --smoke-ms 16000 --frame D:/Prog/simant_recon/build/workers/behavior_text_card/caption-runtime-v1/frame-v5.bmp /dV
