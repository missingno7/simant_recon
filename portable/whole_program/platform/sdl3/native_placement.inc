/* Overflow is a caption cascade, never a reduction of fixed clients. Older
 * captions sit above newer bodies; a two-column row is used only if needed. */
static int placement_visible(int p){
    if(p==WS_RESERVED||p>WS_INFO)return 0;
    Native *n=&u.windows[p];if(!n->h)return 0;
    if(!n->external)return u.ready&&u.layout.panels[p].visible;
    return IsWindowVisible(n->h);
}
static void orderly(RECT target[WS_PANELS]){
    int order[WS_PANELS],count=0;
    for(int p=0;p<WS_PANELS;++p)if(placement_visible(p)){
        if(!u.windows[p].opened)u.windows[p].opened=++u.opened;
        int i=count++;while(i&&u.windows[order[i-1]].opened>u.windows[p].opened){order[i]=order[i-1];--i;}order[i]=p;
    }
    HMONITOR done[WS_PANELS];int done_count=0;
    for(int i=0;i<count;++i){HMONITOR monitor=MonitorFromWindow(u.windows[order[i]].h,MONITOR_DEFAULTTONEAREST);int seen=0;for(int k=0;k<done_count;++k)seen|=done[k]==monitor;if(seen)continue;done[done_count++]=monitor;
        MONITORINFO info={.cbSize=sizeof(info)};GetMonitorInfo(monitor,&info);RECT work=info.rcWork;int members[WS_PANELS],n=0,overflow=0,caption=0;
        for(int k=0;k<count;++k){int p=order[k];if(MonitorFromWindow(u.windows[p].h,MONITOR_DEFAULTTONEAREST)!=monitor)continue;members[n++]=p;
            RECT frame;GetWindowRect(u.windows[p].h,&frame);POINT at={0,0};ClientToScreen(u.windows[p].h,&at);int h=at.y-frame.top;if(h>caption)caption=h;
            if(target[p].right>work.right||target[p].bottom>work.bottom)overflow=1;
        }
        for(int a=0;a<n;++a)for(int b=0;b<n;++b)if(a!=b){RECT cap=target[members[a]],hit;cap.bottom=cap.top+caption;if(IntersectRect(&hit,&cap,&target[members[b]]))overflow=1;}
        if(!overflow)continue;
        RECT main=main_client();int top=monitor==MonitorFromWindow(u.root,MONITOR_DEFAULTTONEAREST)?main.top:work.top+8;
        if(top<work.top+4)top=work.top+4;if(top>work.bottom-caption-4)top=work.top+4;
        int gap=4,columns=(top+n*(caption+gap)>work.bottom)?2:1,rows=(n+columns-1)/columns;
        int step=caption+gap;if(rows>1&&top+(rows-1)*step+caption>work.bottom)step=(work.bottom-top-caption)/(rows-1);
        for(int k=0;k<n;++k){RECT *r=&target[members[k]];int x=work.left+8+(columns==2?(k%2)*(work.right-work.left)/2:(k%4)*12),y=top+(k/columns)*step;
            OffsetRect(r,x-r->left,y-r->top);
        }
    }
}
