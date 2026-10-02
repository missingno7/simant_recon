#include "menu_quit_probe.h"
#include "../../game/resources/database.h"

#include <string.h>

typedef struct ProbeContext {
    const MenuQuitProbeInput *input;
    MenuQuitProbeResult *result;
    const char *text;
    size_t text_length;
    unsigned prompt, key_index, event_index, save_index;
    uintptr_t handle;
    int16_t dirty_after;
    int overflow;
} ProbeContext;

enum {
    EV_OPEN=1, EV_LOAD, EV_LOCK, EV_FONT, EV_RECT, EV_DECORATE, EV_FRAME,
    EV_COLOR, EV_PRINT, EV_KEY_READY, EV_KEY, EV_EVENT, EV_UNLOCK,
    EV_RELEASE, EV_CLOSE, EV_SAVE, EV_EXIT
};

static void record(ProbeContext *p, int kind, const int32_t *args, int argc,
                   const char *text, size_t text_length)
{
    MenuQuitProbeEvent *e;
    int i;
    if (p->result->event_count >= MQ_MAX_TRACE) { p->overflow=1; return; }
    e=&p->result->events[p->result->event_count++];
    memset(e,0,sizeof(*e)); e->kind=(int16_t)kind; e->argc=(int16_t)argc;
    for(i=0;i<argc && i<8;i++) e->args[i]=args[i];
    if(text_length>MQ_TEXT_CAP) { p->overflow=1; return; }
    if(text && text_length) memcpy(e->text,text,text_length);
    e->text_length=(uint16_t)text_length;
}
#define REC(k, ...) do { int32_t rec_args[]={__VA_ARGS__}; record(p,k,rec_args,(int)(sizeof(rec_args)/sizeof(rec_args[0])),NULL,0); } while(0)

int menu_quit_probe_load_resource(const char *root, char *buffer,
                                 size_t capacity, size_t *length)
{
    PortableDatabase db; PortableDbRecord rec; PortableDbStatus status;
    if(!root || !buffer || !length || capacity==0) return -1;
    memset(&db,0,sizeof(db));
    status=portable_db_open(&db,root);
    if(status!=PORTABLE_DB_OK) return -2;
    status=portable_db_load(&db,128,10,&rec);
    if(status!=PORTABLE_DB_OK) { portable_db_close(&db); return -3; }
    if(rec.size+1>capacity) { portable_db_record_free(&rec); portable_db_close(&db); return -4; }
    memcpy(buffer,rec.data,rec.size); buffer[rec.size]=0; *length=rec.size;
    portable_db_record_free(&rec); portable_db_close(&db); return 0;
}

static int open_window(void *ctx,int16_t win){ProbeContext*p=ctx;REC(EV_OPEN,win);return 1;}
static int load_resource(void *ctx,int16_t obj,int16_t kind,int16_t type,uintptr_t*h){ProbeContext*p=ctx;int32_t a[]={obj,kind,type};p->handle=0x12810;*h=p->handle;record(p,EV_LOAD,a,3,NULL,0);return 1;}
static int lock_resource(void *ctx,uintptr_t h,const char**t,size_t*n){ProbeContext*p=ctx;REC(EV_LOCK,(int32_t)h);*t=p->text;*n=p->text_length;return h==p->handle;}
static int set_font(void *ctx,int16_t f){ProbeContext*p=ctx;REC(EV_FONT,f);return 1;}
static int get_rect(void *ctx,int16_t obj,PortableMenuQuitRect*r){ProbeContext*p=ctx;const PortableMenuQuitRect*v=obj==0x2100?&p->input->window_rect:&p->input->text_rect;int32_t a[]={obj,v->left,v->top,v->right,v->bottom};*r=*v;record(p,EV_RECT,a,5,NULL,0);return 1;}
static int decorate(void *ctx,int16_t a,int16_t b,int16_t c){ProbeContext*p=ctx;REC(EV_DECORATE,a,b,c);return 1;}
static int frame(void *ctx,const PortableMenuQuitRect*r,int16_t w){ProbeContext*p=ctx;REC(EV_FRAME,r->left,r->top,r->right,r->bottom,w);return 1;}
static int color(void *ctx,int16_t obj){ProbeContext*p=ctx;REC(EV_COLOR,obj);return 1;}
static int print_text(void *ctx,int16_t first,const char*t,const PortableMenuQuitRect*r){ProbeContext*p=ctx;int32_t a[]={first,r->left,r->top,r->right,r->bottom};record(p,EV_PRINT,a,5,t,p->text_length);return 1;}
static int key_ready(void *ctx,int*ready){ProbeContext*p=ctx;*ready=p->key_index<p->input->key_count[p->prompt];REC(EV_KEY_READY,*ready);return 1;}
static int read_key(void *ctx,int16_t*k){ProbeContext*p=ctx;*k=p->input->keys[p->prompt][p->key_index++];REC(EV_KEY,*k);return 1;}
static int get_event(void *ctx,int*available,int16_t*code){ProbeContext*p=ctx;*available=p->event_index<p->input->event_count[p->prompt];*code=*available?p->input->events[p->prompt][p->event_index++]:0;REC(EV_EVENT,*available,*code);return 1;}
static int unlock(void *ctx,uintptr_t h){ProbeContext*p=ctx;REC(EV_UNLOCK,(int32_t)h);return 1;}
static int release(void *ctx,uintptr_t h){ProbeContext*p=ctx;REC(EV_RELEASE,(int32_t)h);return 1;}
static int close_window(void *ctx,int16_t win){ProbeContext*p=ctx;REC(EV_CLOSE,win);++p->prompt;p->key_index=0;p->event_index=0;return 1;}
static int save_game(void *ctx,int16_t last,int*saved){ProbeContext*p=ctx;*saved=p->save_index<p->input->save_count?p->input->saves[p->save_index++]:0;if(*saved)p->dirty_after=0;REC(EV_SAVE,last,*saved);return 1;}
static int exit_notice(void *ctx,const char*m,int16_t flag,int16_t code){ProbeContext*p=ctx;int32_t a[]={flag,code};record(p,EV_EXIT,a,2,m,strlen(m));return 1;}

int menu_quit_probe_run(const MenuQuitProbeInput *input,const char *text,
                        size_t text_length,MenuQuitProbeResult *result)
{
    ProbeContext p; PortableMenuQuitHost h; PortableMenuQuitInput in;
    PortableMenuQuitStatus status;
    if(!input||!text||!result||input->prompt_count>MQ_MAX_PROMPTS) return -1;
    memset(&p,0,sizeof(p)); memset(result,0,sizeof(*result));
    p.input=input;p.result=result;p.text=text;p.text_length=text_length;p.dirty_after=input->dirty;
    h=(PortableMenuQuitHost){&p,open_window,load_resource,lock_resource,set_font,
      get_rect,decorate,frame,color,print_text,key_ready,read_key,get_event,
      unlock,release,close_window,save_game,exit_notice};
    in=(PortableMenuQuitInput){input->dirty,input->screen_width_metric,
       input->frame_enabled,16};
    status=portable_menu_quit_run(&h,&in); result->status=(int16_t)status;
    result->dirty_after=p.dirty_after;
    return p.overflow?-2:0;
}
