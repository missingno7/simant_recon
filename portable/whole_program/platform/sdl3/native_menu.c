#include "native_menu.h"
#include "native_workspace.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/menu_globals.h"
#include "../m1b73_event_enqueue.h"

#include <stdio.h>
#include <string.h>

/* Win16 SimAnt shows the game's kind-6 menu resource as a native menu bar
 * (InitMenu) and sends WM_COMMAND 0xFDxx to DoMenuEntry. The DOS pull-down
 * (S10 menu_track_popup) posts the same command space as a game event:
 * code = (menu << 4) + item - 0x2FF. Item state bytes (byte 0 of each title
 * and item string: 0x10 check, 0x20 none, | 0x80 disabled) stay owned by the
 * game (SetMenuItemState); the native menu only mirrors them. */

enum { MENU_TITLES = 16, MENU_ITEMS = 16, COMMAND_QUEUE = 16 };

static int commands[COMMAND_QUEUE];
static unsigned command_count;

/* A menu choice (native WM_COMMAND, or replay `menu FDxx`). */
int native_menu_command(int code)
{
    if ((code & 0xff00) != 0xfd00 || command_count == COMMAND_QUEUE) return 0;
    if(enhanced_contracts_enabled()){
          /* Shared commands use the original relocated control transaction,
           * including owner preparation. Yard menu routes alone omit that
           * preparation and can retain a different animation selection. */
          static const struct { int menu,control; } shared[]={
              {0xfd26,8},{0xfd27,9},{0xfd28,10},{0xfd41,15},
              {0xfd13,0x10f},{0xfd14,0x111},{0xfd15,0x113},
              {0xfd16,0x115},{0xfd17,0x114},{0xfd23,0x1909},{0xfd24,0x190a}
          };
          for(unsigned i=0;i<sizeof(shared)/sizeof(shared[0]);++i)
              if(code==shared[i].menu){code=shared[i].control;break;}
        int okay=enhanced_submit_event((unsigned)code,0,0,0)==ENHANCED_QUEUED;
        if(okay&&code==0xfd11)native_workspace_reveal_game();return okay;
    }
    commands[command_count++] = code;
    return 1;
}

void native_menu_pump(void)
{
    unsigned i;
    for (i = 0; i < command_count; ++i)
        portable_m1b73_event_enqueue_four_word_command((int16_t)(uint16_t)commands[i], 0, 0, 0, 0);
    command_count = 0;
}

#ifdef _WIN32
#include <windows.h>

static struct {
    HWND hwnd;
    WNDPROC original;
    HMENU bar;
    char labels[512][192]; unsigned label_count;
    HMENU scales;
    char ***built;                 /* g_6054 the bar was built from */
} m;

