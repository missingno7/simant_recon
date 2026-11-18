/* Real HWND/menu metrics, caption access and source-neutral look switching. */
#define __wrap_enhanced_execute_next unused_scale_execute
#define __wrap_native_windows_present unused_scale_present
#include "ui_scale_probe.c"
#undef __wrap_enhanced_execute_next
#undef __wrap_native_windows_present
static int cp,cs,shot,normal_matrix,caption_failures,menu_failures;
static int look_ticks;
static void CALLBACK look_capture(HWND h,UINT msg,UINT_PTR id,DWORD now){(void)h;(void)msg;(void)id;(void)now;if(++look_ticks==3){char path[2400];snprintf(path,sizeof(path),"%s/look-menu-200.bmp",getenv("SIMANT_UI_OUT"));CHECK(native_workspace_capture(path));EndMenu();}}
static const char *fixed_names[]={"Map / Ant Control Panel","Yard Control Panel","Map","Yard","Behavior Control","Caste Control","History","Info","Status"};
static const char *fixed_files[]={"ant","yard-control","map","yard","behavior","caste","history","info","status"};
static const int fixed_panels[]={WS_ANT,WS_YARD_CONTROL,WS_MAP,WS_YARD,WS_BEHAVIOR,WS_CASTE,WS_HISTORY,WS_INFO,WS_STATUS};
static int independent_width(HDC dc,const char *in,int dpi,int role){
 char label[256];int n=0;for(;*in&&n<255;++in)if(*in!='&')label[n++]=*in;label[n]=0;
 if(native_workspace_classic())return MulDiv(enhanced_font_width(label)*(role==2?2:1),dpi,96);
 HFONT f=CreateFontA(-MulDiv(role==1?10:13,dpi,96),0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,"Tahoma");HGDIOBJ old=SelectObject(dc,f);SIZE z;GetTextExtentPoint32A(dc,label,n,&z);SelectObject(dc,old);DeleteObject(f);return z.cx;
}
static void menu_check(HMENU menu,int bar){
 int dpi=native_workspace_ui_dpi(root);HDC dc=GetDC(root);
 for(int i=0;i<GetMenuItemCount(menu);++i){char label[256]={0};MENUITEMINFOA item={.cbSize=sizeof(item),.fMask=MIIM_DATA|MIIM_FTYPE|MIIM_ID|MIIM_SUBMENU|MIIM_STRING,.dwTypeData=label,.cch=255};CHECK(GetMenuItemInfoA(menu,i,TRUE,&item));if(item.fType&MFT_SEPARATOR)continue;
  CHECK(item.fType&MFT_OWNERDRAW);CHECK(item.dwItemData);if(!item.dwItemData)continue;
  snprintf(label,sizeof(label),"%s",(const char *)item.dwItemData);char *tab=strchr(label,'\t');if(tab)*tab++=0;
  int need=independent_width(dc,label,dpi,2)+(tab?independent_width(dc,tab,dpi,2)+MulDiv(16,dpi,96):0);
  MEASUREITEMSTRUCT m={.CtlType=ODT_MENU,.itemID=item.wID,.itemData=item.dwItemData};CHECK(SendMessage(root,WM_MEASUREITEM,0,(LPARAM)&m));
  int fit=(int)m.itemWidth>=need+MulDiv(36,dpi,96);if(!fit){++menu_failures;fprintf(stderr,"CLASSIC_MENU_WIDTH %s need=%d got=%u dpi=%d\n",label,need,m.itemWidth,dpi);}CHECK(fit);
  if(bar){RECT r;CHECK(GetMenuItemRect(root,menu,i,&r));fit=r.right-r.left>=need+MulDiv(36,dpi,96);if(!fit){++menu_failures;fprintf(stderr,"CLASSIC_BAR_WIDTH %s need=%d got=%ld dpi=%d\n",label,need,r.right-r.left,dpi);}CHECK(fit);}
  if(item.hSubMenu)menu_check(item.hSubMenu,0);
 }ReleaseDC(root,dc);
}
static int art_only(unsigned id){
 static const unsigned ids[]={5,6,7,15,16,0x116,0x117,0x10e,0x10f,0x111,0x113,0x114,0x118,0x1911};for(unsigned i=0;i<sizeof(ids)/sizeof(ids[0]);++i)if(ids[i]==id)return 1;return 0;
}
static void button_checks(void){
 for(unsigned p=0;p<9;++p){HWND parent=named(fixed_names[p]);if(!parent)continue;int dpi=native_workspace_ui_dpi(parent);HDC dc=GetDC(parent);RECT client;GetClientRect(parent,&client);
  for(HWND child=GetWindow(parent,GW_CHILD);child;child=GetWindow(child,GW_HWNDNEXT)){if(!(GetWindowLong(child,GWL_STYLE)&WS_VISIBLE))continue;RECT a;GetWindowRect(child,&a);MapWindowPoints(NULL,parent,(POINT *)&a,2);CHECK(a.left>=0&&a.top>=0&&a.right<=client.right&&a.bottom<=client.bottom);
   for(HWND other=GetWindow(child,GW_HWNDNEXT);other;other=GetWindow(other,GW_HWNDNEXT))if(GetWindowLong(other,GWL_STYLE)&WS_VISIBLE){RECT b,hit;GetWindowRect(other,&b);MapWindowPoints(NULL,parent,(POINT *)&b,2);if(IntersectRect(&hit,&a,&b)){++caption_failures;fprintf(stderr,"CLASSIC_OVERLAP panel=%s ids=%x,%x\n",fixed_names[p],GetDlgCtrlID(child),GetDlgCtrlID(other));CHECK(0);}else CHECK(1);}
   char cls[40];GetClassNameA(child,cls,sizeof(cls));unsigned id=GetDlgCtrlID(child);if(strcmp(cls,"Button")||art_only(id)||id==0xe310||id==0xe311)continue;
   char label[160];const char *caption=native_workspace_button_caption(id);if(!caption){GetWindowTextA(child,label,sizeof(label));caption=label;}
   if(id==0x112||id==0x115)continue;
   int need=independent_width(dc,caption,dpi,1)+MulDiv(6,dpi,96),fit=need<=a.right-a.left;
   if(!fit){++caption_failures;fprintf(stderr,"CLASSIC_CAPTION panel=%s id=%x label=%s need=%d width=%ld dpi=%d\n",fixed_names[p],id,caption,need,a.right-a.left,dpi);}CHECK(fit);
  }ReleaseDC(parent,dc);
 }
}
static void caption_access(void){
 RECT work={0,0,work_width,work_height};
 for(int p=0;p<=WS_INFO;++p){if(p==WS_RESERVED)continue;HWND h=named(ws_name(p));if(!h||!IsWindowVisible(h))continue;
  RECT frame;GetWindowRect(h,&frame);POINT at={0,0};ClientToScreen(h,&at);RECT cap={frame.left+3,frame.top+3,frame.right-3,at.y-3},clipped;CHECK(IntersectRect(&clipped,&cap,&work));
  HRGN free_region=CreateRectRgnIndirect(&clipped);for(HWND above=GetWindow(h,GW_HWNDPREV);above;above=GetWindow(above,GW_HWNDPREV)){DWORD pid;GetWindowThreadProcessId(above,&pid);if(pid!=GetCurrentProcessId()||!IsWindowVisible(above)||above==root)continue;RECT cover;GetWindowRect(above,&cover);HRGN occupied=CreateRectRgnIndirect(&cover);CombineRgn(free_region,free_region,occupied,RGN_DIFF);DeleteObject(occupied);}
  RECT visible={0};int fit=0;DWORD bytes=GetRegionData(free_region,0,NULL);RGNDATA *data=malloc(bytes);
  if(data&&GetRegionData(free_region,bytes,data))for(DWORD i=0;i<data->rdh.nCount;++i){RECT part=((RECT *)data->Buffer)[i];if(part.right-part.left>=MulDiv(60,native_workspace_ui_dpi(h),96)&&part.bottom-part.top>=cap.bottom-cap.top-2){fit=1;visible=part;POINT point={part.left+MulDiv(20,native_workspace_ui_dpi(h),96),(part.top+part.bottom)/2};CHECK(SendMessage(h,WM_NCHITTEST,0,MAKELPARAM(point.x,point.y))==HTCAPTION);break;}}free(data);
  if(!fit)fprintf(stderr,"CLASSIC_CAPTION_ACCESS %s frame=%ld,%ld,%ld,%ld free=%ld,%ld,%ld,%ld area=%d,%d\n",ws_name(p),frame.left,frame.top,frame.right,frame.bottom,visible.left,visible.top,visible.right,visible.bottom,work_width,work_height);CHECK(fit);DeleteObject(free_region);
 }
}
static void pictures(int exclude_map){
 for(int look=0;look<2;++look)for(int k=0;k<2;++k){SendMessage(root,WM_COMMAND,0xe420+look,0);native_workspace_set_ui_scale(k?200:100);
  for(int p=0;p<8;++p){if((exclude_map&&p==2)||(!exclude_map&&p!=2))continue;HWND h=named(fixed_names[p]);CHECK(h);CHECK(IsWindowVisible(h));if(!h)continue;char name[100];snprintf(name,sizeof(name),"%s-%s-%d",fixed_files[p],look?"native":"classic",k?200:100);save(h,name);}
 }
}
static void matrix_classic(void){
 uint64_t before=source_fingerprint();const EnhancedSnapshot published=*enhanced_snapshot();
 for(int look=0;look<2;++look){SendMessage(root,WM_COMMAND,0xe420+look,0);CHECK(native_workspace_layout()->native_look==look);
  for(int physical=96;physical<=144;physical+=24){native_workspace_set_ui_scale(0);
   for(int p=0;p<=WS_STATUS;++p){if(p==WS_RESERVED)continue;HWND h=named(ws_name(p));if(h){RECT r;GetWindowRect(h,&r);SendMessage(h,WM_DPICHANGED,MAKELONG(physical,physical),(LPARAM)&r);}}
   RECT r;GetWindowRect(root,&r);SendMessage(root,WM_DPICHANGED,MAKELONG(physical,physical),(LPARAM)&r);
   menu_check(GetMenu(root),1);button_checks();
   for(int k=1;k<8;++k){native_workspace_set_ui_scale(scales[k]);menu_check(GetMenu(root),1);button_checks();}
  }
 }
 CHECK(source_fingerprint()==before);CHECK(!memcmp(&published,enhanced_snapshot(),sizeof(published)));
 const int areas[][2]={{1280,680},{1920,1040},{2560,1400}},levels[]={100,200,300};
 for(int look=0;look<2;++look)for(int a=0;a<3;++a)for(int k=0;k<3;++k){native_workspace_set_look(look);work_width=areas[a][0];work_height=areas[a][1];native_workspace_set_ui_scale(levels[k]);SendMessage(root,WM_COMMAND,0xe100,0);caption_access();button_checks();
  if(!look&&a==1&&k==1){char path[2400];snprintf(path,sizeof(path),"%s/reset-200-1080p.bmp",getenv("SIMANT_UI_OUT"));CHECK(native_workspace_capture(path));}
 }
 work_width=work_height=0;
 CHECK(source_fingerprint()==before);CHECK(!memcmp(&published,enhanced_snapshot(),sizeof(published)));
}
int __wrap_native_windows_present(const HostPalette *palette){int result=__real_native_windows_present(palette);HWND status=named("Status");
 if(cp==4&&status&&IsWindowVisible(status)){cp=5;button_checks();
  if(shot<4){char name[80];snprintf(name,sizeof(name),"status-%s-%d",shot/2?"native":"classic",shot%2?200:100);save(status,name);}
  else {int index=shot-4,expected=index%8?MulDiv(scales[index%8],96,100):96+(index%24/8)*24;CHECK(native_workspace_ui_dpi(status)==expected);}
  SendMessage(GetDlgItem(status,0x180c),BM_CLICK,0,0);cs=main_iteration_count;}return result;
}
void __wrap_enhanced_execute_next(void){const EnhancedSnapshot *s=enhanced_snapshot();if(!s||!s->panels.world_ready){__real_enhanced_execute_next();return;}
 if(!cp&&main_iteration_count>2){root=named("SimAnt");CHECK(native_workspace_classic());cp=1;cs=main_iteration_count;if(!s->panels.paused)enhanced_submit_event(15,0,0,0);int events[]={0x10f,0x111,0x113,0x115,0xfd21};for(unsigned i=0;i<5;++i)enhanced_submit_event(events[i],0,0,0);}
 if(cp==1&&main_iteration_count>cs+4&&!s->dialogs.modal&&!enhanced_action_lease_active()&&enhanced_action_ledger()->delivered==enhanced_action_ledger()->submitted){matrix_classic();pictures(1);cp=2;cs=main_iteration_count;enhanced_submit_event(0x106,0,0,0);}
 if(cp==2&&main_iteration_count>cs+4&&!s->dialogs.modal&&!enhanced_action_lease_active()){pictures(0);native_workspace_set_ui_scale(200);for(int look=0;look<2;++look){native_workspace_set_look(look);char path[2400];snprintf(path,sizeof(path),"%s/menu-bar-%s-200.bmp",getenv("SIMANT_UI_OUT"),look?"native":"classic");CHECK(native_workspace_capture(path));}
  native_workspace_set_look(0);HMENU options=GetSubMenu(GetMenu(root),3),look=GetSubMenu(options,GetMenuItemCount(options)-2);CHECK(look);SetForegroundWindow(root);SetFocus(root);SetTimer(root,0xe754,100,look_capture);RECT at;GetWindowRect(root,&at);TrackPopupMenuEx(look,TPM_LEFTALIGN|TPM_TOPALIGN,at.left+200,at.top+80,root,NULL);KillTimer(root,0xe754);CHECK(look_ticks>=3);cp=3;}
 if(cp==3){if(shot==52){native_workspace_set_ui_scale(200);fprintf(stderr,"CLASSIC_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"menu_failures\":%d,\"caption_failures\":%d,\"status_captures\":4,\"status_matrix\":48}\n",failures?"false":"true",checks,failures,menu_failures,caption_failures);exit(failures?1:0);}
  if(shot<4){native_workspace_set_look(shot/2);native_workspace_set_ui_scale(shot%2?200:100);}
  else {int index=shot-4,physical=96+(index%24/8)*24;native_workspace_set_look(index/24);native_workspace_set_ui_scale(0);
   for(int p=0;p<=WS_STATUS;++p){if(p==WS_RESERVED)continue;HWND h=named(ws_name(p));if(h){RECT r;GetWindowRect(h,&r);SendMessage(h,WM_DPICHANGED,MAKELONG(physical,physical),(LPARAM)&r);}}
   RECT r;GetWindowRect(root,&r);SendMessage(root,WM_DPICHANGED,MAKELONG(physical,physical),(LPARAM)&r);native_workspace_set_ui_scale(scales[index%8]);}
  cp=4;enhanced_submit_event(0x114,0,0,0);}
 if(cp==5&&main_iteration_count>cs+1&&!s->dialogs.modal&&!enhanced_action_lease_active()){++shot;cp=3;}
 __real_enhanced_execute_next();
}
