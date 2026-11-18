/* Native menu presentation. The source transaction owns every result/command. */
#include "portable/whole_program/enhanced/proximity_labels.inc"
static POINT command_anchor;
static int anchor_valid, anchor_pending, proximity_open, proximity_modifiers;
static HFONT proximity_font;
static int proximity_dpi=96,prompt_dpi=96;
static EnhancedDialogsSnapshot proximity_menu;
static HWND proximity_return_focus;
static int source_modal_focus;
static void proximity_preserve_focus(void){
    if(proximity_return_focus)return;
    HWND origin=u.focus>=0&&u.focus<WS_PANELS?u.windows[u.focus].h:NULL,focus=GetFocus();
    if(!origin)origin=u.windows[WS_GAME].h;
    proximity_return_focus=focus&&origin&&(focus==origin||IsChild(origin,focus))?focus:origin;
}
static void proximity_restore_focus(const EnhancedSnapshot *s){
    if(proximity_open||!proximity_return_focus||!s||s->dialogs.modal)return;
    HWND target=proximity_return_focus;
    if(!IsWindow(target)){proximity_return_focus=NULL;return;}
    if(!IsWindowEnabled(target))return;
    proximity_return_focus=NULL;
    HWND frame=GetAncestor(target,GA_ROOT);SetForegroundWindow(frame);SetFocus(target);
}
static POINT prompt_anchor(void);
static RECT prompt_bounds(POINT,int,int);
static HWND command_prompt;
static int command_tool=-1;
static char command_text[160];

static LRESULT CALLBACK command_prompt_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp){
    if(msg==WM_NCHITTEST)return HTTRANSPARENT;
    if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
    if(msg==WM_ERASEBKGND)return 1;
    if(msg==WM_PAINT||msg==WM_PRINTCLIENT){
        PAINTSTRUCT ps;HDC dc=msg==WM_PAINT?BeginPaint(h,&ps):(HDC)wp;RECT r;GetClientRect(h,&r);
        color_fill(dc,r,PAPER);FrameRect(dc,&r,GetStockObject(BLACK_BRUSH));InflateRect(&r,-scale(8,prompt_dpi),-scale(6,prompt_dpi));
        HFONT font=make_font(prompt_dpi);HGDIOBJ old=SelectObject(dc,font);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,INK);
        native_workspace_text_draw(dc,&r,command_text,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX,prompt_dpi,0,INK);SelectObject(dc,old);DeleteObject(font);
        if(msg==WM_PAINT)EndPaint(h,&ps);return 0;
    }
    return DefWindowProc(h,msg,wp,lp);
}
static void command_prompt_sync(const EnhancedSnapshot *s){
    int tool=s?(s->panels.yard_wait?12:s->panels.tool):-1;
    if(tool!=10&&tool!=11&&tool!=12){if(command_prompt)ShowWindow(command_prompt,SW_HIDE);command_tool=-1;return;}
    if(!command_prompt){
        WNDCLASSEXA cls={.cbSize=sizeof(cls),.lpfnWndProc=command_prompt_proc,.hInstance=GetModuleHandle(NULL),.lpszClassName="SimAntCommandPrompt"};RegisterClassExA(&cls);
        command_prompt=CreateWindowExA(WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE|WS_EX_TRANSPARENT,cls.lpszClassName,"SimAnt command prompt",WS_POPUP,0,0,1,1,u.root,NULL,cls.hInstance,NULL);
    }
    char text[160];native_text(text,sizeof(text),s->panels.prompt);
    if(tool!=command_tool||strcmp(text,command_text)||prompt_dpi!=point_dpi(prompt_anchor())){
        prompt_dpi=point_dpi(prompt_anchor());
        command_tool=tool;snprintf(command_text,sizeof(command_text),"%s",text);
        HDC dc=GetDC(command_prompt);HFONT font=make_font(prompt_dpi);HGDIOBJ old=SelectObject(dc,font);
        RECT r={0,0,scale(300,prompt_dpi),0};DrawTextA(dc,text,-1,&r,DT_CALCRECT|DT_WORDBREAK|DT_NOPREFIX);
        SelectObject(dc,old);DeleteObject(font);ReleaseDC(command_prompt,dc);
        r=prompt_bounds(prompt_anchor(),r.right+scale(16,prompt_dpi),r.bottom+scale(12,prompt_dpi));
        SetWindowPos(command_prompt,HWND_TOP,r.left,r.top,r.right-r.left,r.bottom-r.top,SWP_NOACTIVATE|SWP_SHOWWINDOW);InvalidateRect(command_prompt,NULL,FALSE);
    }
}

