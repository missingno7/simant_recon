/* Isolated fixed-width extraction of root:m0798.c event and geometry bodies.
 * Handler case/fallthrough/callback order is kept in source order.  DOS host
 * services below are test providers; this file is never linked into product. */
#include "source_control_events.h"

#include <string.h>

struct Rect { int16_t left, top, right, bottom; };
struct Pt { int16_t x, y; };
struct TriPoints { int16_t apexX, apexY, leftX, leftY, rightX, rightY; };
struct TriLevel { uint16_t frac, mid, weight; };
struct CtlMsg { uint8_t pad[8]; struct Pt pt; uint16_t code; };

static struct SourceFixture {
    int kind, sample_count, sample_at, still_calls;
    int16_t samples[8][2];
    struct Rect rect;
    SourceCtlResult *out;
} *active;

static int16_t ModeAuto, CasteAuto, g_1B4E, g_1B50, g_1B62, g_1B64;
static struct TriLevel modeLevels, casteLevels;
static struct TriLevel fd_3D57_0810[4], fd_3D57_07F2[4];
static struct TriPoints fd_50F6_3816, fd_50F6_3822;
static struct Pt fd_50F6_0358, fd_50F6_022E;
static uint16_t triWidth, triWidthL, triHeight;
static int16_t IdealCaste[4];

enum { OP_CLIP=1, OP_OFF, OP_HELP, OP_HIDE, OP_SHOW, OP_SELECT,
       OP_GETRECT, OP_DRAW, OP_POLL, OP_STILL };

static void note(int op, int a, int b, int c, int d, int e, int f, int g, int h)
{
    SourceCtlResult *o=active->out;
    int32_t *row;
    if(o->event_count>=64)return;
    row=o->events[o->event_count++];
    row[0]=op;row[1]=a;row[2]=b;row[3]=c;row[4]=d;
    row[5]=e;row[6]=f;row[7]=g;row[8]=h;
}
static void clip_SetWin(int id) { note(OP_CLIP,id,0,0,0,0,0,0,0); }
static void clip_Off(void) { note(OP_OFF,0,0,0,0,0,0,0,0); }
static void DoWinHelp(int id) { note(OP_HELP,id,0,0,0,0,0,0,0); }
static void win_MakeGroupInvisible(int win,int group) { note(OP_HIDE,win,group,0,0,0,0,0,0); }
static void win_MakeGroupVisible(int win,int group) { note(OP_SHOW,win,group,1,0,0,0,0,0); }
static void win_MakeObjSelected(int id) { note(OP_SELECT,id,0,0,0,0,0,0,0); }
static void win_GetObjRect(int id,struct Rect *r)
{ *r=active->rect;note(OP_GETRECT,id,r->left,r->top,r->right,r->bottom,0,0,0); }
static int16_t *source_selector(void) { return active->kind ? &g_1B4E : &g_1B50; }
static int16_t *source_percent(void) { return active->kind ? &g_1B64 : &g_1B62; }
static struct TriLevel *source_level(void) { return active->kind ? &casteLevels : &modeLevels; }
static struct TriLevel *source_rows(void) { return active->kind ? fd_3D57_07F2 : fd_3D57_0810; }
static int16_t *source_auto(void) { return active->kind ? &CasteAuto : &ModeAuto; }
static struct Pt *source_point(void) { return active->kind ? &fd_50F6_022E : &fd_50F6_0358; }
static struct TriPoints *source_tri(void) { return active->kind ? &fd_50F6_3822 : &fd_50F6_3816; }
static void source_draw(int flags)
{
    struct TriLevel *v=source_level();
    note(OP_DRAW,active->kind,flags,*source_percent(),v->frac,v->mid,
         v->weight,*source_selector(),*source_auto());
}
static void win_DrawCasteWindow(int flags) { source_draw(flags); }
static void win_DrawModeWindow(int flags) { source_draw(flags); }
static int _fmemcmp(const void *a,const void *b,uint16_t n) { return memcmp(a,b,n); }
static void *_fmemcpy(void *d,const void *s,uint16_t n) { return memcpy(d,s,n); }
static void f_1FD2_04D0(struct Pt *pt)
{
    if(active->sample_at<active->sample_count) {
        pt->x=active->samples[active->sample_at][0];
        pt->y=active->samples[active->sample_at][1];
        ++active->sample_at;
    }
    note(OP_POLL,pt->x,pt->y,0,0,0,0,0,0);
}
static int StillDown(void)
{
    int down;
    ++active->still_calls;
    down=active->still_calls<active->sample_count;
    note(OP_STILL,down,0,0,0,0,0,0,0);
    return down;
}
static void cvtLevels2IdealCaste(int16_t *ideal)
{
    ideal[0]=(int16_t)((100UL*casteLevels.mid+0x3fff)/0xffff);
    ideal[1]=(int16_t)((100UL*casteLevels.weight+0x3fff)/0xffff);
    ideal[2]=(int16_t)((50UL*casteLevels.frac+0x3fff)/0xffff);
    ideal[3]=(int16_t)((50UL*casteLevels.frac+0x3fff)/0xffff);
}

