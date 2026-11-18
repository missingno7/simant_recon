/* A native device for OpenMiniMapWin. No source map or centring state is
 * written here: selection is replayed by the seam as an original 1401 hit. */
static struct {HWND h;int done,selected,held,entered,dpi;HFONT font;POINT point;RECT map,hit,origin;EnhancedSnapshot frame;} mini;
static void minimap_draw(HDC dc,RECT client,int unused){
    (void)unused;color_fill(dc,client,PAPER);FrameRect(dc,&client,GetStockObject(BLACK_BRUSH));
    HGDIOBJ old=SelectObject(dc,mini.font);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,INK);
    RECT title={scale(12,mini.dpi),scale(6,mini.dpi),client.right-scale(12,mini.dpi),scale(34,mini.dpi)};native_workspace_text_draw(dc,&title,"Minimap - choose a position",DT_SINGLELINE|DT_VCENTER,mini.dpi,2,INK);
    int saved=SaveDC(dc);SetGraphicsMode(dc,GM_ADVANCED);
    XFORM transform={(FLOAT)(mini.map.right-mini.map.left)/512,0,0,(FLOAT)(mini.map.bottom-mini.map.top)/256,(FLOAT)mini.map.left,(FLOAT)mini.map.top};
    SetWorldTransform(dc,&transform);content_map(dc,&mini.frame);RestoreDC(dc,saved);
    if(mini.entered){int arm=scale(8,mini.dpi);HPEN pen=CreatePen(PS_SOLID,1,RUST);HGDIOBJ previous=SelectObject(dc,pen);MoveToEx(dc,mini.point.x-arm,mini.point.y,NULL);LineTo(dc,mini.point.x+arm+1,mini.point.y);MoveToEx(dc,mini.point.x,mini.point.y-arm,NULL);LineTo(dc,mini.point.x,mini.point.y+arm+1);SelectObject(dc,previous);DeleteObject(pen);}
    RECT hint={scale(12,mini.dpi),mini.map.bottom+scale(8,mini.dpi),client.right-scale(12,mini.dpi),client.bottom-scale(6,mini.dpi)};
    native_workspace_text_draw(dc,&hint,"Drag and release, or click a position.\nEsc or click outside to cancel.",DT_LEFT|DT_WORDBREAK,mini.dpi,0,INK);SelectObject(dc,old);
}
static LRESULT CALLBACK minimap_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp){
    if(msg==WM_ERASEBKGND)return 1;
    if(msg==WM_PAINT||msg==WM_PRINTCLIENT){PAINTSTRUCT ps;HDC dc=msg==WM_PAINT?BeginPaint(h,&ps):(HDC)wp;RECT r;GetClientRect(h,&r);buffered(dc,r,0,minimap_draw);if(msg==WM_PAINT)EndPaint(h,&ps);return 0;}
    if(msg==WM_KEYDOWN&&wp==VK_ESCAPE){mini.done=1;return 0;}
    if(msg==WM_CLOSE||msg==WM_CANCELMODE){mini.done=1;return 0;}
    if(msg==WM_LBUTTONDOWN||msg==WM_MOUSEMOVE||msg==WM_LBUTTONUP){
        POINT p={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};int inside=PtInRect(&mini.hit,p);
        if(msg==WM_LBUTTONDOWN){if(!inside){mini.done=1;return 0;}mini.held=1;}
        if(inside){mini.point=p;mini.entered=1;InvalidateRect(h,NULL,FALSE);}
        if(msg==WM_LBUTTONUP){
            /* The release that opens a click-driven menu belongs to MAP. A
             * held drag which reached the map has its ordinary release here. */
            if(mini.held&&(inside||mini.entered)){mini.done=1;mini.selected=inside;}
            else if(mini.held&&!PtInRect(&mini.origin,p))mini.done=1;
            mini.held=0;
        }
        return 0;
    }
    return DefWindowProc(h,msg,wp,lp);
}
int native_workspace_minimap(const EnhancedRect *source,const EnhancedRect *cursor,EnhancedPoint *point){
    (void)cursor;if(!u.active)return 0;
    proximity_preserve_focus();memset(&mini,0,sizeof(mini));mini.frame=*enhanced_snapshot();
    /* Mini_DrawMapI uses the current world plane, independently of MapMode. */
    if(mini.frame.overview.map_mode<4)mini.frame.overview.map_mode=mini.frame.world.plane;
    mini.frame.overview.map_frozen=0;
    int sw=source->right-source->left,sh=source->bottom-source->top;
    if(sw<=0||sh<=0)return 0;
    WNDCLASSEXA cls={.cbSize=sizeof(cls),.lpfnWndProc=minimap_proc,.hInstance=GetModuleHandle(NULL),.hCursor=LoadCursor(NULL,IDC_CROSS),.lpszClassName="SimAntMinimapPopup"};RegisterClassExA(&cls);
    HWND button=GetDlgItem(u.windows[WS_ANT].h,5);RECT anchor;GetWindowRect(button,&anchor);
    POINT at=prompt_anchor();mini.dpi=point_dpi(at);mini.font=make_font(mini.dpi);int width=scale(536,mini.dpi),height=scale(350,mini.dpi);
    MONITORINFO monitor={.cbSize=sizeof(monitor)};GetMonitorInfo(MonitorFromPoint(at,MONITOR_DEFAULTTONEAREST),&monitor);
    if(width>monitor.rcWork.right-monitor.rcWork.left)width=monitor.rcWork.right-monitor.rcWork.left;
    if(height>monitor.rcWork.bottom-monitor.rcWork.top)height=monitor.rcWork.bottom-monitor.rcWork.top;
    RECT bounds=prompt_bounds(at,width,height);mini.map=(RECT){MulDiv(12,width,536),MulDiv(38,height,350),MulDiv(524,width,536),MulDiv(294,height,350)};
    /* Nest maps occupy the middle 64 of the original 128 columns. Blank
     * gutters are outside, rather than hits the source would reject before
     * its next held check (and therefore before the queued close). */
    mini.hit=mini.map;
    if(mini.frame.world.plane==2||mini.frame.world.plane==3){int span=mini.map.right-mini.map.left;mini.hit.left=mini.map.left+(span+3)/4;mini.hit.right=mini.map.left+(span*3+3)/4;}
    mini.h=CreateWindowExA(WS_EX_TOOLWINDOW|WS_EX_TOPMOST,cls.lpszClassName,"Minimap - Esc cancels",WS_POPUP|WS_BORDER,bounds.left,bounds.top,width,height,u.root,NULL,cls.hInstance,NULL);
    if(!mini.h){DeleteObject(mini.font);return 0;}
    mini.origin=anchor;MapWindowPoints(NULL,mini.h,(POINT *)&mini.origin,2);
    mini.held=minimap_origin_down;minimap_origin_down=0;
    if(GetCapture())ReleaseCapture();ShowWindow(mini.h,SW_SHOW);SetForegroundWindow(mini.h);SetFocus(mini.h);SetCapture(mini.h);UpdateWindow(mini.h);
    MSG message;
    while(!mini.done){int r=GetMessage(&message,NULL,0,0);if(r<=0){if(!r)PostQuitMessage((int)message.wParam);break;}
        if(message.message==WM_KEYDOWN&&message.wParam==VK_ESCAPE){mini.done=1;continue;}
        if(message.message==WM_LBUTTONDOWN&&message.hwnd!=mini.h){mini.done=1;continue;}
        TranslateMessage(&message);DispatchMessage(&message);
    }
    if(mini.selected){
        /* Floor the half-open hit interval. MulDiv rounds the final native
         * pixel up to source->right/bottom, which the original loop rejects. */
        point->x=source->left+(int64_t)(mini.point.x-mini.map.left)*sw/(mini.map.right-mini.map.left);
        point->y=source->top+(int64_t)(mini.point.y-mini.map.top)*sh/(mini.map.bottom-mini.map.top);
    }
    if(GetCapture()==mini.h)ReleaseCapture();DestroyWindow(mini.h);DeleteObject(mini.font);mini.h=NULL;return mini.selected;
}
