set pagination off
set confirm off
set substitute-path D:\Prog\simant_recon\build\workers\whole_program\generated D:\Prog\simant_recon\build\whole-application-v14\inputs\build\workers\whole_program\generated
set logging file build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/cursor-pixel-stages-v1.txt
set logging overwrite on
set logging enabled on
set $capn=0
set $maskn=0
set $drawn=0
set $postn=0
break *source_g9148_capture
commands
 silent
 if $ecx == 288 && $edx == 234 && $r8d == 311 && $r9d == 250
  set $capn=$capn+1
  printf "CAPTURE %d rect=(%d,%d)-(%d,%d) buffer=%p\\n",$capn,(int)$ecx,(int)$edx,(int)$r8d,(int)$r9d,*(void**)($rsp+40)
  if $capn == 1
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/cap1-screen-before.bin s_source_owner->pixel_storage s_source_owner->pixel_storage+307200
  end
  if $capn == 2
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/cap2-screen-before.bin s_source_owner->pixel_storage s_source_owner->pixel_storage+307200
  end
  if $capn == 3
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/cap3-screen-before.bin s_source_owner->pixel_storage s_source_owner->pixel_storage+307200
  end
 end
 continue
end
break *source_g9154_callback
commands
 silent
 if $ecx == 288 && $edx == 234
  set $maskn=$maskn+1
  printf "MASK %d xy=(%d,%d) w=%d h=%d logic=%d data=%p\\n",$maskn,(int)$ecx,(int)$edx,(int)$r9d,*(unsigned short*)($rsp+40),s_source_owner->g_3DD2,$r8
  set $pix=s_source_owner->pixel_storage
  if $maskn == 1
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask1-screen-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask1-payload.bin $r8 $r8+32
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask1-save-under.bin portable_m1b73_cursor_save_under portable_m1b73_cursor_save_under+196
  end
  if $maskn == 2
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask2-screen-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask2-payload.bin $r8 $r8+32
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask2-save-under.bin portable_m1b73_cursor_save_under portable_m1b73_cursor_save_under+196
  end
  if $maskn == 3
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask3-screen-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask3-payload.bin $r8 $r8+32
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/mask3-save-under.bin portable_m1b73_cursor_save_under portable_m1b73_cursor_save_under+196
  end
 end
 continue
end
break *source_g914C_callback
commands
 silent
 if $ecx == 288 && $edx == 234
  set $drawn=$drawn+1
  printf "G914C-PRE %d xy=(%d,%d) w=%d h=%d logic=%d data=%p\\n",$drawn,(int)$ecx,(int)$edx,(int)$r9d,*(unsigned short*)($rsp+40),s_source_owner->g_3DD2,$r8
  set $pix=s_source_owner->pixel_storage
  if $drawn == 1
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c1-frame-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c1-payload.bin $r8 $r8+128
  end
  if $drawn == 2
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c2-frame-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c2-payload.bin $r8 $r8+192
  end
  if $drawn == 3
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c3-frame-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c3-payload.bin $r8 $r8+128
  end
  if $drawn == 4
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c4-frame-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c4-payload.bin $r8 $r8+192
  end
  if $drawn == 5
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c5-frame-before.bin $pix $pix+307200
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c5-payload.bin $r8 $r8+128
  end
 end
 continue
end
break *bitmap_call+151
commands
 silent
 if *(void**)($rbp+32) == source_g914C_callback && *(short*)($rbp+40) == 288 && *(short*)($rbp+48) == 234
  set $postn=$postn+1
  printf "G914C-POST %d logic=%d\\n",$postn,s_source_owner->g_3DD2
  set $pix=s_source_owner->pixel_storage
  if $postn == 1
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c1-frame-after.bin $pix $pix+307200
  end
  if $postn == 2
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c2-frame-after.bin $pix $pix+307200
  end
  if $postn == 3
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c3-frame-after.bin $pix $pix+307200
  end
  if $postn == 4
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c4-frame-after.bin $pix $pix+307200
  end
  if $postn == 5
   dump binary memory build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/g914c5-frame-after.bin $pix $pix+307200
  end
 end
 continue
end
run --headless --smoke-ms 30000 --frame build/workers/whole_program/source-main-vga-full-game-v14-cursor-diag-v1/cursor-pixel-frame-v1.bmp --seed 1 /dV --input-script build/workers/behavior_text_card/caption-runtime-v1/full-game-vga-v1.txt
quit