static const int ui_scales[]={0,100,125,150,175,200,250,300};
static void scale_checks(void){
    const Workspace *w=native_workspace_layout();if(!w||!m.scales)return;
    for(unsigned i=0;i<sizeof(ui_scales)/sizeof(ui_scales[0]);++i)CheckMenuItem(m.scales,0xe400+i,MF_BYCOMMAND|(w->ui_scale==ui_scales[i]?MF_CHECKED:MF_UNCHECKED));
}
static void themed_append(HMENU menu,UINT flags,UINT_PTR id,const char *text){
    AppendMenuA(menu,flags,id,text);
    if(flags&MF_SEPARATOR||m.label_count>=512)return;
    char *label=m.labels[m.label_count++];snprintf(label,192,"%s",text);
    MENUITEMINFOA item={.cbSize=sizeof(item),.fMask=MIIM_FTYPE|MIIM_DATA,.fType=MFT_OWNERDRAW,.dwItemData=(ULONG_PTR)label};
    SetMenuItemInfoA(menu,GetMenuItemCount(menu)-1,TRUE,&item);
}
void native_menu_theme_item(void *menu,unsigned position,const char *label){
    MENUITEMINFOA item={.cbSize=sizeof(item),.fMask=MIIM_FTYPE|MIIM_DATA,.fType=MFT_OWNERDRAW,.dwItemData=(ULONG_PTR)label};SetMenuItemInfoA((HMENU)menu,position,TRUE,&item);
}
int native_menu_theme_message(void *owner,unsigned msg,intptr_t param){
    if(msg!=WM_MEASUREITEM&&msg!=WM_DRAWITEM)return 0;
    if(msg==WM_MEASUREITEM){MEASUREITEMSTRUCT *v=(void *)param;if(v->CtlType!=ODT_MENU||!v->itemData)return 0;}
    else {DRAWITEMSTRUCT *v=(void *)param;if(v->CtlType!=ODT_MENU||!v->itemData)return 0;}
    HWND window=owner?(HWND)owner:m.hwnd;
    int dpi=native_workspace_ui_dpi(window);
    HFONT font=CreateFontA(-MulDiv(13,dpi,96),0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,"Tahoma");
    if(msg==WM_MEASUREITEM){MEASUREITEMSTRUCT *v=(void *)param;if(v->CtlType!=ODT_MENU){DeleteObject(font);return 0;}
        HDC dc=GetDC(window);HGDIOBJ old=SelectObject(dc,font);SIZE size;const char *label=(const char *)v->itemData;
        GetTextExtentPoint32A(dc,label,(int)strlen(label),&size);SelectObject(dc,old);ReleaseDC(window,dc);
        v->itemWidth=size.cx+MulDiv(40,dpi,96);v->itemHeight=MulDiv(26,dpi,96);
    }else if(msg==WM_DRAWITEM){DRAWITEMSTRUCT *v=(void *)param;if(v->CtlType!=ODT_MENU){DeleteObject(font);return 0;}
        int active=v->itemState&ODS_SELECTED;COLORREF paper=RGB(245,242,232),ink=RGB(36,43,33),earth=RGB(85,44,4);
        HBRUSH brush=CreateSolidBrush(active?earth:paper);FillRect(v->hDC,&v->rcItem,brush);DeleteObject(brush);
        HGDIOBJ old=SelectObject(v->hDC,font);SetTextColor(v->hDC,v->itemState&ODS_DISABLED?RGB(129,124,105):active?paper:ink);SetBkMode(v->hDC,TRANSPARENT);
        RECT r=v->rcItem;r.left+=MulDiv(24,dpi,96);r.right-=MulDiv(12,dpi,96);
        const char *label=(const char *)v->itemData;char text[192];snprintf(text,sizeof(text),"%s",label);char *tab=strchr(text,'\t');
        if(tab){*tab++=0;DrawTextA(v->hDC,tab,-1,&r,DT_SINGLELINE|DT_VCENTER|DT_RIGHT|DT_NOPREFIX);r.right-=MulDiv(60,dpi,96);}
        DrawTextA(v->hDC,text,-1,&r,DT_SINGLELINE|DT_VCENTER);
        MENUITEMINFOA submenu={.cbSize=sizeof(submenu),.fMask=MIIM_SUBMENU};
        if((HMENU)v->hwndItem!=m.bar&&GetMenuItemInfoA((HMENU)v->hwndItem,v->itemID,FALSE,&submenu)&&submenu.hSubMenu){
            int x=v->rcItem.right-MulDiv(8,dpi,96),y=(v->rcItem.top+v->rcItem.bottom)/2,t=MulDiv(3,dpi,96);POINT arrow[]={{x-t,y-t},{x+t,y},{x-t,y+t}};
            HBRUSH brush=CreateSolidBrush(GetTextColor(v->hDC));HGDIOBJ oldbrush=SelectObject(v->hDC,brush),oldpen=SelectObject(v->hDC,GetStockObject(NULL_PEN));Polygon(v->hDC,arrow,3);SelectObject(v->hDC,oldpen);SelectObject(v->hDC,oldbrush);DeleteObject(brush);
        }
        if(v->itemState&ODS_CHECKED){r=v->rcItem;r.left+=MulDiv(5,dpi,96);DrawTextW(v->hDC,L"\x2713",1,&r,DT_SINGLELINE|DT_VCENTER);}
        SelectObject(v->hDC,old);
    }else{DeleteObject(font);return 0;}
    DeleteObject(font);return 1;
}
static UINT command_of(int menu, int item) { return 0xFD01u + ((unsigned)menu << 4) + (unsigned)item; }

static void label(char *out, size_t size, const char *text)
{
    size_t length;
    snprintf(out, size, "%s", text && text[0] ? text + 1 : "");
    length = strlen(out);
    while (length && out[length - 1] == ' ') out[--length] = 0;
    while (out[0] == ' ') memmove(out, out + 1, strlen(out));
}