/* Body-origin src/root/m0798.c:261-285, mechanically width-adjusted. */
static int IsPointInIsoTri(struct Pt *pt,struct Rect *r)
{
    int16_t top,bottom,right,left,mid,x,y;
    int32_t edge;
    top=r->top;bottom=r->bottom;right=r->right;left=r->left;
    mid=(int16_t)((right+left)/2);x=pt->x;y=pt->y;
    if(y>=bottom||y<top)return 0;
    edge=(int32_t)(left-mid)*(y-bottom)/(int32_t)(bottom-top)+left;
    if(edge>x)return 0;
    edge=(int32_t)(mid-right)*(y-top)/(int32_t)(top-bottom)+mid;
    if(edge<x)return 0;
    return 1;
}
/* Body-origin src/root/m0798.c:287-322. */
static void BoundPointToTri(struct Pt *pt,struct Rect *r)
{
    int16_t top,bottom,right,left,mid,x,y;
    int32_t edge;
    top=r->top;bottom=(int16_t)(r->bottom-1);right=r->right;left=r->left;
    mid=(int16_t)((right+left)/2);x=pt->x;y=pt->y;
    if(y>bottom)y=bottom;else if(y<top)y=top;
    edge=(int32_t)(left-mid)*(y-bottom)/(int32_t)(bottom-top)+left;
    if(edge>x)x=(int16_t)edge;
    else { edge=(int32_t)(mid-right)*(y-top)/(int32_t)(top-bottom)+mid;
        if(edge<x)x=(int16_t)edge; }
    pt->x=x;pt->y=y;
}
/* Body-origin src/root/m0798.c:468-493. */
static void GetTriLatDist(struct TriLevel *level,struct TriPoints *tri,struct Pt *pt)
{
    int16_t dx,dy,row;
    uint16_t w;
    dx=(int16_t)(pt->x-tri->leftX);dy=(int16_t)(pt->y-tri->apexY);
    if((uint16_t)dy>(uint16_t)(triHeight-2))level->frac=0;
    else level->frac=(uint16_t)((int32_t)(triHeight-dy-2)*0xffff/(int32_t)(triHeight-2));
    w=(uint16_t)((uint32_t)level->frac*triWidthL/0xffffu);
    row=(int16_t)(triWidth-w*2u);
    if(row<=2){level->weight=level->mid=0;return;}
    if(dx-(int16_t)w>=row-2)level->weight=(uint16_t)(0xffffu-level->frac);
    else if(dx-(int16_t)w<=2)level->weight=0;
    else level->weight=(uint16_t)((int32_t)(0xffffu-level->frac)*(dx-(int16_t)w)/(row-2));
    level->mid=(uint16_t)(0xffffu-level->weight-level->frac);
}
/* Body-origin src/root/m0798.c:495-510, used only to project the draw knob. */
static void SetTriLatPoint(struct TriLevel *level,struct TriPoints *tri,struct Pt *out)
{
    uint16_t w=(uint16_t)((uint32_t)triWidthL*level->frac/0xffffu);
    int16_t row=(int16_t)(triWidth-w*2u);
    out->y=(int16_t)((uint32_t)(triHeight-2)*(0xffffu-level->frac)/0xffffu+tri->apexY);
    if(level->frac==0xffffu||row<3)out->x=(int16_t)(tri->apexX+2);
    else out->x=(int16_t)((int32_t)(row-3)*level->weight/(int32_t)(0xffffu-level->frac)+tri->leftX+w+2);
}

