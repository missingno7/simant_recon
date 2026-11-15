#include "workspace.h"
#include <string.h>
#include <stdlib.h>
static const char *names[WS_PANELS]={"World","Inspector 1","Inspector 2","Inspector 3",
    "Ant / World Controls","Colony Operations","Overview","Minimap","Behavior","Caste",
    "History","Info","Status","Population","Help","Inspect","Messages","Tools",
    "Welcome","New Game","Results","About","Prompt","Debug"};
const char *ws_name(int p){return p>=0&&p<WS_PANELS?names[p]:"Unknown";}
static int alloc_node(Workspace *w,int kind) {
    for(int i=0;i<WS_NODES;++i)if(!w->nodes[i].kind){memset(&w->nodes[i],0,sizeof(WsNode));w->nodes[i].kind=kind;return i;}
    return -1;
}
static int tabs(Workspace *w,int p) {int n=alloc_node(w,1);if(n>=0){w->nodes[n].count=1;w->nodes[n].panels[0]=p;}return n;}
static int split(Workspace *w,int a,int b,int axis,int ratio) {
    int n=alloc_node(w,2);if(n>=0){w->nodes[n].a=a;w->nodes[n].b=b;w->nodes[n].axis=axis;w->nodes[n].ratio=ratio;}return n;
}
static void replace(Workspace *w,int old,int next) {
    if(w->root==old)w->root=next;
    for(int i=0;i<WS_FLOATS;++i)if(w->floats[i].root==old)w->floats[i].root=next;
    for(int i=0;i<WS_NODES;++i)if(w->nodes[i].kind==2) {
        if(w->nodes[i].a==old)w->nodes[i].a=next;
        if(w->nodes[i].b==old)w->nodes[i].b=next;
    }
}
int ws_group(const Workspace *w,int p) {
    for(int i=0;i<WS_NODES;++i)if(w->nodes[i].kind==1)
        for(int j=0;j<w->nodes[i].count;++j)if(w->nodes[i].panels[j]==p)return i;
    return -1;
}
static int remove_panel(Workspace *w,int p) {
    int g=ws_group(w,p);if(g<0)return 0;WsNode *n=&w->nodes[g];w->panels[p].home=g;
    for(int i=0;i<n->count;++i)if(n->panels[i]==p) {
        memmove(n->panels+i,n->panels+i+1,(n->count-i-1)*sizeof(int));--n->count;break;
    }
    if(n->count){if(n->active>=n->count)n->active=n->count-1;return 1;}
    int parent=-1,sibling=-1;
    for(int i=0;i<WS_NODES;++i)if(w->nodes[i].kind==2&&(w->nodes[i].a==g||w->nodes[i].b==g)) {
        parent=i;sibling=w->nodes[i].a==g?w->nodes[i].b:w->nodes[i].a;break;
    }
    if(parent>=0){memset(&w->nodes[parent],0,sizeof(WsNode));replace(w,parent,sibling);}
    else replace(w,g,-1);
    memset(n,0,sizeof(*n));return 1;
}
int ws_hide(Workspace *w,int p) {
    if(p<0||p>=WS_PANELS||p==22)return 0; /* active Prompt cannot be removed */
    if(remove_panel(w,p)){++w->revision;return 1;}return 0;
}
int ws_reveal(Workspace *w,int p) {
    if(p<0||p>=WS_PANELS)return 0;
    int g=ws_group(w,p);
    if(g<0){g=w->panels[p].home;if(g<0||g>=WS_NODES||w->nodes[g].kind!=1)g=ws_group(w,0);
        if(g<0){g=tabs(w,p);if(g<0)return 0;if(w->root<0)w->root=g;else {int s=split(w,w->root,g,0,700);if(s<0)return 0;w->root=s;}}
        else {WsNode *n=&w->nodes[g];n->panels[n->count++]=p;}
    }
    WsNode *n=&w->nodes[g];n->collapsed=0;for(int j=0;j<n->count;++j)if(n->panels[j]==p)n->active=j;
    for(int j=0;j<n->count;++j)if(n->panels[j]==22)n->active=j;
    ++w->revision;return 1;
}
int ws_move(Workspace *w,int p,int target,int edge,int outer) {
    if(p<0||p>=WS_PANELS||target<0||target>=WS_PANELS||edge<0||edge>WS_STACK)return 0;
    Workspace c=*w;int t=ws_group(&c,target),old=ws_group(&c,p);
    if(t<0||p==target||p==22)return 0;
    if(t==old&&c.nodes[t].count==1)return 0;
    remove_panel(&c,p);t=outer?c.root:ws_group(&c,target);if(t<0)return 0;
    if(edge==WS_STACK){WsNode *n=&c.nodes[t];if(n->kind!=1||n->count==WS_TABS)return 0;
        n->panels[n->count++]=p;n->active=n->count-1;n->collapsed=0;
        for(int j=0;j<n->count;++j)if(n->panels[j]==22)n->active=j;}
    else {int group=tabs(&c,p),s;if(group<0)return 0;
        int before=edge==WS_LEFT||edge==WS_TOP;
        /* Replace before allocating the parent, so it cannot replace itself. */
        s=alloc_node(&c,2);if(s<0)return 0;replace(&c,t,s);
        c.nodes[s].axis=edge>=WS_TOP;c.nodes[s].ratio=500;
        c.nodes[s].a=before?group:t;c.nodes[s].b=before?t:group;
    }
    ++c.revision;if(!ws_validate(&c))return 0;*w=c;return 1;
}
int ws_float(Workspace *w,int p,int x,int y,int width,int height) {
    if(p<0||p>=WS_PANELS||p==22)return 0;
    Workspace c=*w;remove_panel(&c,p);
    for(int i=0;i<WS_FLOATS;++i)if(c.floats[i].root<0){int n=tabs(&c,p);if(n<0)return 0;
        c.floats[i]=(WsFloat){.root=n,.x=x,.y=y,.w=width<320?320:width,.h=height<240?240:height};
        ++c.revision;if(!ws_validate(&c))return 0;*w=c;return 1;}
    return 0;
}
int ws_collapse(Workspace *w,int g) {
    if(g<0||g>=WS_NODES||w->nodes[g].kind!=1)return 0;
    for(int i=0;i<w->nodes[g].count;++i)if(w->nodes[g].panels[i]==22)return 0;
    w->nodes[g].collapsed=!w->nodes[g].collapsed;++w->revision;return 1;
}
void ws_prompt(Workspace *w,int active) {
    if(active){if(ws_group(w,22)<0)ws_reveal(w,22);
        int g=ws_group(w,22);WsNode *n=&w->nodes[g];n->collapsed=0;
        for(int j=0;j<n->count;++j)if(n->panels[j]==22)n->active=j;
    }else remove_panel(w,22);
}
void ws_preset(Workspace *w,int preset) {
    memset(w,0,sizeof(*w));w->root=-1;for(int i=0;i<WS_FLOATS;++i)w->floats[i].root=-1;
    for(int i=0;i<WS_PANELS;++i)w->panels[i]=(WsPanel){.plane=i==2?2:i==3?3:1,.x=-1,.y=-1,.zoom=100,.home=-1};
    int world=tabs(w,0);w->root=world;
    int left=tabs(w,4),right=tabs(w,6),bottom=tabs(w,5);
    w->nodes[right].panels[1]=7;w->nodes[right].panels[2]=11;w->nodes[right].count=3;
    if(preset==1){w->nodes[right].panels[0]=8;w->nodes[right].panels[1]=9;w->nodes[right].panels[2]=13;w->nodes[right].panels[3]=12;w->nodes[right].count=4;}
    if(preset==2){int inspector=tabs(w,1);world=split(w,world,inspector,0,500);w->nodes[right].panels[0]=11;w->nodes[right].panels[1]=10;w->nodes[right].count=2;}
    if(preset==3){w->nodes[left].collapsed=1;w->nodes[right].collapsed=1;}
    int middle=split(w,left,world,0,210);middle=split(w,middle,right,0,780);
    w->root=split(w,middle,bottom,1,840);++w->revision;
}
static int visit(const Workspace *w,int at,unsigned char *seen,unsigned char *panels,int depth) {
    if(at<0||at>=WS_NODES||seen[at]++||depth>WS_NODES)return 0;
    const WsNode *n=&w->nodes[at];
    if(n->kind==2)return (n->axis==0||n->axis==1)&&n->ratio>=50&&n->ratio<=950&&visit(w,n->a,seen,panels,depth+1)&&visit(w,n->b,seen,panels,depth+1);
    if(n->kind!=1||n->count<1||n->count>WS_TABS||n->active<0||n->active>=n->count||n->collapsed<0||n->collapsed>1)return 0;
    for(int i=0;i<n->count;++i){int p=n->panels[i];if(p<0||p>=WS_PANELS||panels[p]++)return 0;}
    return 1;
}
int ws_validate(const Workspace *w) {
    unsigned char seen[WS_NODES]={0},panels[WS_PANELS]={0};
    if(w->root>=0&&!visit(w,w->root,seen,panels,0))return 0;
    if(w->root < -1)return 0;
    for(int i=0;i<WS_FLOATS;++i){const WsFloat *f=&w->floats[i];if(f->root < -1)return 0;
        if(f->root>=0&&(f->w<160||f->h<100||f->w>10000||f->h>10000||f->x < -100000||f->x>100000||f->y < -100000||f->y>100000||!visit(w,f->root,seen,panels,0)))return 0;}
    for(int i=0;i<WS_NODES;++i)if(w->nodes[i].kind&&!seen[i])return 0;
    for(int i=0;i<WS_PANELS;++i){const WsPanel *p=&w->panels[i];if(p->plane<1||p->plane>3||p->zoom<25||p->zoom>800||p->x < -1||p->x>2047||p->y < -1||p->y>1023||p->home < -1||p->home>=WS_NODES)return 0;}
    return 1;
}
int ws_write(const Workspace *w,FILE *f) {
    if(!ws_validate(w))return 0;
    fprintf(f,"SIMANT-WORKSPACE 1\n%d\n",w->root);
    for(int i=0;i<WS_NODES;++i){const WsNode *n=&w->nodes[i];fprintf(f,"%d %d %d %d %d %d %d %d",n->kind,n->axis,n->ratio,n->a,n->b,n->count,n->active,n->collapsed);for(int j=0;j<WS_TABS;++j)fprintf(f," %d",n->panels[j]);fputc('\n',f);}
    for(int i=0;i<WS_PANELS;++i){const WsPanel *p=&w->panels[i];fprintf(f,"%d %d %d %d %d\n",p->plane,p->x,p->y,p->zoom,p->home);}
    for(int i=0;i<WS_FLOATS;++i){const WsFloat *p=&w->floats[i];fprintf(f,"%d %d %d %d %d %s\n",p->root,p->x,p->y,p->w,p->h,p->monitor[0]?p->monitor:"-");}
    return !ferror(f);
}
int ws_read(Workspace *w,FILE *f) {
    Workspace c={0};char magic[32];int version;
    if(fscanf(f,"%31s%d",magic,&version)!=2||strcmp(magic,"SIMANT-WORKSPACE")||version!=1||fscanf(f,"%d",&c.root)!=1)return 0;
    for(int i=0;i<WS_NODES;++i){WsNode *n=&c.nodes[i];if(fscanf(f,"%d%d%d%d%d%d%d%d",&n->kind,&n->axis,&n->ratio,&n->a,&n->b,&n->count,&n->active,&n->collapsed)!=8)return 0;for(int j=0;j<WS_TABS;++j)if(fscanf(f,"%d",&n->panels[j])!=1)return 0;}
    for(int i=0;i<WS_PANELS;++i){WsPanel *p=&c.panels[i];if(fscanf(f,"%d%d%d%d%d",&p->plane,&p->x,&p->y,&p->zoom,&p->home)!=5)return 0;}
    for(int i=0;i<WS_FLOATS;++i){WsFloat *p=&c.floats[i];if(fscanf(f,"%d%d%d%d%d%63s",&p->root,&p->x,&p->y,&p->w,&p->h,p->monitor)!=6)return 0;if(!strcmp(p->monitor,"-"))p->monitor[0]=0;}
    char tail;if(fscanf(f," %c",&tail)==1||!ws_validate(&c))return 0;*w=c;return 1;
}
void ws_exercise(Workspace *w,unsigned step) {
    switch(step%10){case 0:ws_preset(w,0);break;case 1:ws_reveal(w,1);ws_move(w,1,0,WS_RIGHT,0);break;
    case 2:ws_reveal(w,2);ws_move(w,2,1,WS_BOTTOM,0);break;case 3:ws_move(w,2,1,WS_STACK,0);break;
    case 4:ws_float(w,1,50,50,480,320);break;case 5:ws_collapse(w,ws_group(w,2));break;
    case 6:ws_reveal(w,2);ws_move(w,1,0,WS_LEFT,1);break;case 7:ws_hide(w,2);break;
    case 8:ws_preset(w,2);break;case 9:ws_preset(w,0);break;}
}