static const char *accelerator(unsigned id){
    switch(id){case 0xfd03:return "Ctrl+N";case 0xfd04:return "Ctrl+O";case 0xfd05:return "Ctrl+S";case 0xfd06:return "Ctrl+Shift+S";case 0xfd08:return "Alt+F4";
    case 0xfd11:return "Ctrl+1";case 0xfd12:return "Ctrl+2";case 0xfd13:return "Ctrl+3";case 0xfd14:return "Ctrl+4";case 0xfd15:return "Ctrl+5";case 0xfd16:return "Ctrl+6";case 0xfd17:return "Ctrl+7";
    case 0xfd41:return "P";case 0xfd43:return "1";case 0xfd44:return "2";case 0xfd45:return "3";case 0xfd46:return "4";}return "";
}
static void item_label(char *text,size_t size,const char *source,unsigned id){
    char base[128];label(base,sizeof(base),source);
    if(native_workspace_active()&&id==0xfd11)snprintf(base,sizeof(base),"Game");
    snprintf(text,size,"%s%s%s",base,native_workspace_active()&&*accelerator(id)?"\t":"",native_workspace_active()?accelerator(id):"");
}
static void refresh(HMENU popup, int menu)
{
    char **items = g_6054 ? g_6054[menu + 1] : NULL;
    int k;
    for (k = 0; items && items[k] && k < MENU_ITEMS; ++k) {
        unsigned char state = (unsigned char)items[k][0];
        if (items[k][1] == '-') continue;
        char text[192];item_label(text,sizeof(text),items[k],command_of(menu,k));
        MENUITEMINFOA paint={.cbSize=sizeof(paint),.fMask=MIIM_DATA};if(GetMenuItemInfoA(popup,command_of(menu,k),FALSE,&paint)&&paint.dwItemData)snprintf((char *)paint.dwItemData,192,"%s",text);
        char old[192];GetMenuStringA(popup,command_of(menu,k),old,sizeof(old),MF_BYCOMMAND);if(strcmp(old,text)){MENUITEMINFOA item={.cbSize=sizeof(item),.fMask=MIIM_STRING,.dwTypeData=text};SetMenuItemInfoA(popup,command_of(menu,k),FALSE,&item);}
        CheckMenuItem(popup, command_of(menu, k),
                      MF_BYCOMMAND | (((state & 0x7f) == 0x10) ? MF_CHECKED : MF_UNCHECKED));
        EnableMenuItem(popup, command_of(menu, k),
                       MF_BYCOMMAND | ((state & 0x80) ? MF_GRAYED : MF_ENABLED));
    }
}

static LRESULT CALLBACK menu_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    if(native_workspace_active()&&(msg==WM_MEASUREITEM||msg==WM_DRAWITEM)&&native_menu_theme_message(hwnd,msg,lparam))return TRUE;
    if(msg==WM_COMMAND&&HIWORD(wparam)==0&&LOWORD(wparam)>=0xe400&&LOWORD(wparam)<0xe408){
        native_workspace_set_ui_scale(ui_scales[LOWORD(wparam)-0xe400]);scale_checks();return 0;
    }
    if (msg == WM_COMMAND && HIWORD(wparam) == 0 && (LOWORD(wparam) & 0xff00) == 0xfd00) {
        native_menu_command(LOWORD(wparam));
        return 0;
    }
    if (msg == WM_INITMENUPOPUP && !HIWORD(lparam) && m.bar) {
        scale_checks();
        int menu = LOWORD(lparam);
        if ((HMENU)wparam == GetSubMenu(m.bar, menu)) refresh((HMENU)wparam, menu);
    }
    return CallWindowProc(m.original, hwnd, msg, wparam, lparam);
}