/* Source handler body origins: ProcCasteEvent src/root/m0798.c:130-196;
 * ProcModeEvent src/root/m0798.c:198-259. */
static void ProcCasteEvent(struct CtlMsg *msg)
{
    struct Rect rect;struct Pt last;
    clip_SetWin(0x1300);
    switch((int16_t)(msg->code-0x1303)) {
    case 0: DoWinHelp(0x130e);break;
    case 1: if(CasteAuto==0){CasteAuto=1;win_MakeGroupInvisible(0x1300,4);}break;
    case 3: case 4: case 5:
        win_MakeObjSelected(0x1305);
        _fmemcpy(&fd_3D57_07F2[g_1B4E],&casteLevels,6);
        g_1B4E=(int16_t)(msg->code-0x1306);
        _fmemcpy(&casteLevels,&fd_3D57_07F2[g_1B4E],6);
        clip_SetWin(0x1300);win_DrawCasteWindow(3); /* fall through */
    case 2: if(CasteAuto){CasteAuto=0;win_MakeGroupVisible(0x1300,4);}break;
    case 10:
        win_GetObjRect(0x130d,&rect);
        if(!IsPointInIsoTri(&msg->pt,&rect))break;
        if(CasteAuto){CasteAuto=0;win_MakeObjSelected(0x1305);win_MakeGroupVisible(0x1300,4);}
        last.x=-1;clip_SetWin(0x1300);
        do { if(_fmemcmp(&last,&msg->pt,4)) { last=msg->pt;BoundPointToTri(&msg->pt,&rect);
                GetTriLatDist(&casteLevels,&fd_50F6_3822,&msg->pt);win_DrawCasteWindow(3); }
            f_1FD2_04D0(&msg->pt);
        } while(StillDown());
        _fmemcpy(&fd_3D57_07F2[g_1B4E],&casteLevels,6);cvtLevels2IdealCaste(IdealCaste);break;
    case 12: case 13: case 14:g_1B64^=1;win_DrawCasteWindow(3);break;
    }
    clip_Off();
}
static void ProcModeEvent(struct CtlMsg *msg)
{
    struct Rect rect;struct Pt last;
    clip_SetWin(0x1200);
    switch((int16_t)(msg->code-0x1203)) {
    case 0:DoWinHelp(0x120e);break;
    case 1:if(ModeAuto==0){ModeAuto=1;win_MakeGroupInvisible(0x1200,4);}break;
    case 3:case 4:case 5:
        win_MakeObjSelected(0x1205);
        _fmemcpy(&fd_3D57_0810[g_1B50],&modeLevels,6);
        g_1B50=(int16_t)(msg->code-0x1206);
        _fmemcpy(&modeLevels,&fd_3D57_0810[g_1B50],6);
        clip_SetWin(0x1200);win_DrawModeWindow(3); /* fall through */
    case 2:if(ModeAuto){ModeAuto=0;win_MakeGroupVisible(0x1200,4);}break;
    case 10:
        win_GetObjRect(0x120d,&rect);
        if(!IsPointInIsoTri(&msg->pt,&rect))break;
        if(ModeAuto){ModeAuto=0;win_MakeObjSelected(0x1205);win_MakeGroupVisible(0x1200,4);}
        last.x=-1;clip_SetWin(0x1200);
        do { if(_fmemcmp(&last,&msg->pt,4)){last=msg->pt;BoundPointToTri(&msg->pt,&rect);
                GetTriLatDist(&modeLevels,&fd_50F6_3816,&msg->pt);win_DrawModeWindow(3);}
            f_1FD2_04D0(&msg->pt);
        } while(StillDown());
        _fmemcpy(&fd_3D57_0810[g_1B50],&modeLevels,6);break;
    case 12:case 13:case 14:g_1B62^=1;win_DrawModeWindow(3);break;
    }
    clip_Off();
}

