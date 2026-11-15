import gdb, json
class Log(gdb.Breakpoint):
 def stop(self):
  names=['MapPlane','MapPnt','edit_life_tiles_handle','edit_life_alt_tiles_handle','MeType','MeHealth','MeEgg','main_iteration_count','*(short*)&clip_window_z_order']
  vals={}
  for n in names:
   try: vals[n]=str(gdb.parse_and_eval(n))
   except Exception as e: vals[n]=str(e)
  for n,size in [('LifeA',8192),('LifeB',4096),('LifeR',4096)]:
   try:
    raw=bytes(gdb.selected_inferior().read_memory(int(gdb.parse_and_eval('&'+n)),size));vals[n+'_nonzero']=sum(x!=0 for x in raw)
   except Exception as e: vals[n+'_error']=str(e)
  print('DESIGN_TRACE '+self.location+' '+json.dumps(vals))
  if self.location=='edit_release_life_tiles' and int(gdb.parse_and_eval('main_iteration_count'))>0:
   print(gdb.execute('bt 9',to_string=True))
  return False
for name in ['YellowDialog','YellowBirth','YellowDeath','edit_release_life_tiles','app_window_state_changed','win_EditChanged']:
 Log(name)
class Stop(gdb.Breakpoint):
 def stop(self):
  Log.stop(self)
  return False
Stop('__wrap_exit')