static void build(void)
{
    char **titles = g_6054[0];
    char text[192];
    int menu, k;
    m.label_count=0;m.scales=NULL;
    HMENU bar = CreateMenu();
    for (menu = 0; titles[menu] && menu < MENU_TITLES; ++menu) {
        char **items = g_6054[menu + 1];
        HMENU popup = CreatePopupMenu();
        for (k = 0; items && items[k] && k < MENU_ITEMS; ++k) {
            if (items[k][1] == '-') AppendMenuA(popup, MF_SEPARATOR, 0, NULL);
            else {
                item_label(text, sizeof(text), items[k],command_of(menu,k));
                if(native_workspace_active())themed_append(popup,MF_STRING,command_of(menu,k),text);else AppendMenuA(popup,MF_STRING,command_of(menu,k),text);
                fprintf(stderr, "Native menu %04X: %s\n", command_of(menu, k), text);
            }
        }
        if(menu==1&&native_workspace_active()){
            AppendMenuA(popup,MF_SEPARATOR,0,NULL);
            HMENU views=CreatePopupMenu();themed_append(views,MF_STRING,0xe102,"Black Nest");themed_append(views,MF_STRING,0xe103,"Red Nest");
            themed_append(popup,MF_POPUP,(UINT_PTR)views,"World views");
            themed_append(popup,MF_STRING,0xe100,"Reset window layout");
        }
        if(menu==3&&native_workspace_active()){
            m.scales=CreatePopupMenu();const char *labels[]={"Auto (per-monitor DPI)","100%","125%","150%","175%","200%","250%","300%"};
            for(unsigned i=0;i<8;++i)themed_append(m.scales,MF_STRING,0xe400+i,labels[i]);
            AppendMenuA(popup,MF_SEPARATOR,0,NULL);themed_append(popup,MF_POPUP,(UINT_PTR)m.scales,"UI Scale");scale_checks();
        }
        label(text, sizeof(text), titles[menu]);
        if(native_workspace_active()){char title[192];snprintf(title,sizeof(title),"&%s",text);snprintf(text,sizeof(text),"%s",title);}
        UINT flags=MF_POPUP|(((unsigned char)titles[menu][0]&0x80)?MF_GRAYED:0);
        if(native_workspace_active())themed_append(bar,flags,(UINT_PTR)popup,text);else AppendMenuA(bar,flags,(UINT_PTR)popup,text);
    }
    SetMenu(m.hwnd, bar);
    if (m.bar) DestroyMenu(m.bar);
    m.bar = bar;
    m.built = g_6054;
    DrawMenuBar(m.hwnd);
    fprintf(stderr, "Native menu bar: %d menus from the game's menu resource\n", menu);
}

int native_menu_init(SDL_Window *root)
{
    memset(&m, 0, sizeof(m));
    m.hwnd = (HWND)SDL_GetPointerProperty(SDL_GetWindowProperties(root),
                                          SDL_PROP_WINDOW_WIN32_HWND_POINTER, NULL);
    if (m.hwnd == NULL) return 0;            /* headless: no native menu */
    m.original = (WNDPROC)SetWindowLongPtr(m.hwnd, GWLP_WNDPROC, (LONG_PTR)menu_proc);
    return m.original != NULL;
}

int native_menu_sync(void)
{
    if (m.hwnd == NULL || g_6054 == NULL) return m.bar != NULL;
    if(g_6054!=m.built)build();
    for(int i=0;g_6054[0]&&g_6054[0][i]&&i<MENU_TITLES;++i){
        unsigned flag=((unsigned char)g_6054[0][i][0]&0x80)?MF_GRAYED:MF_ENABLED;
        if((GetMenuState(m.bar,i,MF_BYPOSITION)&MF_GRAYED)!=flag){EnableMenuItem(m.bar,i,MF_BYPOSITION|flag);DrawMenuBar(m.hwnd);}
        refresh(GetSubMenu(m.bar,i),i);
    }
    return 1;
}
void native_menu_shutdown(void)
{
    if (m.hwnd && m.original) SetWindowLongPtr(m.hwnd, GWLP_WNDPROC, (LONG_PTR)m.original);
    if (m.hwnd && m.bar) SetMenu(m.hwnd, NULL);
    if (m.bar) DestroyMenu(m.bar);
    memset(&m, 0, sizeof(m));
    command_count = 0;
}

#else
void native_menu_theme_item(void *menu,unsigned p,const char *label){(void)menu;(void)p;(void)label;}
int native_menu_theme_message(void *owner,unsigned m,intptr_t p){(void)owner;(void)m;(void)p;return 0;}
int native_menu_init(SDL_Window *root) { (void)root; return 0; }
int native_menu_sync(void) { return 0; }
void native_menu_shutdown(void) { command_count = 0; }
#endif