int source_control_event_run(int kind,uint16_t code,int16_t start_auto,
    int16_t start_selector,int16_t start_percent,const int16_t rect[4],
    const uint16_t metrics[3],const int16_t initial_point[2],
    const int16_t control_point[2],const int16_t *samples,int sample_count,
    SourceCtlResult *result)
{
    struct SourceFixture fixture;struct CtlMsg msg;
    if(!result||!rect||!metrics||!initial_point||!control_point||
       sample_count<0||sample_count>8||(!samples&&sample_count)||kind<0||kind>1)return -1;
    memset(result,0,sizeof *result);memset(&fixture,0,sizeof fixture);
    active=&fixture;fixture.kind=kind;fixture.sample_count=sample_count;fixture.out=result;
    fixture.rect=(struct Rect){rect[0],rect[1],rect[2],rect[3]};
    for(int i=0;i<sample_count;i++){fixture.samples[i][0]=samples[2*i];fixture.samples[i][1]=samples[2*i+1];}
    triWidth=metrics[0];triHeight=metrics[1];triWidthL=metrics[2];
    memset(fd_3D57_0810,0,sizeof fd_3D57_0810);memset(fd_3D57_07F2,0,sizeof fd_3D57_07F2);
    fd_3D57_0810[0]=(struct TriLevel){0x9999,0x3333,0x3333};
    fd_3D57_0810[1]=(struct TriLevel){0xffff,0,0};
    fd_3D57_0810[2]=(struct TriLevel){0,0xffff,0};
    fd_3D57_0810[3]=(struct TriLevel){0,0,0xffff};
    fd_3D57_07F2[0]=(struct TriLevel){0,0x9999,0x6666};
    fd_3D57_07F2[1]=(struct TriLevel){0x7fff,0x3fff,0x3fff};
    fd_3D57_07F2[2]=(struct TriLevel){0,0xffff,0};
    fd_3D57_07F2[3]=(struct TriLevel){0,0,0xffff};
    modeLevels=(struct TriLevel){0x9999,0x3333,0x3333};
    casteLevels=(struct TriLevel){0,0x9999,0x6666};
    IdealCaste[0]=60;IdealCaste[1]=40;IdealCaste[2]=IdealCaste[3]=0;
    ModeAuto=CasteAuto=1;g_1B50=g_1B4E=0;g_1B62=g_1B64=1;
    if(kind==0){g_1B50=start_selector;g_1B62=start_percent;if(start_auto>=0)ModeAuto=start_auto;}
    else{g_1B4E=start_selector;g_1B64=start_percent;if(start_auto>=0)CasteAuto=start_auto;}
    if(start_selector<0||start_selector>3)return -2;
    fd_50F6_3816=(struct TriPoints){(int16_t)(rect[0]+((rect[2]-rect[0])/2)),rect[1],rect[0],rect[3],rect[2],rect[3]};
    fd_50F6_3822=fd_50F6_3816;
    fd_50F6_0358=(struct Pt){control_point[0],control_point[1]};
    fd_50F6_022E=fd_50F6_0358;
    memset(&msg,0,sizeof msg);msg.code=code;msg.pt=(struct Pt){initial_point[0],initial_point[1]};
    if(kind)ProcCasteEvent(&msg);else ProcModeEvent(&msg);
    for(int i=0;i<result->event_count;i++)
        if(result->events[i][0]==OP_DRAW){SetTriLatPoint(source_level(),source_tri(),source_point());break;}
    result->automatic=*source_auto();result->selector=*source_selector();result->percent=*source_percent();
    result->current[0]=source_level()->frac;result->current[1]=source_level()->mid;result->current[2]=source_level()->weight;
    for(int i=0;i<4;i++){struct TriLevel v=source_rows()[i];result->presets[i*3]=v.frac;result->presets[i*3+1]=v.mid;result->presets[i*3+2]=v.weight;}
    memcpy(result->ideal_caste,IdealCaste,sizeof IdealCaste);
    result->point[0]=source_point()->x;result->point[1]=source_point()->y;
    return 0;
}
