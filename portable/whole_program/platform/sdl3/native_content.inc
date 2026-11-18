/* Native content paints. All source drawing still runs on hidden canonical
 * surfaces. These clients read semantic publications and immutable resources. */
static int content_panel(int p){return p>=WS_MAP&&p<=WS_STATUS;}
static void content_size(int p,int *w,int *h){
    ws_fixed_content(p,w,h);
}
static int content_owner(int p){static const int ids[]={0x100,0x1900,0x1200,0x1300,0x1500,0x500,0x1800};return content_panel(p)?ids[p-WS_MAP]:-1;}
static RECT content_rect(int l,int t,int r,int b){return (RECT){l,t,r,b};}
static void content_label(HDC dc,int x,int y,int w,int h,const char *s){text(dc,content_rect(x,y,x+w,y+h),s,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX);}
static void content_image(HDC dc,int id,int x,int y){native_workspace_art_paint(dc,id,x,y);}
static void content_line(HDC dc,int x,int y,int xx,int yy,COLORREF color,int width){HPEN pen=CreatePen(PS_SOLID,width,color);HGDIOBJ old=SelectObject(dc,pen);MoveToEx(dc,x,y,NULL);LineTo(dc,xx,yy);SelectObject(dc,old);DeleteObject(pen);}
static void content_map(HDC dc,const EnhancedSnapshot *s){
    uint8_t cells[128*64];int mode=s->overview.map_mode,nest=mode==2||mode==3;
    memset(cells,15,sizeof(cells));
    for(int y=0;y<64;++y)for(int x=0;x<128;++x){
        unsigned c=11;
        if(mode>=4&&mode<=8){static const int channels[]={2,3,4,5,0};unsigned v=s->world.scent[channels[mode-4]][x/2][y/2];c=v?(v>>5)+16:11;}
        else if(nest){if(x<32||x>=96)continue;unsigned life=(mode==2?s->world.life_black:s->world.life_red)[x-32][y];unsigned tile=(mode==2?s->world.black:s->world.red)[x-32][y];c=life?(life>=254?1:life&128?3:15):tile/4<40?s->overview.nest_colors[tile/4]:0;}
        else {unsigned life=s->world.life_surface[x][y],tile=s->world.surface[x][y];c=life?s->overview.life_colors[life>>3]:s->world.terrain_set?(tile<208?s->overview.house_colors[tile]:0):(tile<144?s->overview.terrain_colors[tile]:0);}
        cells[y*128+x]=(uint8_t)c;
    }
    /* The source's cached logical colour cells preserve its background toggle.
     * This is its 128x64 semantic map buffer, never a VGA/hosted raster plane. */
    if(s->overview.map_frozen&&mode<=3&&s->overview.map_cells_available){
        if(nest){for(int y=0;y<64;++y)memcpy(cells+y*128+32,s->overview.map_cells+y*64,64);}
        else memcpy(cells,s->overview.map_cells,sizeof(cells));
        /* Source fresh mode retains old background but still adds current life. */
        for(int y=0;y<64;++y)for(int x=0;x<128;++x){
            if(nest){if(x<32||x>=96)continue;unsigned life=(mode==2?s->world.life_black:s->world.life_red)[x-32][y];if(life)cells[y*128+x]=life>=254?1:life&128?3:15;}
            else {unsigned life=s->world.life_surface[x][y];if(life)cells[y*128+x]=s->overview.life_colors[life>>3];}
        }
    }
    draw_indexed(dc,content_rect(0,0,512,256),cells,128,64);
    if(s->world.spider_on&&s->world.plane==1&&!nest&&!s->overview.map_frozen)content_image(dc,1100+s->overview.spider_direction,(s->world.spider_x>>4)*4-3,(s->world.spider_y>>4)*4-3);
    if(s->overview.foot_here&&s->world.plane==1&&!s->overview.map_frozen){
        content_image(dc,1200+s->overview.boy_direction,s->overview.foot_x*4,s->overview.foot_y*4);
        if(s->overview.boy_here==3||s->overview.boy_here==4)content_image(dc,1210+(s->overview.boy_direction&1),s->overview.mower_x*4,s->overview.mower_y*4);
    }
    int pad=nest?32:0;
    int x=(s->world.origin.x+pad)*4,y=s->world.origin.y*4;
    int w=(s->world.hidden_viewport.right-s->world.hidden_viewport.left)/16*4,h=(s->world.hidden_viewport.bottom-s->world.hidden_viewport.top)/16*4;
    Native *game=&u.windows[WS_GAME];WsPanel *camera=&u.layout.panels[WS_GAME];
    if(game->h && camera->camera_x>=0 && camera->camera_y>=0){
        RECT client;GetClientRect(game->h,&client);double z=camera->zoom/100.0*game->dpi/96.0;
        int width=nest?1024:2048,sw=(int)(client.right/z),sh=(int)(client.bottom/z);
        if(sw>width-camera->camera_x)sw=width-camera->camera_x;if(sh>1024-camera->camera_y)sh=1024-camera->camera_y;
        x=camera->camera_x/4+pad*4;y=camera->camera_y/4;w=sw/4;h=sh/4;
    }
    RECT view={x,y,x+w,y+h};FrameRect(dc,&view,GetStockObject(BLACK_BRUSH));InflateRect(&view,-1,-1);HBRUSH b=CreateSolidBrush(RGB(255,243,4));FrameRect(dc,&view,b);DeleteObject(b);
}
static const char *allocation_names[2][3]={{"Forage","Dig","Nurse"},{"Breeders","Workers","Soldiers"}};
static void content_sync(int p);
static COLORREF content_palette(unsigned index){const uint8_t *rgb=u.palette.rgb[index&15];return RGB(rgb[0],rgb[1],rgb[2]);}
static const char *history_names[]={"Pop","Pop","Food","Food","Health","Health","S.Food","Eaten","Expired","Killed"};
static void content_allocation(HDC dc,const EnhancedSnapshot *s,int p){
    const EnhancedAllocationSnapshot *a=p==WS_BEHAVIOR?&s->panels.behavior:&s->panels.caste;
    RECT canvas={0,0,210,170};color_fill(dc,canvas,native_workspace_classic()?RGB(192,192,192):RGB(192,192,184));FrameRect(dc,&canvas,GetStockObject(BLACK_BRUSH));
    /* Shipped 4600/4620 already contain Set labels beneath their hit objects.
     * Hiding a source hit region does not erase that static decoration. */
    for(int i=0;i<3;++i)if(!(a->control_flags[i+3]&1)){
        RECT button={4,46+i*20,42,64+i*20};color_fill(dc,button,RGB(208,206,196));game_edge(dc,button,0,96);
        char label[16];snprintf(label,sizeof(label),"Set %d",i+1);text(dc,button,label,DT_CENTER|DT_VCENTER|DT_SINGLELINE|DT_NOPREFIX);
    }
    content_line(dc,112,42,180,132,EARTH,5);content_line(dc,44,133,178,133,EARTH,4);
    POINT tri[]={{110,42},{44,130},{176,130}};HGDIOBJ old=SelectObject(dc,GetStockObject(WHITE_BRUSH));Polygon(dc,tri,3);SelectObject(dc,old);
    content_line(dc,110,42,44,130,RGB(255,243,4),3);
    int tw=a->triangle.right-a->triangle.left,th=a->triangle.bottom-a->triangle.top;
    int x=44+(a->knob.x-a->triangle.left)*132/(tw?tw:1),y=42+(a->knob.y-a->triangle.top)*88/(th?th:1);
    content_image(dc,1400,x-7,y-7);
    const uint16_t levels[]={a->frac,a->mid,a->weight};
    int total=p==WS_BEHAVIOR?a->population[0]+a->population[1]+a->population[2]:a->population[0];
    RECT panel={181,4,209,94};color_fill(dc,panel,RGB(255,255,255));FrameRect(dc,&panel,GetStockObject(BLACK_BRUSH));
    for(int i=0;i<3;++i){char label[80];long value=((uint32_t)levels[i]*(a->percent?100:total)+0x3fff)/65535;
        if(a->percent)snprintf(label,sizeof(label),"%s",allocation_names[p==WS_CASTE][i]);else snprintf(label,sizeof(label),"%s %ld",allocation_names[p==WS_CASTE][i],value);
        int lx=i==0?78:i==1?40:142,ly=i==0?0:135;RECT box={lx,ly,lx+66,ly+35};
        color_fill(dc,box,RGB(255,255,255));HBRUSH edge=CreateSolidBrush(content_palette(a->bar_colors[i]));FrameRect(dc,&box,edge);DeleteObject(edge);
        content_label(dc,lx+2,ly+1,62,16,label);
        content_label(dc,lx+50,ly+18,14,16,"%");
        RECT bar={184+i*8,8,189+i*8,68};bar.top=bar.bottom-levels[i]*60/65535;
        if(bar.top+1<bar.bottom){color_fill(dc,bar,content_palette(a->bar_colors[i]));FrameRect(dc,&bar,GetStockObject(BLACK_BRUSH));}
    }
    HFONT small=CreateFontW(-11,0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Tahoma");
    HGDIOBJ was=SelectObject(dc,small);text(dc,content_rect(181,72,209,90),p==WS_BEHAVIOR?"FDN":"BWS",DT_CENTER|DT_SINGLELINE|DT_NOPREFIX);SelectObject(dc,was);DeleteObject(small);
}
static void content_history(HDC dc,const EnhancedSnapshot *s){
    const EnhancedHistorySnapshot *h=&s->history;RECT graph={8,8,312,116};color_fill(dc,graph,RGB(255,255,255));FrameRect(dc,&graph,GetStockObject(GRAY_BRUSH));
    static const COLORREF colors[]={RGB(0,92,129),RGB(160,45,40),RGB(0,101,16),RGB(146,113,56)};
    for(int slot=3;slot>=0;--slot){int g=h->shown[slot];if(g<0||g>9)continue;
        /* HistGraphs order differs from raw data order. See history_window.c. */
        static const int series[]={0,1,2,3,4,5,6,8,7,9};int which=series[g],max=1;
        for(int i=0;i<64;++i)if(h->samples[which][i]>max)max=h->samples[which][i];
        int px=9,py=115;
        for(int n=0;n<64;++n){int at=(h->start+n)&63;int x=9+n*300/64,y=115-h->samples[which][at]*104/max;if(n)content_line(dc,px,py,x,y,colors[h->colors[g]&3],1);px=x;py=y;}
        if(u.windows[WS_HISTORY].gesture){char value[24];snprintf(value,sizeof(value),"%d",h->samples[which][(h->start+63)&63]);RECT r={246,8+slot*23,310,30+slot*23};SetTextColor(dc,colors[h->colors[g]&3]);SetBkColor(dc,PAPER);SetBkMode(dc,OPAQUE);DrawTextA(dc,value,-1,&r,DT_RIGHT|DT_SINGLELINE|DT_NOPREFIX);}
    }
    content_label(dc,8,126,44,20,"Black");content_label(dc,8,152,44,20,"Red");
}
static unsigned content_be(const uint8_t *p){return (unsigned)p[0]*256+p[1];}
/* Native word layout also owns its hyperlink hit boxes. Stable source link
 * targets map back to the source draw-produced table; no source rect is edited. */
static void card_text(HDC dc,int id,RECT r){
    size_t n;const uint8_t *raw=enhanced_resource(id,10,&n);if(!raw)return;
    const EnhancedSnapshot *frame=enhanced_snapshot();Native *native=&u.windows[WS_INFO];
    int x=r.left,y=r.top-native->card_scroll,line=16;char word[256];
    int saved=SaveDC(dc);IntersectClipRect(dc,r.left,r.top,r.right,r.bottom);
    for(size_t at=0;at<n;){
        unsigned c=raw[at];if(!c){++at;continue;}
        if(c=='\r'||c=='\n'){x=r.left;y+=line;++at;continue;}
        if(c<=' '){x+=4;++at;continue;}
        size_t length=0;while(at<n&&raw[at]>' '&&length+1<sizeof(word))word[length++]=(char)raw[at++];word[length]=0;
        wchar_t wide[256];if(!MultiByteToWideChar(10000,0,word,-1,wide,256))wide[0]=0;
        SIZE extent;GetTextExtentPoint32W(dc,wide,(int)wcslen(wide),&extent);
        if(x+extent.cx>r.right&&x>r.left){x=r.left;y+=line;}
        int visible=y+line>r.top&&y<r.bottom;
        unsigned link=128;
        if(frame){char upper[256];memcpy(upper,word,length+1);CharUpperBuffA(upper,(DWORD)length);
            while(length && strchr(".,;:!?()",upper[length-1]))upper[--length]=0;
            for(unsigned i=0;i<frame->cards.link_count;++i)if(frame->cards.links[i].label[0]&&!strcmp(upper,frame->cards.links[i].label)){link=i;break;}
        }
        RECT rect={x,y,x+extent.cx,y+line};SetTextColor(dc,link<128?RGB(0,92,129):INK);SetBkMode(dc,TRANSPARENT);if(visible)DrawTextW(dc,wide,-1,&rect,DT_SINGLELINE|DT_NOPREFIX);
        if(link<128&&visible){content_line(dc,x,y+line-2,x+extent.cx,y+line-2,RGB(0,92,129),1);if(native->link_count<128){native->links[native->link_count].rect=rect;native->links[native->link_count++].index=link;}}
        x+=extent.cx;
    }
    int maximum=y+line+native->card_scroll-r.bottom;if(maximum>native->card_max)native->card_max=maximum;
    RestoreDC(dc,saved);
}
static void content_card(HDC dc,const EnhancedSnapshot *s){
    Native *native=&u.windows[WS_INFO];native->link_count=0;
    if(native->card_id!=s->cards.card){native->card_id=s->cards.card;native->card_scroll=native->card_max=0;}
    native->card_max=0;
    size_t n;const uint8_t *card=enhanced_resource(s->cards.card,17,&n);if(!card){content_label(dc,8,8,304,40,"Card resource unavailable");return;}
    size_t at=4;
    while(at+4<=n){unsigned kind=card[at];at+=4;
        if(kind=='P'){
            if(at+12>n)break;int id=content_be(card+at),y=content_be(card+at+2),x=content_be(card+at+4),links=content_be(card+at+10);at+=12;if((size_t)links>(n-at)/10)break;
            int footer=links>0&&y>=176;for(int i=0;i<links;++i){int target=(int16_t)content_be(card+at+i*10+8);if(target!=1&&target!=128)footer=0;}
            if(!footer)content_image(dc,id,x,y);at+=links*10;
        }else if(kind=='T'){
            if(at+10>n)break;RECT r={content_be(card+at+2),content_be(card+at),content_be(card+at+6),content_be(card+at+4)};unsigned frames=content_be(card+at+8);at+=10;
            if(frames>(n-at)/2)break;for(unsigned i=0;i<frames;++i){int id=content_be(card+at);at+=2;card_text(dc,id,r);}
        }else break;
    }
}
static void content_status(HDC dc,const EnhancedSnapshot *s){
    static const char *names[]={"Colony Health","Foraging","Eggs Hatched","Fights Won","Colonies Started","Colonies Held","Yard Filled","House Filled"};
    content_label(dc,8,8,140,20,"COLONY");content_label(dc,164,8,140,20,"EMPIRE");
    for(int i=0;i<8;++i){int x=i<4?8:164,y=26+(i&3)*22;char label[40];content_label(dc,x,y,114,22,names[i]);
        if(!s->history.score_metrics_available)snprintf(label,sizeof(label),"...");else if(i>=4&&s->panels.game_type!=2)snprintf(label,sizeof(label),"N.A.");else snprintf(label,sizeof(label),"%d%%",s->history.score_metrics[i]);content_label(dc,x+116,y,38,22,label);
    }
    content_line(dc,8,118,312,118,RGB(129,124,105),1);char score[80];snprintf(score,sizeof(score),"Overall %s Game Score\n%ld",s->panels.game_type==2?"Full":"Quick",(long)s->history.last_overall_score);text(dc,content_rect(8,124,312,160),score,DT_CENTER|DT_WORDBREAK);
}
static void content_yard(HDC dc,const EnhancedOverviewSnapshot *s){
    char status[300];native_text(status,sizeof(status),s->message);RECT status_box={0,0,488,0};int status_height=0;
    if(status[0]){DrawTextA(dc,status,-1,&status_box,DT_CALCRECT|DT_WORDBREAK|DT_NOPREFIX);status_height=status_box.bottom+8;}
    uint8_t *pixels=malloc(512*226);if(!pixels)return;
    EnhancedOverviewSnapshot yard=*s;yard.message[0]=yard.human_balloon[0]=0;yard.actors.count=0;
    /* These two animation IDs are source speech placeholders, not shipped art. */
    for(unsigned i=0;i<s->actors.count;++i)if(s->actors.poses[i].id!=30000&&s->actors.poses[i].id!=30001){unsigned n=yard.actors.count++;yard.actors.ids[n]=s->actors.ids[i];yard.actors.poses[n]=s->actors.poses[i];}
    enhanced_yard_draw(&yard,pixels,512,226,512);draw_indexed(dc,content_rect(0,0,512,226),pixels,512,226);free(pixels);
    for(unsigned i=0;i<s->actors.count;++i)if(s->actors.poses[i].id==30000&&s->human_balloon[0]){
        char message[300];native_text(message,sizeof(message),s->human_balloon);
        RECT extent={0,0,264,0};DrawTextA(dc,message,-1,&extent,DT_CALCRECT|DT_WORDBREAK|DT_NOPREFIX);
        int w=extent.right+16,h=extent.bottom+12,x=s->actors.poses[i].x,y=s->actors.poses[i].y+20-h;
        if(x+w>512)x=512-w;if(x<0)x=0;if(y<status_height+4)y=status_height+4;
        RECT bubble={x,y,x+w,y+h};color_fill(dc,bubble,PAPER);FrameRect(dc,&bubble,GetStockObject(BLACK_BRUSH));InflateRect(&bubble,-8,-6);text(dc,bubble,message,DT_WORDBREAK|DT_NOPREFIX);
    }
    if(status[0]){int width=status_box.right+16;if(width>504)width=504;RECT r={(512-width)/2,4,(512+width)/2,4+status_height};color_fill(dc,r,PAPER);InflateRect(&r,-8,-4);text(dc,r,status,DT_CENTER|DT_WORDBREAK|DT_NOPREFIX);}
}
static void content_draw(HDC dc,RECT client,int p){
    const EnhancedSnapshot *s=enhanced_snapshot();u.text_dpi=96;color_fill(dc,client,PAPER);if(!s)return;
    int w,h;content_size(p,&w,&h);int saved=SaveDC(dc);SetMapMode(dc,MM_ANISOTROPIC);SetWindowExtEx(dc,w,h,NULL);SetViewportExtEx(dc,client.right,client.bottom,NULL);HFONT font=make_font(96);SelectObject(dc,font);
    if(p==WS_MAP)content_map(dc,s);
    else if(p==WS_YARD)content_yard(dc,&s->overview);
    else if(p==WS_BEHAVIOR||p==WS_CASTE)content_allocation(dc,s,p);
    else if(p==WS_HISTORY)content_history(dc,s);
    else if(p==WS_INFO)content_card(dc,s);
    else if(p==WS_STATUS)content_status(dc,s);
    RestoreDC(dc,saved);DeleteObject(font);
}
static HWND content_button(int p,int id,const char *label,int x,int y,int w,int h){
    int base=content_owner(p);DWORD style=BS_OWNERDRAW;
    Native *n=&u.windows[p];HWND b=CreateWindowExA(0,"BUTTON",label,WS_CHILD|WS_VISIBLE|WS_TABSTOP|style,scale(x,n->dpi),scale(y,n->dpi),scale(w,n->dpi),scale(h,n->dpi),n->h,(HMENU)(INT_PTR)id,GetModuleHandle(NULL),NULL);SetPropA(b,"SimAntLogicalX",(HANDLE)(INT_PTR)(x+1));SetPropA(b,"SimAntLogicalY",(HANDLE)(INT_PTR)(y+1));SetPropA(b,"SimAntLogicalW",(HANDLE)(INT_PTR)w);SetPropA(b,"SimAntLogicalH",(HANDLE)(INT_PTR)h);SendMessage(b,WM_SETFONT,(WPARAM)n->font,TRUE);SetWindowSubclass(b,child_proc,71,0);return b;
}
static void content_children(int p){
    int base=content_owner(p);Native *n=&u.windows[p];
    if(p==WS_BEHAVIOR||p==WS_CASTE){
        content_button(p,base+4,"Auto",4,4,48,18);content_button(p,base+5,"Manual",4,24,48,18);
        for(int i=0;i<3;++i){char s[20];snprintf(s,sizeof(s),"Set %d",i+1);content_button(p,base+6+i,s,4,46+i*20,38,18);}
        for(int i=0;i<3;++i){char label[40];snprintf(label,sizeof(label),"%s percentage",allocation_names[p==WS_CASTE][i]);
            HWND edit=CreateWindowExA(0,"EDIT","",WS_CHILD|WS_VISIBLE|WS_TABSTOP|WS_BORDER|ES_RIGHT|ES_AUTOHSCROLL,scale(i==0?80:i==1?42:144,n->dpi),scale(i==0?17:152,n->dpi),scale(44,n->dpi),scale(17,n->dpi),n->h,(HMENU)(INT_PTR)(0xe520+i),GetModuleHandle(NULL),NULL);
            SetPropA(edit,"SimAntLogicalX",(HANDLE)(INT_PTR)((i==0?80:i==1?42:144)+1));SetPropA(edit,"SimAntLogicalY",(HANDLE)(INT_PTR)((i==0?17:152)+1));SetPropA(edit,"SimAntLogicalW",(HANDLE)(INT_PTR)44);SetPropA(edit,"SimAntLogicalH",(HANDLE)(INT_PTR)17);
            SendMessage(edit,WM_SETFONT,(WPARAM)n->font,TRUE);SendMessage(edit,EM_SETLIMITTEXT,12,0);SetWindowSubclass(edit,child_proc,71,0);
        }
        content_button(p,base+3,"Help",4,109,38,18);content_button(p,base+15,"% / #",4,130,38,18);
    }else if(p==WS_HISTORY){for(int i=0;i<10;++i)content_button(p,0x1503+i,history_names[i],52+(i/2)*49,126+(i&1)*26,47,22);}
    else if(p==WS_INFO){content_button(p,0xe510,"Previous",8,178,100,20);content_button(p,0xe511,"Top Card",112,178,100,20);}
    else if(p==WS_STATUS)content_button(p,0x180c,"Continue",60,160,200,22);
}
static void content_link(unsigned index,int hold){const EnhancedSnapshot *s=enhanced_snapshot();if(!s||index>=s->cards.link_count)return;const EnhancedRect *r=&s->cards.links[index].rect;
    const SimWindowRefEntry *e=&sim_window_ref_registry.entries[5];if(!e->bound||e->view.count<3)return;const uint8_t *b=(const uint8_t *)e->view.object_table[2];int x=(r->left+r->right)/2-sim_window_wire_read_i16(b,0),y=(r->top+r->bottom)/2-sim_window_wire_read_i16(b,2);
    if(enhanced_submit_pointer(0x502,x,y,0x200)==ENHANCED_QUEUED){
        u.info_popup=s->cards.links[index].target<0?-s->cards.links[index].target:0;
        Native *n=&u.windows[WS_INFO];n->gx=x;n->gy=y;n->gesture=hold;
        enhanced_pointer_update(x,y,hold);if(hold)SetCapture(n->h);
    }
}
static void content_edit_commit(int p,int axis){
    Native *n=&u.windows[p];if(!n->edit_dirty[axis])return;n->edit_dirty[axis]=0;
    char input[64],*end;HWND edit=GetDlgItem(n->h,0xe520+axis);GetWindowTextA(edit,input,sizeof(input));
    long value=strtol(input,&end,10);int valid=end!=input;while(*end==' '||*end=='\t')++end;
    if(*end=='%'){++end;while(*end==' '||*end=='\t')++end;}valid&=*end==0;
    if(valid){int percent=value<0?0:value>100?100:(int)value;enhanced_submit_allocation(content_owner(p),axis,percent);}
    content_sync(p);
}
static int content_command(int p,int id){

    if(p==WS_INFO&&(id==0xe510||id==0xe511)){const EnhancedSnapshot *s=enhanced_snapshot();if(s)for(unsigned i=0;i<s->cards.link_count;++i)if(s->cards.links[i].target==(id==0xe510?1:128)){content_link(i,0);break;}return 1;}
    if(p==WS_STATUS&&id==0x180c){
        /* The source may still be completing win_Open when this first frame
         * receives a click. Its own modal queue consumes the retained intent. */
        u.status_continue_pending=1;return 1;
    }

    return enhanced_submit_event(id,0,0,0)==ENHANCED_QUEUED;
}
static POINT content_pointer(int p,LPARAM lp){int w,h;content_size(p,&w,&h);RECT r;GetClientRect(u.windows[p].h,&r);POINT pt={MulDiv(GET_X_LPARAM(lp),w,r.right?r.right:1),MulDiv(GET_Y_LPARAM(lp),h,r.bottom?r.bottom:1)};return pt;}
static int content_mouse(HWND hwnd,int p,UINT msg,WPARAM wp,LPARAM lp){
    Native *n=&u.windows[p];const EnhancedSnapshot *s=enhanced_snapshot();if(!s)return 0;
    if(msg!=WM_LBUTTONDOWN&&msg!=WM_LBUTTONDBLCLK&&msg!=WM_LBUTTONUP&&msg!=WM_RBUTTONDOWN&&msg!=WM_RBUTTONDBLCLK&&msg!=WM_RBUTTONUP&&msg!=WM_MOUSEMOVE&&msg!=WM_CAPTURECHANGED)return 0;
    if(msg==WM_MOUSEMOVE&&!n->gesture)return 0;
    if(msg==WM_CAPTURECHANGED){if(n->gesture){enhanced_pointer_update(n->gx,n->gy,0);n->gesture=0;}return 0;}
    POINT at=content_pointer(p,lp);int event=0,x=at.x,y=at.y;
    if(p==WS_MAP){event=0x102;x/=4;y/=4;}
    else if(p==WS_YARD){event=0x1902;}
    else if(p==WS_BEHAVIOR||p==WS_CASTE){const EnhancedAllocationSnapshot *a=p==WS_BEHAVIOR?&s->panels.behavior:&s->panels.caste;event=content_owner(p)+13;x=(at.x-44)*(a->triangle.right-a->triangle.left)/132;y=(at.y-42)*(a->triangle.bottom-a->triangle.top)/88;if(!n->gesture&&(at.x<44||at.x>176||at.y<42||at.y>=130))return 0;}
    else if(p==WS_HISTORY){event=0x150e;x=(at.x-8)*1000/304;y=(at.y-8)*1000/108;if(!n->gesture&&(at.x<8||at.x>=312||at.y<8||at.y>=116))return 0;}
    else if(p==WS_INFO){if(msg==WM_LBUTTONUP){if(n->gesture){enhanced_pointer_update(n->gx,n->gy,0);n->gesture=0;ReleaseCapture();}return 1;}if(msg!=WM_LBUTTONDOWN)return 1;for(unsigned i=0;i<n->link_count;++i)if(PtInRect(&n->links[i].rect,at)){content_link(n->links[i].index,1);return 1;}for(unsigned i=0;i<s->cards.link_count;++i){if(s->cards.links[i].label[0])continue;const EnhancedRect *r=&s->cards.links[i].rect;const SimWindowRefEntry *e=&sim_window_ref_registry.entries[5];if(!e->bound)break;const uint8_t *b=(const uint8_t *)e->view.object_table[2];int left=sim_window_wire_read_i16(b,0),top=sim_window_wire_read_i16(b,2);RECT hit={r->left-left,r->top-top,r->right-left,r->bottom-top};if(PtInRect(&hit,at)){content_link(i,1);break;}}return 1;}
    if(!event)return 0;
    n->gx=x;n->gy=y;
    if(msg==WM_LBUTTONDOWN||msg==WM_LBUTTONDBLCLK||msg==WM_RBUTTONDOWN||msg==WM_RBUTTONDBLCLK){int mods=msg==WM_LBUTTONDBLCLK?0x2000:msg==WM_RBUTTONDBLCLK?0x4000:msg==WM_RBUTTONDOWN?0x800:0x200;if(enhanced_submit_pointer(event,x,y,mods)==ENHANCED_QUEUED){n->gesture=1;SetCapture(hwnd);SetFocus(hwnd);}}
    else if(n->gesture){enhanced_pointer_update(x,y,msg!=WM_LBUTTONUP&&msg!=WM_RBUTTONUP);if(msg==WM_LBUTTONUP||msg==WM_RBUTTONUP){n->gesture=0;ReleaseCapture();}}
    return 1;
}

/* content_sync runs every frame; these change a control only when its value differs,
 * so unchanged controls are never repainted (each set would otherwise redraw it). */
static void sync_check(HWND c,int on){if((SendMessage(c,BM_GETCHECK,0,0)==BST_CHECKED)!=!!on)SendMessage(c,BM_SETCHECK,on?BST_CHECKED:BST_UNCHECKED,0);}
static void sync_shown(HWND c,int on){if(!(GetWindowLong(c,GWL_STYLE)&WS_VISIBLE)!=!on)ShowWindow(c,on?SW_SHOWNA:SW_HIDE);}
static void sync_text(HWND c,const char *text){char current[160];GetWindowTextA(c,current,sizeof(current));if(strcmp(current,text))SetWindowTextA(c,text);}
static void content_sync(int p){
    const EnhancedSnapshot *s=enhanced_snapshot();if(!s)return;Native *n=&u.windows[p];
    n->syncing=1;
    if(p==WS_BEHAVIOR||p==WS_CASTE){const EnhancedAllocationSnapshot *a=p==WS_BEHAVIOR?&s->panels.behavior:&s->panels.caste;int base=content_owner(p);const uint16_t levels[]={a->frac,a->mid,a->weight};
        for(int i=0;i<6;++i){HWND button=GetDlgItem(n->h,base+3+i);sync_shown(button,a->control_flags[i]&1);EnableWindow(button,(a->control_flags[i]&2)!=0);}
        for(int i=0;i<3;++i)if(!n->edit_dirty[i]){char label[16];snprintf(label,sizeof(label),"%u",(levels[i]*100u+0x3fff)/65535);sync_text(GetDlgItem(n->h,0xe520+i),label);}
    }
    /* History selection is painted directly from the four source slots. */
    if(p==WS_INFO){
        size_t size;const uint8_t *title=enhanced_resource(s->cards.card,19,&size);char caption[160]="Info";
        if(title&&size<120){snprintf(caption,sizeof(caption),"Info - %s",title);for(char *c=caption;*c;++c)if(*c=='_')*c=' ';}
        sync_text(n->h,caption);
        SCROLLINFO si={.cbSize=sizeof(si),.fMask=SIF_RANGE|SIF_PAGE|SIF_POS,.nMin=0,.nMax=n->card_max+127,.nPage=128,.nPos=n->card_scroll},was={.cbSize=sizeof(was),.fMask=SIF_RANGE|SIF_PAGE|SIF_POS};
        if(!GetScrollInfo(n->h,SB_VERT,&was)||was.nMin!=si.nMin||was.nMax!=si.nMax||was.nPage!=si.nPage||was.nPos!=si.nPos)SetScrollInfo(n->h,SB_VERT,&si,TRUE);
        EnableWindow(GetDlgItem(n->h,0xe510),s->cards.previous[(s->cards.previous_index-1)&15]!=0);EnableWindow(GetDlgItem(n->h,0xe511),s->cards.card!=128);}
    if(p==WS_YARD){static const char *title[]={"Yard","House","Strategic","Graphic"};sync_text(n->h,title[s->overview.yard_mode&3]);}
    n->syncing=0;
}
