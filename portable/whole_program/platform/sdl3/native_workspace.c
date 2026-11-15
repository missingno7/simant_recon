/* Native presentation only. No window_hosting mutation or source clock APIs. */
#include "native_workspace.h"
#include "portable/whole_program/enhanced/workspace.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/world.h"
#include "portable/whole_program/enhanced/assets.h"
#include "portable/whole_program/enhanced/actions.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <shlobj.h>

enum { CMD_PRESET=100, CMD_REVEAL=200, CMD_MOVE=1000, CMD_PLANE=400, CMD_FLOAT=410,
       CMD_COLLAPSE,CMD_HIDE,CMD_RESET,CMD_INSPECTOR,CMD_ZOOMIN,CMD_ZOOMOUT,CMD_OUTER=1300 };
typedef struct Group {
    HWND host,tab,menu,collapse,canvas; RECT rect; int visible,dpi; HFONT font;
} Group;
static struct {
    int active,building,saving,focus_group,drag_panel,dragging,split_drag,applying,small,com_initialized;
    HWND root,floats[WS_FLOATS],splitters[WS_NODES],targets[9],preview;
    Group groups[WS_NODES]; RECT splits[WS_NODES];
    Workspace layout; HostPalette palette;
    HFONT font; int dpi; POINT drag_start; int target_group,target_edge,target_outer;
    UINT64 generation,last_paint; SDL_WindowID sdl_id;
    int source_ready,source_plane,source_x,source_y;
    char path[2048]; HMENU menu;
} u;
static LRESULT CALLBACK root_proc(HWND,UINT,WPARAM,LPARAM,UINT_PTR,DWORD_PTR);
static LRESULT CALLBACK group_proc(HWND,UINT,WPARAM,LPARAM);
static LRESULT CALLBACK float_proc(HWND,UINT,WPARAM,LPARAM);
static LRESULT CALLBACK control_proc(HWND,UINT,WPARAM,LPARAM,UINT_PTR,DWORD_PTR);
static void arrange(void);
static void save(void);
static void panel_menu(int,POINT);
static void finish_drag(int);
static int dip(int v){return MulDiv(v,u.dpi,96);}
static int undip(int v){return MulDiv(v,96,u.dpi);}
static int window_dpi(HWND h) {
    typedef UINT (WINAPI *GetDpi)(HWND);
    GetDpi get=(GetDpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");
    if(get)return get(h);HDC dc=GetDC(h);int dpi=GetDeviceCaps(dc,LOGPIXELSX);ReleaseDC(h,dc);return dpi;
}
static int panel_at(int g){WsNode *n=&u.layout.nodes[g];return n->count?n->panels[n->active]:-1;}
static HWND control(const char *cls,const char *text,DWORD style,HWND owner,int id) {
    HWND h=CreateWindowExA(0,cls,text,WS_CHILD|WS_VISIBLE|style,0,0,0,0,owner,(HMENU)(INT_PTR)id,GetModuleHandle(NULL),NULL);
    SendMessage(h,WM_SETFONT,(WPARAM)u.font,TRUE);return h;
}
static void dimensions(int node,int *w,int *h) {
    WsNode *n=&u.layout.nodes[node];
    if(n->kind==1){int world=0;for(int i=0;i<n->count;++i)world|=n->panels[i]<4;
        *w=dip(n->collapsed?30:world?320:220);*h=dip(n->collapsed?30:world?240:120);return;}
    int a,b,c,d;dimensions(n->a,&a,&b);dimensions(n->b,&c,&d);
    *w=n->axis?(a>c?a:c):a+c+dip(6);*h=n->axis?b+d+dip(6):(b>d?b:d);
}
static void font(void) {
    HFONT old=u.font;u.font=CreateFontW(-dip(14),0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Segoe UI");
    if(old)DeleteObject(old);
}
static void layout_node(int node,HWND parent,RECT r) {
    if(node<0)return;WsNode *n=&u.layout.nodes[node];int width=r.right-r.left,height=r.bottom-r.top;
    if(n->kind==2) {
        int aw,ah,bw,bh;dimensions(n->a,&aw,&ah);dimensions(n->b,&bw,&bh);
        int size=(n->axis?height:width)-dip(6),a=n->axis?ah:aw,b=n->axis?bh:bw;
        int at=MulDiv(size,n->ratio,1000);
        if(size>=a+b){if(at<a)at=a;if(at>size-b)at=size-b;}
        else {at=MulDiv(size,a,a+b);if(at<dip(24))at=dip(24);if(at>size-dip(24))at=size-dip(24);}
        if(u.layout.nodes[n->a].kind==1&&u.layout.nodes[n->a].collapsed)at=dip(30);
        if(u.layout.nodes[n->b].kind==1&&u.layout.nodes[n->b].collapsed)at=size-dip(30);
        RECT first=r,last=r,s=r;
        if(n->axis){first.bottom=r.top+at;s.top=first.bottom;s.bottom=s.top+dip(6);last.top=s.bottom;}
        else {first.right=r.left+at;s.left=first.right;s.right=s.left+dip(6);last.left=s.right;}
        if(!u.splitters[node]) {
            u.splitters[node]=control(TRACKBAR_CLASSA,"Workspace splitter",WS_TABSTOP|TBS_NOTICKS|(n->axis?TBS_VERT:0),parent,500+node);
            SetWindowSubclass(u.splitters[node],control_proc,3,node);
            SendMessage(u.splitters[node],TBM_SETRANGE,TRUE,MAKELPARAM(50,950));
        }
        SetParent(u.splitters[node],parent);u.splits[node]=r;
        SetWindowTextA(u.splitters[node],n->axis?"Horizontal region splitter: Up/Down, Home equal":"Vertical region splitter: Left/Right, Home equal");
        MoveWindow(u.splitters[node],s.left,s.top,s.right-s.left,s.bottom-s.top,TRUE);
        SendMessage(u.splitters[node],TBM_SETPOS,TRUE,n->ratio);ShowWindow(u.splitters[node],SW_SHOW);
        layout_node(n->a,parent,first);layout_node(n->b,parent,last);return;
    }
    Group *g=&u.groups[node];g->visible=1;g->rect=r;
    if(!g->host) {
        g->host=CreateWindowExA(WS_EX_CONTROLPARENT,"SimAntWorkspaceGroup","Panel region",WS_CHILD|WS_VISIBLE|WS_CLIPCHILDREN,0,0,0,0,parent,NULL,GetModuleHandle(NULL),(void *)(INT_PTR)node);
        g->tab=control(WC_TABCONTROLA,"Panel tabs",WS_TABSTOP|TCS_FOCUSONBUTTONDOWN,g->host,1);
        g->menu=control("BUTTON","Move panel",WS_TABSTOP,g->host,2);
        g->collapse=control("BUTTON","Collapse region",WS_TABSTOP|BS_OWNERDRAW,g->host,3);
        g->canvas=control("BUTTON","World canvas",WS_TABSTOP|BS_OWNERDRAW,g->host,4);
        SetWindowSubclass(g->tab,control_proc,1,node);SetWindowSubclass(g->canvas,control_proc,2,node);
        SetWindowSubclass(g->menu,control_proc,4,node);SetWindowSubclass(g->collapse,control_proc,4,node);
    }
    SetParent(g->host,parent);MoveWindow(g->host,r.left,r.top,width,height,TRUE);
    if(g->dpi!=u.dpi){HFONT old=g->font;g->dpi=u.dpi;
        g->font=CreateFontW(-dip(14),0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Segoe UI");
        HWND controls[]={g->tab,g->menu,g->collapse,g->canvas};for(int i=0;i<4;++i)SendMessage(controls[i],WM_SETFONT,(WPARAM)g->font,TRUE);
        if(old)DeleteObject(old);}
    TabCtrl_DeleteAllItems(g->tab);
    for(int i=0;i<n->count;++i){TCITEMA item={.mask=TCIF_TEXT,.pszText=(char *)ws_name(n->panels[i])};TabCtrl_InsertItem(g->tab,i,&item);}
    TabCtrl_SetCurSel(g->tab,n->active);
    int title=dip(30),buttons=dip(126);
    MoveWindow(g->tab,0,0,width>buttons?width-buttons:width,title,TRUE);
    MoveWindow(g->menu,width-dip(126),0,dip(84),title,TRUE);
    MoveWindow(g->collapse,width-dip(42),0,dip(42),title,TRUE);
    SetWindowTextA(g->collapse,n->collapsed?"Expand region":"Collapse region");
    ShowWindow(g->menu,width<dip(160)?SW_HIDE:SW_SHOW);ShowWindow(g->collapse,width<dip(160)?SW_HIDE:SW_SHOW);
    MoveWindow(g->canvas,1,title,width>2?width-2:1,height>title?height-title-1:1,TRUE);
    ShowWindow(g->canvas,n->collapsed?SW_HIDE:SW_SHOW);
    int p=panel_at(node);char name[240];
    if(p<4)snprintf(name,sizeof(name),"%s. %s. Live %s. Mouse wheel zoom; drag pan; Shift F10 view and layout menu.",ws_name(p),p?"Read only":"Primary",p&&u.layout.panels[p].plane==2?"black nest":p&&u.layout.panels[p].plane==3?"red nest":"world");
    else snprintf(name,sizeof(name),"%s. Empty native panel; content arrives in a later phase.",ws_name(p));
    SetWindowTextA(g->canvas,name);SetWindowTextA(g->host,ws_name(p));
    ShowWindow(g->host,SW_SHOW);InvalidateRect(g->canvas,NULL,FALSE);
}
typedef struct MonitorFind {const char *name;HMONITOR found;} MonitorFind;
static BOOL CALLBACK monitor_find(HMONITOR h,HDC dc,LPRECT r,LPARAM data){(void)dc;(void)r;MonitorFind *f=(MonitorFind *)data;MONITORINFOEXA m={.cbSize=sizeof(m)};GetMonitorInfoA(h,(MONITORINFO *)&m);if(!strcmp(m.szDevice,f->name))f->found=h;return TRUE;}
static RECT float_rect(WsFloat *f) {
    MonitorFind find={f->monitor,NULL};EnumDisplayMonitors(NULL,NULL,monitor_find,(LPARAM)&find);
    HMONITOR h=find.found?find.found:MonitorFromWindow(u.root,MONITOR_DEFAULTTONEAREST);
    MONITORINFOEXA m={.cbSize=sizeof(m)};GetMonitorInfoA(h,(MONITORINFO *)&m);
    /* Effective monitor DPI is a host metric, unrelated to source units. */
    typedef HRESULT (WINAPI *MonitorDpi)(HMONITOR,int,UINT *,UINT *);
    HMODULE shcore=LoadLibraryA("shcore.dll");MonitorDpi get=shcore?(MonitorDpi)GetProcAddress(shcore,"GetDpiForMonitor"):NULL;
    UINT dx=u.dpi,dy=u.dpi;if(get)get(h,0,&dx,&dy);if(shcore)FreeLibrary(shcore);
    int width=MulDiv(f->w,dx,96),height=MulDiv(f->h,dy,96),mw=m.rcWork.right-m.rcWork.left,mh=m.rcWork.bottom-m.rcWork.top;
    if(width>mw)width=mw;if(height>mh)height=mh;
    int x=m.rcWork.left+MulDiv(f->x,dx,96),y=m.rcWork.top+MulDiv(f->y,dy,96);
    if(x<m.rcWork.left)x=m.rcWork.left;if(x+width>m.rcWork.right)x=m.rcWork.right-width;
    if(y<m.rcWork.top)y=m.rcWork.top;if(y+height>m.rcWork.bottom)y=m.rcWork.bottom-height;
    return (RECT){x,y,x+width,y+height};
}
static void arrange(void) {
    if(!u.active||u.building)return;u.building=1;
    for(int i=0;i<WS_NODES;++i){u.groups[i].visible=0;if(u.groups[i].host)ShowWindow(u.groups[i].host,SW_HIDE);if(u.splitters[i])ShowWindow(u.splitters[i],SW_HIDE);}
    RECT r;GetClientRect(u.root,&r);r.left+=dip(4);r.top+=dip(4);r.right-=dip(4);r.bottom-=dip(4);
    /* Entering a narrow workspace collapses side regions once. They remain
     * explicitly expandable, and the remembered split ratios survive. */
    int small=r.right<dip(900);
    if(small&&!u.small)for(int i=0;i<WS_NODES;++i)
        if(u.layout.nodes[i].kind==1){int p=panel_at(i);if(p>=4&&p!=22)u.layout.nodes[i].collapsed=1;}
    u.small=small;
    layout_node(u.layout.root,u.root,r);
    for(int i=0;i<WS_FLOATS;++i){WsFloat *f=&u.layout.floats[i];
        if(f->root<0){if(u.floats[i])ShowWindow(u.floats[i],SW_HIDE);continue;}
        if(!u.floats[i]){RECT b=float_rect(f);u.floats[i]=CreateWindowExA(WS_EX_TOOLWINDOW|WS_EX_CONTROLPARENT,"SimAntWorkspaceFloat","SimAnt floating panels",WS_OVERLAPPEDWINDOW|WS_CLIPCHILDREN,b.left,b.top,b.right-b.left,b.bottom-b.top,u.root,NULL,GetModuleHandle(NULL),(void *)(INT_PTR)i);}
        GetClientRect(u.floats[i],&r);int root_dpi=u.dpi;u.dpi=window_dpi(u.floats[i]);if(!u.dpi)u.dpi=root_dpi;
        layout_node(f->root,u.floats[i],r);u.dpi=root_dpi;ShowWindow(u.floats[i],SW_SHOWNOACTIVATE);
    }
    u.building=0;InvalidateRect(u.root,NULL,TRUE);
}
static void save(void) {
    if(!u.path[0]||u.saving)return;u.saving=1;char tmp[2100];snprintf(tmp,sizeof(tmp),"%s.tmp",u.path);
    FILE *f=fopen(tmp,"w");if(f){int okay=ws_write(&u.layout,f);if(fclose(f))okay=0;if(okay)MoveFileExA(tmp,u.path,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH);else DeleteFileA(tmp);}
    u.saving=0;
}
static void commit_layout(void){
    const EnhancedSnapshot *s=enhanced_snapshot();if(s&&s->dialogs.modal)ws_prompt(&u.layout,1);
    arrange();u.applying=1;
    for(int i=0;i<WS_FLOATS;++i)if(u.floats[i]&&u.layout.floats[i].root>=0){RECT r=float_rect(&u.layout.floats[i]);SetWindowPos(u.floats[i],NULL,r.left,r.top,r.right-r.left,r.bottom-r.top,SWP_NOZORDER|SWP_NOACTIVATE);}
    u.applying=0;save();
}
static void focus_group(int g){if(g>=0&&g<WS_NODES&&u.groups[g].visible){u.focus_group=g;SetFocus(u.groups[g].canvas);}}
static int gesture(void) {const EnhancedSnapshot *s=enhanced_snapshot();return s&&s->panels.tool!=-1;}
static void cycle(int direction,int tabs) {
    int g=u.focus_group;
    if(tabs&&g>=0&&u.layout.nodes[g].kind==1){WsNode *n=&u.layout.nodes[g];n->active=(n->active+n->count+direction)%n->count;commit_layout();focus_group(g);return;}
    for(int i=1;i<=WS_NODES;++i){int k=(g+WS_NODES+i*direction)%WS_NODES;if(u.groups[k].visible){focus_group(k);return;}}
}
static void zoom(int p,int in) {
    WsPanel *v=&u.layout.panels[p];int value=v->zoom;
    value=in?(value>=100?value+100:value*2):(value>100?value-100:value/2);
    v->zoom=value<25?25:value>800?800:value;
}
static int shortcut(UINT msg,WPARAM key) {
    if(msg!=WM_KEYDOWN)return 0;
    if(key==VK_F6){cycle(GetKeyState(VK_SHIFT)<0?-1:1,0);return 1;}
    if(key==VK_TAB&&GetKeyState(VK_CONTROL)<0){cycle(GetKeyState(VK_SHIFT)<0?-1:1,1);return 1;}
    if(key==VK_ESCAPE&&u.dragging){finish_drag(0);return 1;}
    if(key==VK_F10&&GetKeyState(VK_SHIFT)<0){POINT p;GetCursorPos(&p);panel_menu(u.focus_group,p);return 1;}
    return 0;
}
static void command(int id,int g) {
    int p=g>=0?panel_at(g):0;
    if(id>=CMD_PRESET&&id<CMD_PRESET+4){if(gesture())return;ws_preset(&u.layout,id-CMD_PRESET);}
    else if(id>=CMD_REVEAL&&id<CMD_REVEAL+WS_PANELS)ws_reveal(&u.layout,id-CMD_REVEAL);
    else if(id>=CMD_MOVE&&id<CMD_MOVE+WS_PANELS*5){if(gesture())return;int v=id-CMD_MOVE;ws_move(&u.layout,p,v/5,v%5,0);}
    else if(id>=CMD_OUTER&&id<CMD_OUTER+4){if(gesture())return;int target=p==0?4:0;ws_move(&u.layout,p,target,id-CMD_OUTER,1);}
    else if(id>=CMD_PLANE&&id<CMD_PLANE+3&&p<4){if(p)u.layout.panels[p].plane=id-CMD_PLANE+1;
        else {const EnhancedSnapshot *s=enhanced_snapshot();const EnhancedActionLedger *l=enhanced_action_ledger();EnhancedIntent intent={.id="N01",.parameter=id-CMD_PLANE+1,.serial=l->last_serial+1,.generation=s?s->generation:0};enhanced_submit(&intent);}}
    else switch(id){case CMD_FLOAT:if(!gesture())ws_float(&u.layout,p,80,80,520,400);break;
        case CMD_COLLAPSE:ws_collapse(&u.layout,g);break;case CMD_HIDE:if(!gesture())ws_hide(&u.layout,p);break;
        case CMD_RESET:if(!gesture())ws_preset(&u.layout,0);break;
        case CMD_INSPECTOR:for(int i=1;i<4;++i)if(ws_group(&u.layout,i)<0){ws_reveal(&u.layout,i);ws_move(&u.layout,i,0,WS_RIGHT,0);break;}break;
        case CMD_ZOOMIN:if(p<4)zoom(p,1);break;
        case CMD_ZOOMOUT:if(p<4)zoom(p,0);break;}
    commit_layout();
}
static void panel_menu(int g,POINT pos) {
    if(g<0||g>=WS_NODES||u.layout.nodes[g].kind!=1)return;
    u.focus_group=g;int p=panel_at(g);HMENU menu=CreatePopupMenu(),move=CreatePopupMenu();
    const char *edges[]={"Split left","Split right","Split above","Split below","Stack as tab"};
    for(int target=0;target<WS_PANELS;++target)if(target!=p&&ws_group(&u.layout,target)>=0) {
        HMENU sub=CreatePopupMenu();for(int edge=0;edge<5;++edge)AppendMenuA(sub,MF_STRING,CMD_MOVE+target*5+edge,edges[edge]);
        AppendMenuA(move,MF_POPUP,(UINT_PTR)sub,ws_name(target));}
    AppendMenuA(menu,MF_POPUP,(UINT_PTR)move,"Move panel to...");
    HMENU outer=CreatePopupMenu();for(int edge=0;edge<4;++edge)AppendMenuA(outer,MF_STRING,CMD_OUTER+edge,edges[edge]);AppendMenuA(menu,MF_POPUP,(UINT_PTR)outer,"Dock to workspace edge");
    AppendMenuA(menu,MF_STRING,CMD_FLOAT,"Float as tool window");AppendMenuA(menu,MF_STRING,CMD_COLLAPSE,"Collapse / Expand");
    AppendMenuA(menu,p==22?MF_GRAYED:MF_STRING,CMD_HIDE,"Hide panel");
    if(p<4){AppendMenuA(menu,MF_SEPARATOR,0,NULL);const char *planes[]={"Surface","Black nest","Red nest"};for(int i=0;i<3;++i)AppendMenuA(menu,MF_STRING,CMD_PLANE+i,planes[i]);
        AppendMenuA(menu,MF_STRING,CMD_ZOOMIN,"Zoom in");AppendMenuA(menu,MF_STRING,CMD_ZOOMOUT,"Zoom out");}
    AppendMenuA(menu,MF_STRING,CMD_RESET,"Reset Layout");int id=TrackPopupMenu(menu,TPM_RETURNCMD|TPM_RIGHTBUTTON,pos.x,pos.y,0,u.root,NULL);
    DestroyMenu(menu);if(id)command(id,g);
}
static void draw_world(HDC dc,RECT r,int p) {
    const EnhancedSnapshot *s=enhanced_snapshot();
    FillRect(dc,&r,GetSysColorBrush(COLOR_APPWORKSPACE));
    if(!s){SetTextColor(dc,RGB(245,245,245));SetBkMode(dc,TRANSPARENT);DrawTextA(dc,"Waiting for a live world snapshot",-1,&r,DT_CENTER|DT_VCENTER|DT_SINGLELINE);return;}
    WsPanel *view=&u.layout.panels[p];int plane=p?view->plane:s->world.plane;
    int width=plane<2?2048:1024,height=1024;
    uint8_t *indexed=calloc((size_t)width,height);uint32_t *pixels=malloc((size_t)width*height*4);
    if(!indexed||!pixels){free(indexed);free(pixels);return;}
    for(int x=0;x<width/16;++x)for(int y=0;y<64;++y){ModernCell c;uint8_t tile[256];enhanced_world_cell(&s->world,plane,x,y,&c);
        if(enhanced_asset_cell(s->world.terrain_set,c.ground,c.life,tile))for(int yy=0;yy<16;++yy)memcpy(indexed+(size_t)(y*16+yy)*width+x*16,tile+yy*16,16);}
    if(plane==s->world.plane)enhanced_world_draw(&s->world,indexed,width,height,width);
    for(int i=0;i<width*height;++i){const uint8_t *rgb=u.palette.rgb[indexed[i]&15];pixels[i]=rgb[0]*65536u+rgb[1]*256u+rgb[2];}
    BITMAPINFO info={.bmiHeader={.biSize=sizeof(BITMAPINFOHEADER),.biWidth=width,.biHeight=-height,.biPlanes=1,.biBitCount=32,.biCompression=BI_RGB}};
    double zoom=view->zoom/100.0*u.dpi/96.0;
    int cw=r.right-r.left,ch=r.bottom-r.top;
    if(view->x<0)view->x=p&&plane!=s->world.plane?(width/2-(int)(cw/zoom)/2):s->world.origin.x*16;
    if(view->y<0)view->y=p&&plane!=s->world.plane?(height/2-(int)(ch/zoom)/2):s->world.origin.y*16;
    if(view->x<0)view->x=0;if(view->y<0)view->y=0;
    int sx=view->x,sy=view->y;if(sx>width-16)sx=width-16;if(sy>height-16)sy=height-16;
    int sw=(int)(cw/zoom),sh=(int)(ch/zoom);if(sw>width-sx)sw=width-sx;if(sh>height-sy)sh=height-sy;
    SetStretchBltMode(dc,COLORONCOLOR);StretchDIBits(dc,r.left,r.top,(int)(sw*zoom),(int)(sh*zoom),sx,height-sy-sh,sw,sh,pixels,&info,DIB_RGB_COLORS,SRCCOPY);
    free(indexed);free(pixels);
    RECT label=r;label.bottom=label.top+dip(26);HBRUSH b=CreateSolidBrush(RGB(28,35,39));FillRect(dc,&label,b);DeleteObject(b);
    SetTextColor(dc,RGB(241,245,245));SetBkMode(dc,TRANSPARENT);SelectObject(dc,u.font);
    char text[180];snprintf(text,sizeof(text),"  %s  |  %s  |  %d%%  |  Live %llu",p?"Read-only inspector":"Primary world",plane==1?"Surface":plane==2?"Black nest":"Red nest",view->zoom,(unsigned long long)s->generation);
    DrawTextA(dc,text,-1,&label,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
}
static void paint_canvas(DRAWITEMSTRUCT *d,int g) {
    int root_dpi=u.dpi;HFONT root_font=u.font;u.dpi=u.groups[g].dpi;u.font=u.groups[g].font;
    int p=panel_at(g);if(p<4)draw_world(d->hDC,d->rcItem,p);
    else {FillRect(d->hDC,&d->rcItem,GetSysColorBrush(COLOR_WINDOW));SetBkMode(d->hDC,TRANSPARENT);SetTextColor(d->hDC,GetSysColor(COLOR_WINDOWTEXT));SelectObject(d->hDC,u.font);
        DrawTextA(d->hDC,ws_name(p),-1,&d->rcItem,DT_CENTER|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);}
    if(d->itemState&ODS_FOCUS){RECT r=d->rcItem;InflateRect(&r,-3,-3);DrawFocusRect(d->hDC,&r);}
    u.dpi=root_dpi;u.font=root_font;
}
static int hit_group(POINT point) {
    for(int i=0;i<WS_NODES;++i)if(u.groups[i].visible){RECT r;GetWindowRect(u.groups[i].host,&r);if(PtInRect(&r,point))return i;}return -1;
}
static void targets(POINT point) {
    int g=hit_group(point);u.target_group=g;u.target_edge=-1;u.target_outer=0;
    RECT workspace;GetWindowRect(u.root,&workspace);int size=dip(40),gap=dip(6),cx=(workspace.left+workspace.right)/2,cy=(workspace.top+workspace.bottom)/2;
    RECT group=workspace;if(g>=0)GetWindowRect(u.groups[g].host,&group);
    int gx=(group.left+group.right)/2,gy=(group.top+group.bottom)/2;
    POINT pts[9]={{workspace.left+size,cy},{workspace.right-size,cy},{cx,workspace.top+size*2},{cx,workspace.bottom-size},
        {gx-size-gap,gy},{gx+size+gap,gy},{gx,gy-size-gap},{gx,gy+size+gap},{gx,gy}};
    const char *labels[]={"Left","Right","Top","Bottom","Left","Right","Above","Below","Tabs"};
    int selected=-1;
    for(int i=0;i<9;++i){if(!u.targets[i])u.targets[i]=CreateWindowExA(WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE|WS_EX_TOPMOST,"STATIC",labels[i],WS_POPUP|WS_BORDER|SS_CENTER|SS_CENTERIMAGE,0,0,1,1,u.root,NULL,GetModuleHandle(NULL),NULL);
        SendMessage(u.targets[i],WM_SETFONT,(WPARAM)u.font,0);RECT r={pts[i].x-size/2,pts[i].y-size/2,pts[i].x+size/2,pts[i].y+size/2};
        SetWindowPos(u.targets[i],HWND_TOPMOST,r.left,r.top,size,size,SWP_NOACTIVATE|SWP_SHOWWINDOW);if(PtInRect(&r,point))selected=i;}
    if(selected>=0){u.target_edge=selected<4?selected:selected-4;u.target_outer=selected<4;if(g<0)u.target_group=ws_group(&u.layout,0);
        RECT preview=u.target_outer?workspace:group;int edge=u.target_edge;
        if(edge==WS_LEFT)preview.right=(preview.left+preview.right)/2;else if(edge==WS_RIGHT)preview.left=(preview.left+preview.right)/2;
        else if(edge==WS_TOP)preview.bottom=(preview.top+preview.bottom)/2;else if(edge==WS_BOTTOM)preview.top=(preview.top+preview.bottom)/2;
        if(!u.preview){u.preview=CreateWindowExA(WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE|WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_TOPMOST,"STATIC","Dock preview",WS_POPUP|WS_BORDER,0,0,1,1,u.root,NULL,GetModuleHandle(NULL),NULL);SetLayeredWindowAttributes(u.preview,0,60,LWA_ALPHA);}
        SetWindowPos(u.preview,HWND_TOPMOST,preview.left,preview.top,preview.right-preview.left,preview.bottom-preview.top,SWP_NOACTIVATE|SWP_SHOWWINDOW);
    }else if(u.preview)ShowWindow(u.preview,SW_HIDE);
}
static void finish_drag(int apply) {
    int p=u.drag_panel;POINT point;GetCursorPos(&point);
    if(apply&&u.dragging){if(u.target_edge>=0&&u.target_group>=0)ws_move(&u.layout,p,panel_at(u.target_group),u.target_edge,u.target_outer);
        else {POINT client=point;ScreenToClient(u.root,&client);RECT r;GetClientRect(u.root,&r);if(!PtInRect(&r,client))ws_float(&u.layout,p,undip(point.x),undip(point.y),520,400);}}
    u.dragging=0;u.drag_panel=-1;ReleaseCapture();for(int i=0;i<9;++i)if(u.targets[i])ShowWindow(u.targets[i],SW_HIDE);if(u.preview)ShowWindow(u.preview,SW_HIDE);
    if(apply)commit_layout();
}
static LRESULT CALLBACK control_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp,UINT_PTR id,DWORD_PTR data) {
    int g=(int)data;Group *group=&u.groups[g];WsNode *n=&u.layout.nodes[g];
    if(shortcut(msg,wp))return 0;
    if(msg==WM_SETFOCUS)u.focus_group=g;
    if(msg==WM_CONTEXTMENU){POINT p;GetCursorPos(&p);panel_menu(g,p);return 0;}
    if(msg==WM_KEYDOWN&&id==3){WsNode *s=&u.layout.nodes[g];int delta=GetKeyState(VK_SHIFT)<0?100:20;
        if(wp==VK_HOME)s->ratio=500;else if(wp==VK_LEFT||wp==VK_UP)s->ratio-=delta;else if(wp==VK_RIGHT||wp==VK_DOWN)s->ratio+=delta;else return DefSubclassProc(h,msg,wp,lp);
        if(s->ratio<50)s->ratio=50;if(s->ratio>950)s->ratio=950;commit_layout();return 0;}
    if(id==3&&(msg==WM_LBUTTONDOWN||msg==WM_MOUSEMOVE||msg==WM_LBUTTONUP)) {
        if(msg==WM_LBUTTONDOWN){u.split_drag=g+1;SetCapture(h);}
        if(u.split_drag==g+1){POINT p;GetCursorPos(&p);HWND parent=GetParent(h);ScreenToClient(parent,&p);RECT r=u.splits[g];WsNode *s=&u.layout.nodes[g];
            int extent=s->axis?r.bottom-r.top:r.right-r.left;int at=s->axis?p.y-r.top:p.x-r.left;s->ratio=extent?MulDiv(at,1000,extent):500;if(s->ratio<50)s->ratio=50;if(s->ratio>950)s->ratio=950;arrange();}
        if(msg==WM_LBUTTONUP){u.split_drag=0;ReleaseCapture();save();}return 0;
    }
    if(id==1){
        if(msg==WM_LBUTTONDOWN&&!gesture()){POINT p={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};ClientToScreen(h,&p);u.drag_start=p;TCHITTESTINFO hit={.pt={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)}};int tab=TabCtrl_HitTest(h,&hit);u.drag_panel=tab>=0&&tab<n->count?n->panels[tab]:-1;SetCapture(h);}
        if(msg==WM_MOUSEMOVE&&u.drag_panel>=0&&(wp&MK_LBUTTON)){POINT p={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};ClientToScreen(h,&p);if(abs(p.x-u.drag_start.x)>=dip(8)||abs(p.y-u.drag_start.y)>=dip(8))u.dragging=1;if(u.dragging)targets(p);}
        if(msg==WM_LBUTTONUP&&u.drag_panel>=0){int dragged=u.dragging;finish_drag(dragged);if(dragged)return 0;
            if(n->collapsed){ws_collapse(&u.layout,g);commit_layout();return 0;}}
        if(msg==WM_CAPTURECHANGED&&u.dragging)finish_drag(0);
    }
    if(id==2&&panel_at(g)<4){int p=panel_at(g);WsPanel *v=&u.layout.panels[p];
        if(msg==WM_MOUSEWHEEL){zoom(p,GET_WHEEL_DELTA_WPARAM(wp)>0);InvalidateRect(h,NULL,FALSE);save();return 0;}
        if(msg==WM_LBUTTONDOWN){SetFocus(h);SetCapture(h);u.drag_start=(POINT){GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};return 0;}
        if(msg==WM_MOUSEMOVE&&GetCapture()==h&&(wp&MK_LBUTTON)){int x=GET_X_LPARAM(lp),y=GET_Y_LPARAM(lp);v->x-=MulDiv(x-u.drag_start.x,9600,v->zoom*group->dpi);v->y-=MulDiv(y-u.drag_start.y,9600,v->zoom*group->dpi);if(v->x<0)v->x=0;if(v->y<0)v->y=0;if(v->x>2047)v->x=2047;if(v->y>1023)v->y=1023;u.drag_start=(POINT){x,y};InvalidateRect(h,NULL,FALSE);return 0;}
        if(msg==WM_LBUTTONUP){ReleaseCapture();save();return 0;}
    }
    if(msg==WM_KEYDOWN&&wp==VK_TAB){HWND next=GetNextDlgTabItem(group->host,h,GetKeyState(VK_SHIFT)<0);if(next)SetFocus(next);return 0;}
    return DefSubclassProc(h,msg,wp,lp);
}
static LRESULT CALLBACK group_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp) {
    int g=(int)GetWindowLongPtr(h,GWLP_USERDATA);
    if(msg==WM_NCCREATE){SetWindowLongPtr(h,GWLP_USERDATA,(LONG_PTR)((CREATESTRUCT *)lp)->lpCreateParams);return TRUE;}
    if(msg==WM_DRAWITEM){DRAWITEMSTRUCT *d=(DRAWITEMSTRUCT *)lp;
        if(d->CtlID==4)paint_canvas(d,g);
        else {DrawFrameControl(d->hDC,&d->rcItem,DFC_BUTTON,DFCS_BUTTONPUSH|((d->itemState&ODS_SELECTED)?DFCS_PUSHED:0));
            SetBkMode(d->hDC,TRANSPARENT);DrawTextA(d->hDC,u.layout.nodes[g].collapsed?"+":"-",-1,&d->rcItem,DT_CENTER|DT_VCENTER|DT_SINGLELINE);if(d->itemState&ODS_FOCUS){RECT r=d->rcItem;InflateRect(&r,-3,-3);DrawFocusRect(d->hDC,&r);}}
        return TRUE;}
    if(msg==WM_NOTIFY&&((NMHDR *)lp)->code==TCN_SELCHANGE){u.layout.nodes[g].active=TabCtrl_GetCurSel(u.groups[g].tab);commit_layout();focus_group(g);return 0;}
    if(msg==WM_COMMAND){int id=LOWORD(wp);if(id==2||id==4){POINT p;GetCursorPos(&p);panel_menu(g,p);}else if(id==3){ws_collapse(&u.layout,g);commit_layout();}return 0;}
    if(msg==WM_HSCROLL||msg==WM_VSCROLL)return 0;
    if(shortcut(msg,wp))return 0;return DefWindowProc(h,msg,wp,lp);
}
static void remember_float(int i) {
    if(u.building||u.applying||u.layout.floats[i].root<0)return;RECT r;GetWindowRect(u.floats[i],&r);
    MONITORINFOEXA m={.cbSize=sizeof(m)};GetMonitorInfoA(MonitorFromWindow(u.floats[i],MONITOR_DEFAULTTONEAREST),(MONITORINFO *)&m);
    int dpi=window_dpi(u.floats[i]);if(!dpi)dpi=u.dpi;
    WsFloat *f=&u.layout.floats[i];f->x=MulDiv(r.left-m.rcWork.left,96,dpi);f->y=MulDiv(r.top-m.rcWork.top,96,dpi);f->w=MulDiv(r.right-r.left,96,dpi);f->h=MulDiv(r.bottom-r.top,96,dpi);snprintf(f->monitor,sizeof(f->monitor),"%s",m.szDevice);save();
}
static LRESULT CALLBACK float_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp) {
    int i=(int)GetWindowLongPtr(h,GWLP_USERDATA);
    if(msg==WM_NCCREATE){SetWindowLongPtr(h,GWLP_USERDATA,(LONG_PTR)((CREATESTRUCT *)lp)->lpCreateParams);return TRUE;}
    if(msg==WM_SIZE&&!u.building){arrange();return 0;}
    if(msg==WM_EXITSIZEMOVE){remember_float(i);return 0;}
    if(msg==WM_GETMINMAXINFO){MINMAXINFO *m=(MINMAXINFO *)lp;m->ptMinTrackSize=(POINT){dip(320),dip(240)};return 0;}
    if(msg==WM_CLOSE){int root=u.layout.floats[i].root;int ids[WS_PANELS],count=0;
        /* Close hides every member; IDs are copied before tree compression. */
        for(int p=0;p<WS_PANELS;++p){int g=ws_group(&u.layout,p);HWND owner=g>=0?GetAncestor(u.groups[g].host,GA_ROOT):NULL;if(g>=0&&owner==h)ids[count++]=p;}
        (void)root;for(int j=0;j<count;++j)ws_hide(&u.layout,ids[j]);commit_layout();return 0;}
    if(msg==WM_DPICHANGED){RECT *r=(RECT *)lp;SetWindowPos(h,NULL,r->left,r->top,r->right-r->left,r->bottom-r->top,SWP_NOZORDER|SWP_NOACTIVATE);arrange();return 0;}
    if(shortcut(msg,wp))return 0;return DefWindowProc(h,msg,wp,lp);
}
static LRESULT CALLBACK root_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp,UINT_PTR id,DWORD_PTR data) {
    (void)id;(void)data;
    if(shortcut(msg,wp))return 0;
    if(msg==WM_COMMAND&&HIWORD(wp)==0&&LOWORD(wp)>=100&&LOWORD(wp)<1400){command(LOWORD(wp),u.focus_group);return 0;}
    if(msg==WM_SIZE){LRESULT result=DefSubclassProc(h,msg,wp,lp);arrange();return result;}
    if(msg==WM_GETMINMAXINFO){LRESULT result=DefSubclassProc(h,msg,wp,lp);MINMAXINFO *m=(MINMAXINFO *)lp;m->ptMinTrackSize=(POINT){dip(720),dip(480)};return result;}
    if(msg==WM_ERASEBKGND){RECT r;GetClientRect(h,&r);FillRect((HDC)wp,&r,GetSysColorBrush(COLOR_APPWORKSPACE));return 1;}
    if(msg==WM_PAINT){PAINTSTRUCT p;BeginPaint(h,&p);FillRect(p.hdc,&p.rcPaint,GetSysColorBrush(COLOR_APPWORKSPACE));EndPaint(h,&p);return 0;}
    if(msg==WM_DISPLAYCHANGE){for(int i=0;i<WS_FLOATS;++i)if(u.floats[i]&&u.layout.floats[i].root>=0){RECT r=float_rect(&u.layout.floats[i]);SetWindowPos(u.floats[i],NULL,r.left,r.top,r.right-r.left,r.bottom-r.top,SWP_NOZORDER|SWP_NOACTIVATE);}arrange();return 0;}
    if(msg==WM_DPICHANGED){u.dpi=HIWORD(wp);font();RECT *r=(RECT *)lp;SetWindowPos(h,NULL,r->left,r->top,r->right-r->left,r->bottom-r->top,SWP_NOZORDER|SWP_NOACTIVATE);arrange();return 0;}
    if(msg==WM_SETFOCUS){focus_group(u.focus_group);return 0;}
    if(msg==WM_KEYDOWN||msg==WM_KEYUP||msg==WM_CHAR||msg==WM_MOUSEWHEEL||msg==WM_LBUTTONDOWN||msg==WM_LBUTTONUP||msg==WM_MOUSEMOVE)return 0;
    return DefSubclassProc(h,msg,wp,lp);
}
int native_workspace_init(SDL_Window *root) {
    const char *enabled=getenv("SIMANT_ENHANCED_WORKSPACE");
    if(!enhanced_world_enabled()||(enabled&&!strcmp(enabled,"0")))return 0;
    HWND hwnd=SDL_GetPointerProperty(SDL_GetWindowProperties(root),SDL_PROP_WINDOW_WIN32_HWND_POINTER,NULL);
    if(!hwnd)return 0;memset(&u,0,sizeof(u));u.root=hwnd;u.sdl_id=SDL_GetWindowID(root);u.dpi=window_dpi(hwnd);if(!u.dpi)u.dpi=96;
    u.com_initialized=SUCCEEDED(CoInitializeEx(NULL,COINIT_APARTMENTTHREADED));
    u.drag_panel=-1;u.target_group=-1;u.target_edge=-1;u.focus_group=0;
    INITCOMMONCONTROLSEX controls={sizeof(controls),ICC_TAB_CLASSES|ICC_BAR_CLASSES};InitCommonControlsEx(&controls);
    WNDCLASSEXA cls={.cbSize=sizeof(cls),.lpfnWndProc=group_proc,.hInstance=GetModuleHandle(NULL),.hCursor=LoadCursor(NULL,IDC_ARROW),.hbrBackground=(HBRUSH)(COLOR_BTNFACE+1),.lpszClassName="SimAntWorkspaceGroup"};RegisterClassExA(&cls);
    cls.lpfnWndProc=float_proc;cls.lpszClassName="SimAntWorkspaceFloat";RegisterClassExA(&cls);font();ws_preset(&u.layout,0);
    const char *path=getenv("SIMANT_WORKSPACE_LAYOUT");
    if(path)snprintf(u.path,sizeof(u.path),"%s",path);
    else {char local[MAX_PATH];if(SUCCEEDED(SHGetFolderPathA(NULL,CSIDL_LOCAL_APPDATA,NULL,SHGFP_TYPE_CURRENT,local))){snprintf(u.path,sizeof(u.path),"%s\\SimAnt",local);CreateDirectoryA(u.path,NULL);size_t len=strlen(u.path);snprintf(u.path+len,sizeof(u.path)-len,"\\workspace-v1.txt");}}
    FILE *f=u.path[0]?fopen(u.path,"r"):NULL;
    if(f){if(!ws_read(&u.layout,f)){fclose(f);f=NULL;char bad[2100];snprintf(bad,sizeof(bad),"%s.rejected-%llu",u.path,(unsigned long long)GetTickCount64());CopyFileA(u.path,bad,TRUE);ws_preset(&u.layout,0);}if(f)fclose(f);}
    u.menu=CreateMenu();HMENU layouts=CreatePopupMenu(),panels=CreatePopupMenu();const char *presets[]={"Play","Colony","Research","Minimal"};
    for(int i=0;i<4;++i)AppendMenuA(layouts,MF_STRING,CMD_PRESET+i,presets[i]);AppendMenuA(layouts,MF_SEPARATOR,0,NULL);AppendMenuA(layouts,MF_STRING,CMD_RESET,"Reset Layout");
    for(int i=0;i<WS_PANELS;++i)AppendMenuA(panels,MF_STRING,CMD_REVEAL+i,ws_name(i));AppendMenuA(panels,MF_SEPARATOR,0,NULL);AppendMenuA(panels,MF_STRING,CMD_INSPECTOR,"New read-only inspector");
    AppendMenuA(u.menu,MF_POPUP,(UINT_PTR)layouts,"&Layout");AppendMenuA(u.menu,MF_POPUP,(UINT_PTR)panels,"&Panels");SetMenu(hwnd,u.menu);DrawMenuBar(hwnd);
    u.active=1;SetWindowSubclass(hwnd,root_proc,29,0);SetWindowTextA(hwnd,"SimAnt - Native Workspace Preview");
    SDL_SetWindowSize(root,dip(1120),dip(760));arrange();return 1;
}
int native_workspace_active(void){return u.active;}
void native_workspace_present(const HostPalette *palette) {
    if(!u.active)return;u.palette=*palette;
    const EnhancedSnapshot *s=enhanced_snapshot();
    if(s&&s->panels.game_type>=0){WsPanel *v=&u.layout.panels[0];
        if(!u.source_ready||u.source_plane!=s->world.plane){v->x=s->world.origin.x*16;v->y=s->world.origin.y*16;}
        else if(v->x>=0&&v->y>=0){v->x+=(s->world.origin.x-u.source_x)*16;v->y+=(s->world.origin.y-u.source_y)*16;}
        if(v->x<0)v->x=0;if(v->x>2047)v->x=2047;if(v->y<0)v->y=0;if(v->y>1023)v->y=1023;
        u.source_ready=1;u.source_plane=s->world.plane;u.source_x=s->world.origin.x;u.source_y=s->world.origin.y;
    }
    if(s){int present=ws_group(&u.layout,22);if(s->dialogs.modal) {
        if(present<0||panel_at(present)!=22||u.layout.nodes[present].collapsed){ws_prompt(&u.layout,1);arrange();}
    }else if(present>=0){ws_prompt(&u.layout,0);arrange();}}
    uint64_t now=SDL_GetTicksNS();if(now-u.last_paint<50000000)return;u.last_paint=now;
    u.generation=s?s->generation:0;
    for(int i=0;i<WS_NODES;++i)if(u.groups[i].visible&&!u.layout.nodes[i].collapsed){
        int p=panel_at(i);if(p<4&&s){WsPanel *v=&u.layout.panels[p];char text[256];int plane=p?v->plane:s->world.plane;
            snprintf(text,sizeof(text),"%s. %s. Live %llu. %s. Zoom %d percent. Camera %d, %d. Activate for view and layout commands.",ws_name(p),p?"Read only":"Primary",(unsigned long long)s->generation,plane==1?"Surface":plane==2?"Black nest":"Red nest",v->zoom,v->x,v->y);SetWindowTextA(u.groups[i].canvas,text);}
        InvalidateRect(u.groups[i].canvas,NULL,FALSE);UpdateWindow(u.groups[i].canvas);}
}
int native_workspace_filter(const SDL_Event *event) {
    if(!u.active)return 0;
    if(event->type==SDL_EVENT_KEY_DOWN||event->type==SDL_EVENT_KEY_UP||event->type==SDL_EVENT_TEXT_INPUT||event->type==SDL_EVENT_MOUSE_MOTION||event->type==SDL_EVENT_MOUSE_BUTTON_DOWN||event->type==SDL_EVENT_MOUSE_BUTTON_UP||event->type==SDL_EVENT_MOUSE_WHEEL){
        SDL_WindowID id=event->type==SDL_EVENT_KEY_DOWN||event->type==SDL_EVENT_KEY_UP?event->key.windowID:event->type==SDL_EVENT_MOUSE_MOTION?event->motion.windowID:event->type==SDL_EVENT_MOUSE_WHEEL?event->wheel.windowID:event->button.windowID;
        return id==u.sdl_id;}
    return 0;
}
int native_workspace_input(HostInputState *s){
    if(!u.active)return 0;
    SDL_Window *hover=SDL_GetMouseFocus();if(hover&&SDL_GetWindowID(hover)!=u.sdl_id)return 0;
    memset(s,0,sizeof(*s));s->x=320;s->y=240;return 1;
}
int native_workspace_operation(unsigned step){if(!u.active||gesture())return 0;ws_exercise(&u.layout,step);commit_layout();return ws_validate(&u.layout);}
const Workspace *native_workspace_layout(void){return u.active?&u.layout:NULL;}
int native_workspace_apply(const Workspace *w){if(!u.active||!ws_validate(w)||gesture())return 0;u.layout=*w;commit_layout();return 1;}
static void print_window(HDC output,HWND window,RECT bounds) {
    RECT r;GetWindowRect(window,&r);int width=r.right-r.left,height=r.bottom-r.top;
    HDC temp=CreateCompatibleDC(output);HBITMAP bmp=CreateCompatibleBitmap(output,width,height);HGDIOBJ old=SelectObject(temp,bmp);
    PrintWindow(window,temp,0);BitBlt(output,r.left-bounds.left,r.top-bounds.top,width,height,temp,0,0,SRCCOPY);
    SelectObject(temp,old);DeleteObject(bmp);DeleteDC(temp);
}
int native_workspace_capture(const char *path) {
    if(!u.active)return 0;RECT r;GetWindowRect(u.root,&r);int width=r.right-r.left,height=r.bottom-r.top;
    HWND windows[20];int count=0;windows[count++]=u.root;
    for(int i=0;i<WS_FLOATS;++i)if(u.floats[i]&&IsWindowVisible(u.floats[i]))windows[count++]=u.floats[i];
    for(int i=0;i<9;++i)if(u.targets[i]&&IsWindowVisible(u.targets[i]))windows[count++]=u.targets[i];
    for(int i=1;i<count;++i){RECT b;GetWindowRect(windows[i],&b);UnionRect(&r,&r,&b);}
    width=r.right-r.left;height=r.bottom-r.top;
    HDC dc=GetWindowDC(u.root),mem=CreateCompatibleDC(dc);HBITMAP bmp=CreateCompatibleBitmap(dc,width,height);HGDIOBJ old=SelectObject(mem,bmp);
    RECT canvas={0,0,width,height};FillRect(mem,&canvas,GetSysColorBrush(COLOR_APPWORKSPACE));
    for(int i=0;i<count;++i)print_window(mem,windows[i],r);
    BITMAPINFO info={.bmiHeader={.biSize=sizeof(BITMAPINFOHEADER),.biWidth=width,.biHeight=-height,.biPlanes=1,.biBitCount=32,.biCompression=BI_RGB}};
    void *pixels=malloc((size_t)width*height*4);SelectObject(mem,old);int okay=GetDIBits(mem,bmp,0,height,pixels,&info,DIB_RGB_COLORS)!=0;
    FILE *f=okay?fopen(path,"wb"):NULL;if(f){BITMAPFILEHEADER header={.bfType=0x4d42,.bfSize=54+width*height*4,.bfOffBits=54};fwrite(&header,14,1,f);fwrite(&info.bmiHeader,40,1,f);fwrite(pixels,4,width*height,f);fclose(f);}else okay=0;
    free(pixels);DeleteObject(bmp);DeleteDC(mem);ReleaseDC(u.root,dc);return okay;
}
void native_workspace_shutdown(void) {
    if(!u.active)return;save();RemoveWindowSubclass(u.root,root_proc,29);
    /* Children are reparented into the root before destroying floating owners. */
    for(int i=0;i<WS_NODES;++i){if(u.groups[i].host)DestroyWindow(u.groups[i].host);if(u.groups[i].font)DeleteObject(u.groups[i].font);if(u.splitters[i])DestroyWindow(u.splitters[i]);}
    for(int i=0;i<WS_FLOATS;++i)if(u.floats[i])DestroyWindow(u.floats[i]);
    for(int i=0;i<9;++i)if(u.targets[i])DestroyWindow(u.targets[i]);if(u.preview)DestroyWindow(u.preview);
    SetMenu(u.root,NULL);DestroyMenu(u.menu);DeleteObject(u.font);if(u.com_initialized)CoUninitialize();memset(&u,0,sizeof(u));
}
#else
int native_workspace_init(SDL_Window *root){(void)root;return 0;}
int native_workspace_active(void){return 0;}
void native_workspace_shutdown(void){}
void native_workspace_present(const HostPalette *p){(void)p;}
int native_workspace_filter(const SDL_Event *e){(void)e;return 0;}
int native_workspace_input(HostInputState *s){(void)s;return 0;}
int native_workspace_operation(unsigned step){(void)step;return 0;}
int native_workspace_capture(const char *path){(void)path;return 0;}
const Workspace *native_workspace_layout(void){return NULL;}
int native_workspace_apply(const Workspace *w){(void)w;return 0;}
#endif