void native_workspace_anchor(int x,int y){command_anchor=(POINT){x,y};anchor_valid=anchor_pending=1;}
void native_workspace_activate_point(int x,int y){command_anchor=(POINT){x,y};anchor_valid=1;anchor_pending=0;}
void native_workspace_request_point(int *x,int *y){POINT p;if(anchor_pending){p=command_anchor;anchor_pending=0;}else p=native_cursor_point();*x=p.x;*y=p.y;}
int native_workspace_proximity_modifiers(void){return proximity_modifiers;}
static POINT prompt_anchor(void){return anchor_valid?command_anchor:native_cursor_point();}
static RECT prompt_bounds(POINT at,int width,int height){
    MONITORINFO monitor={.cbSize=sizeof(monitor)};
    GetMonitorInfo(MonitorFromPoint(at,MONITOR_DEFAULTTONEAREST),&monitor);
    int gap=scale(8,point_dpi(at));
    RECT r={at.x+gap,at.y+gap,at.x+gap+width,at.y+gap+height},work=monitor.rcWork;
    if(r.right>work.right)OffsetRect(&r,work.right-r.right,0);
    if(r.bottom>work.bottom)OffsetRect(&r,0,work.bottom-r.bottom);
    if(r.left<work.left)OffsetRect(&r,work.left-r.left,0);
    if(r.top<work.top)OffsetRect(&r,0,work.top-r.top);
    return r;
}
void native_workspace_place_prompt(SDL_Window *window){
    if(!u.active)return;
    HWND h=SDL_GetPointerProperty(SDL_GetWindowProperties(window),SDL_PROP_WINDOW_WIN32_HWND_POINTER,NULL);
    RECT r;GetWindowRect(h,&r);r=prompt_bounds(prompt_anchor(),r.right-r.left,r.bottom-r.top);
    SetWindowPos(h,HWND_TOP,r.left,r.top,0,0,SWP_NOSIZE|SWP_NOACTIVATE);
}
static int proximity_message(UINT msg,LPARAM lp){
    if(!proximity_open)return 0;
    if(msg==WM_MEASUREITEM){
        MEASUREITEMSTRUCT *m=(void *)lp;if(m->CtlType!=ODT_MENU)return 0;
        const EnhancedObjectSnapshot *o=(void *)m->itemData;
        HDC dc=GetDC(u.root);HGDIOBJ old=SelectObject(dc,proximity_font);SIZE size;
        size.cx=native_workspace_text_width(dc,o->text,proximity_dpi,0);SelectObject(dc,old);ReleaseDC(u.root,dc);
        m->itemWidth=size.cx+scale(48,proximity_dpi);m->itemHeight=scale(28,proximity_dpi);return 1;
    }
    if(msg==WM_DRAWITEM){
        DRAWITEMSTRUCT *d=(void *)lp;if(d->CtlType!=ODT_MENU)return 0;
        const EnhancedObjectSnapshot *o=(void *)d->itemData;
        int selected=d->itemState&ODS_SELECTED,disabled=d->itemState&ODS_DISABLED;
        color_fill(d->hDC,d->rcItem,selected?RGB(85,44,4):PAPER);
        HGDIOBJ old=SelectObject(d->hDC,proximity_font);SetBkMode(d->hDC,TRANSPARENT);
        SetTextColor(d->hDC,disabled?RGB(129,124,105):selected?PAPER:INK);
        RECT r=d->rcItem;r.left+=scale(28,proximity_dpi);r.right-=scale(8,proximity_dpi);
        native_workspace_text_draw(d->hDC,&r,o->text,DT_SINGLELINE|DT_VCENTER|DT_NOPREFIX,proximity_dpi,0,GetTextColor(d->hDC));
        if(d->itemState&ODS_CHECKED){r=d->rcItem;r.left+=scale(8,proximity_dpi);DrawTextW(d->hDC,L"\x2713",1,&r,DT_SINGLELINE|DT_VCENTER|DT_NOPREFIX);}
        SelectObject(d->hDC,old);return 1;
    }
    return 0;
}
int native_workspace_proximity(const EnhancedDialogsSnapshot *menu){
    if(!u.active||!menu)return -1;
    /* Source win_Open can already have disabled the world by this point.
     * u.focus retains the originating native panel across that focus loss. */
    proximity_preserve_focus();
    proximity_menu=*menu;proximity_open=1;proximity_dpi=point_dpi(prompt_anchor());proximity_font=make_font(proximity_dpi);
    HMENU popup=CreatePopupMenu();HBRUSH paper=CreateSolidBrush(PAPER);
    MENUINFO info={.cbSize=sizeof(info),.fMask=MIM_BACKGROUND,.hbrBack=paper};SetMenuInfo(popup,&info);
    for(unsigned i=0;i<proximity_menu.object_count;++i){
        EnhancedObjectSnapshot *o=&proximity_menu.objects[i];
        if(o->id<menu->owner+2||!o->text[0]||!(o->flags&1))continue;
        AppendMenuA(popup,MF_OWNERDRAW|((o->flags&2)?0:MF_GRAYED)|((o->flags&4)||o->id==menu->proximity_item?MF_CHECKED:0),
            (UINT_PTR)(unsigned short)o->id,(LPCSTR)o);
    }
    if(!GetMenuItemCount(popup)){
        /* The full-game Tools resource has no selectable hit objects. */
        if(menu->owner==0xb00){
            EnhancedObjectSnapshot *o=&proximity_menu.objects[proximity_menu.object_count++];memset(o,0,sizeof(*o));
            snprintf(o->text,sizeof(o->text),"%s",proximity_label(5011,0));
            AppendMenuA(popup,MF_OWNERDRAW|MF_GRAYED,menu->owner+1,(LPCSTR)o);
        }else{
            DestroyMenu(popup);DeleteObject(paper);DeleteObject(proximity_font);proximity_font=NULL;proximity_open=0;proximity_return_focus=NULL;return -1;
        }
    }
    /* Native capture ownership ends the originating world drag. No second
     * processEdit request is generated by the menu's real release. */
    if(GetCapture())ReleaseCapture();
    native_workspace_present(&u.palette);
    for(int p=0;p<WS_PANELS;++p)if(u.windows[p].h)UpdateWindow(u.windows[p].h);
    POINT at=prompt_anchor();RECT position=prompt_bounds(at,1,1);
    SetForegroundWindow(u.root);
    unsigned result=TrackPopupMenuEx(popup,TPM_RETURNCMD|TPM_NONOTIFY|TPM_LEFTALIGN|TPM_TOPALIGN|TPM_RIGHTBUTTON,
        position.left,position.top,u.root,NULL);
    proximity_modifiers=(GetKeyState(VK_SHIFT)<0?2:0)|(GetKeyState(VK_CONTROL)<0?4:0)|(GetKeyState(VK_MENU)<0?8:0);
    DestroyMenu(popup);DeleteObject(paper);DeleteObject(proximity_font);proximity_font=NULL;proximity_open=0;
    PostMessage(u.root,WM_NULL,0,0);
    return result?(int)result:menu->owner+1;
}
