#include "world.h"
#include "assets.h"
#include <stdlib.h>
#include <string.h>

/* DoCalcTile's presentation projection, applied to immutable snapshot values.
 * No source scratch/global-plane swaps, clock, producers or game routines. */
void enhanced_world_cell(const EnhancedWorldSnapshot *w,int plane,int x,int y,ModernCell *cell)
{
    unsigned v;cell->ground=0;cell->life=0;
    if(!w || y<0 || y>=64)return;
    if(plane<2) {
        x&=127;
        if(w->world_layer>=0 && w->world_layer<=4) {
            static const unsigned channel[]={0,2,3,4,5};
            v=w->scent[channel[w->world_layer]][x>>1][y>>1];
            if(v>16)cell->ground=(uint8_t)(((v>>4)&31)-16);
        }
        if(!cell->ground)cell->ground=w->surface[x][y];
        v=w->life_surface[x][y];
    } else {x&=63;cell->ground=(uint8_t)((plane==2?w->black[x][y]:w->red[x][y])-0x70);
        v=plane==2?w->life_black[x][y]:w->life_red[x][y];}
    if(v==255) {cell->life=(uint16_t)(w->player_base+w->player_type+(plane<2?0x380:0x300));
        cell->life+=(uint16_t)(w->player_type<8?w->player_egg:w->player_dir);}
    else if(v==254)cell->life=(uint16_t)(w->player_base+w->player_type+w->player_dir+(plane<2?0x388:0x308));
    else if(v)cell->life=(uint16_t)(v+(plane<2?0x100:0x200));
}
typedef struct Canvas {uint8_t *p;int w,h,stride;EnhancedRect bounds;} Canvas;
static void pixel(Canvas *c,int x,int y,int color) {
    if(x<0||y<0||x>=c->w||y>=c->h)return;
    c->p[(size_t)y*c->stride+x]=(uint8_t)(color&15);
    if(x<c->bounds.left)c->bounds.left=x;if(y<c->bounds.top)c->bounds.top=y;
    if(x+1>c->bounds.right)c->bounds.right=x+1;if(y+1>c->bounds.bottom)c->bounds.bottom=y+1;
}
static void rect(Canvas *c,int x,int y,int w,int h,int color) {
    for(int yy=y;yy<y+h;++yy)for(int xx=x;xx<x+w;++xx)pixel(c,xx,yy,color);
}
static void line(Canvas *c,int x0,int y0,int x1,int y1,int color) {
    int dx=abs(x1-x0),dy=-abs(y1-y0),sx=x0<x1?1:-1,sy=y0<y1?1:-1,err=dx+dy;
    for(;;){pixel(c,x0,y0,color);if(x0==x1&&y0==y1)break;int twice=err*2;
        if(twice>=dy){err+=dy;x0+=sx;}if(twice<=dx){err+=dx;y0+=sy;}}
}
static void image(Canvas *c,int id,int x,int y) {
    const EnhancedArt *a=enhanced_art(id);if(!a)return;
    for(int yy=0;yy<a->height;++yy)for(int xx=0;xx<a->width;++xx) {
        unsigned index=a->pixels[(size_t)yy*a->width+xx];if(index!=255)pixel(c,x+xx,y+yy,index);
    }
}
static void balloon(Canvas *c,int x,int y,const char *text) {
    int lines=1;for(const char *p=text;*p;++p)if(*p=='\\'&&p[1]=='n'){++lines;++p;}
    int w=enhanced_font_width(text)+16,h=enhanced_font_height()*lines+14;
    int l=x+4,t=y-h-4;
    rect(c,l+2,t,w-4,h,15);rect(c,l,t+2,w,h-4,15);
    line(c,l+2,t,l+w-3,t,0);line(c,l+2,t+h-1,l+w-3,t+h-1,0);
    line(c,l,t+2,l,t+h-3,0);line(c,l+w-1,t+2,l+w-1,t+h-3,0);
    for(int yy=0;yy<7;++yy)line(c,l+8,t+h+yy,l+14-yy,t+h+yy,15);
    line(c,l+8,t+h-1,l+8,t+h+6,0);line(c,l+8,t+h+6,l+14,t+h-1,0);
    enhanced_font_draw(c->p,c->w,c->h,c->stride,l+8,t+6,text,0);
}
EnhancedRect enhanced_world_draw(const EnhancedWorldSnapshot *w,uint8_t *p,int width,int height,int stride)
{
    Canvas c={p,width,height,stride,{width,height,0,0}};
    const EnhancedWorldOverlays *o=&w->overlays;
    if(!o->available||o->plane!=w->plane)return c.bounds;
    for(unsigned i=0;i<o->art_count;++i)image(&c,o->art[i].id,o->art[i].x,o->art[i].y);
    for(unsigned i=0;i<o->line_count;++i) {const EnhancedLine *l=&o->lines[i];line(&c,l->x0,l->y0,l->x1,l->y1,l->color);}
    for(unsigned i=0;i<o->rect_count;++i) {const EnhancedRect *r=&o->rects[i].rect;
        /* g9134 uses the low color nibble, including compound source tokens. */
        for(int y=r->top;y<r->bottom;++y)for(int x=r->left;x<r->right;++x) {
            if(x<0||y<0||x>=width||y>=height)continue;
            int old=p[(size_t)y*stride+x],color=o->rects[i].color&15,op=o->rects[i].operation;
            pixel(&c,x,y,op==8?(old&color):op==16?(old|color):op==24?(old^color):color);
        }
    }
    for(unsigned i=0;i<o->balloon_count;++i)if(o->balloons[i].plane==w->plane)
        balloon(&c,o->balloons[i].anchor.x,o->balloons[i].anchor.y,o->balloons[i].text);
    return c.bounds;
}
static void diamond(Canvas *c,int x,int y,int color,int fill) {
    /* DOS yard projection g_2A42 and DrawSimColonies, in native picture units. */
    for(int row=0;row<=7;++row) {
        int l=x-row,r=l+24;if(fill)line(c,l,y+row,r,y+row,color);
        else {pixel(c,l,y+row,color);pixel(c,r,y+row,color);}
    }
    line(c,x,y,x+24,y,color);line(c,x-7,y+7,x+17,y+7,color);
}
void enhanced_yard_draw(const EnhancedOverviewSnapshot *y,uint8_t *p,int width,int height,int stride)
{
    Canvas c={p,width,height,stride,{width,height,0,0}};
    memset(p,0,(size_t)height*stride);
    if(y->yard_mode<2) {
        image(&c,7000+y->yard_mode,-1,0);
        image(&c,7003,280,0);
        unsigned order[96];for(unsigned i=0;i<y->actors.count;++i)order[i]=i;
        for(unsigned i=1;i<y->actors.count;++i) {unsigned a=order[i],j=i;
            while(j && y->actors.poses[order[j-1]].priority>y->actors.poses[a].priority){order[j]=order[j-1];--j;}order[j]=a;}
        for(unsigned i=0;i<y->actors.count;++i) {
            const EnhancedArtPose *a=&y->actors.poses[order[i]];
            if(a->id==30000)balloon(&c,a->x-4,a->y+24,y->human_balloon);
            else if(a->id!=30001)image(&c,a->id,a->x,a->y);
        }
    } else {
        image(&c,7020,0,65);const EnhancedArt *a=enhanced_art(7020);
        image(&c,7021,0,65+(a?a->height:0));const EnhancedArt *b=enhanced_art(7021);
        image(&c,7022,0,65+(a?a->height:0)+(b?b->height:0));
        for(int x=0;x<12;++x)for(int row=0;row<16;++row) {
            int px=169+x*28-row*10,py=67+row*10;
            if(y->yard_mode==2) {
                int black=y->population_black[x][row]!=0,red=y->population_red[x][row]!=0;
                int color=black?(red?6:15):(red?4:8);diamond(&c,px,py,color,1);
            } else {
                int hb=(y->population_black[x][row]+3)>>2,hr=(y->population_red[x][row]+3)>>2;
                rect(&c,168+x*28-row*10,py+4-hb,9,hb,15);
                rect(&c,180+x*28-row*10,py+4-hr,9,hr,4);
            }
        }
    }
    diamond(&c,169+y->current_patch.x*28-y->current_patch.y*10,67+y->current_patch.y*10,14,0);
    if(y->message[0]) {
        int w=enhanced_font_width(y->message);rect(&c,(width-w)/2-4,4,w+8,enhanced_font_height()+4,15);
        enhanced_font_draw(p,width,height,stride,(width-w)/2,6,y->message,0);
    }
}
