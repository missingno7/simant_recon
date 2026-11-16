#include "assets.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t terrain[2][32768], life[2][24576];
static EnhancedArt art[256];
static unsigned art_count;
static struct { int id,kind; size_t size; uint8_t *data; } resources[2048];
static unsigned resource_count;
static uint8_t *font;
static size_t font_size;
static int ready;
static char error[240];
static unsigned le(const uint8_t *p) { return p[0]|(unsigned)p[1]<<8; }
static unsigned be(const uint8_t *p) { return p[1]|(unsigned)p[0]<<8; }
static uint32_t le32(const uint8_t *p) { return le(p)|(uint32_t)le(p+2)<<16; }
static uint8_t *read_file(const char *root,const char *name,size_t *size)
{
    char path[2048]; FILE *f; long length; uint8_t *p;
    if (snprintf(path,sizeof(path),"%s/%s",root,name)>=(int)sizeof(path)) return NULL;
    f=fopen(path,"rb"); if (!f) return NULL;
    if (fseek(f,0,SEEK_END) || (length=ftell(f))<0 || length>4000000 || fseek(f,0,SEEK_SET)) { fclose(f); return NULL; }
    p=malloc((size_t)length); *size=(size_t)length;
    if (!p || fread(p,1,*size,f)!=*size) { free(p); p=NULL; }
    fclose(f); return p;
}
/* Independent native Okumura LZSS decoder. No canonical Unpack state/routines. */
static int unpack(const uint8_t *in,size_t n,uint8_t *out,size_t wanted)
{
    uint8_t ring[4096]; unsigned write=4078,flags=0; size_t at=0,done=0;
    memset(ring,' ',sizeof(ring));
    while (done<wanted) {
        flags>>=1;
        if (!(flags&256)) { if (at>=n) return 0; flags=in[at++]|0xff00; }
        if (flags&1) {
            uint8_t c; if (at>=n) return 0; c=in[at++];
            out[done++]=c; ring[write]=c; write=(write+1)&4095;
        } else {
            unsigned from,count; if (at+2>n) return 0;
            from=in[at]|(in[at+1]&240)<<4; count=(in[at+1]&15)+3; at+=2;
            while (count-- && done<wanted) { uint8_t c=ring[from]; from=(from+1)&4095;
                out[done++]=c; ring[write]=c; write=(write+1)&4095; }
        }
    }
    return 1;
}
static int picture(int id,const uint8_t *p,size_t n)
{
    uint8_t *decoded=NULL,*pixels; unsigned type,w,h,bytes,depth; size_t extent;
    if (n<12) return 0;
    if (le(p)==65535) {
        unsigned wanted=le(p+2); decoded=malloc(wanted);
        if (!decoded || !unpack(p+4,n-4,decoded,wanted)) { free(decoded); return 0; }
        p=decoded; n=wanted;
    }
    if (n<12) { free(decoded); return 0; }
    type=le(p); w=le(p+8); h=le(p+10); depth=p[2]; bytes=(w+7)/8;
    extent=(size_t)bytes*h*(depth+(type==3));
    if ((type!=0 && type!=3) || (depth!=4 && depth!=1) || !w || !h || w>1024 || h>1024 || 12+extent>n || art_count==256) { free(decoded); return 0; }
    pixels=malloc((size_t)w*h); if (!pixels) { free(decoded); return 0; }
    for (unsigned y=0;y<h;++y) for (unsigned x=0;x<w;++x) {
        unsigned bit=7-(x&7),idx=0; const uint8_t *row=p+12+(size_t)y*bytes*(depth+(type==3));
        /* Planar mask precedes the four color planes; one means replace. */
        for (unsigned plane=0;plane<depth;++plane) idx|=((row[(plane+(type==3))*bytes+x/8]>>bit)&1)<<plane;
        if(depth==1)idx=idx?15:0;
        pixels[(size_t)y*w+x]=type==3 && !((row[x/8]>>bit)&1) ? 255:(uint8_t)idx;
    }
    art[art_count++]=(EnhancedArt){id,(int)w,(int)h,pixels}; free(decoded); return 1;
}
static int database(const char *root,const char *stem,unsigned *found)
{
    uint8_t *ndx=NULL,*dat=NULL; size_t ns=0,ds=0; char name[64]; int okay=0;
    snprintf(name,sizeof(name),"%s.NDX",stem);ndx=read_file(root,name,&ns);
    snprintf(name,sizeof(name),"%s.DAT",stem);dat=read_file(root,name,&ds);
    snprintf(error,sizeof(error),"Native asset catalog: invalid/missing %s record",stem);
    if (!ndx || !dat || ns<20 || ns<20+(size_t)le(ndx)*8) goto done;
    for (unsigned i=0;i<le(ndx);++i) {
        const uint8_t *r=ndx+20+i*8; unsigned id=le(r+4),kind=r[6],flags=r[7];
        size_t off=14+(size_t)le32(r),n; const uint8_t *p; uint8_t *decoded=NULL;
        if (kind!=2 && kind!=10 && kind!=17 && kind!=19 && kind!=21 && !(found && kind==9 && (id==9 || id==10 || id==13 || id==14))) continue;
        if (off+10>ds || (n=le(dat+off+6))>ds-off-10) goto done;
        p=dat+off+10;
        if ((flags&1) && !(flags&4) && n) {
            unsigned wanted; if (n<2) goto done; wanted=le(p); decoded=malloc(wanted);
            if (!decoded || !unpack(p+2,n-2,decoded,wanted)) { free(decoded); goto done; }
            p=decoded; n=wanted;
        } else if ((flags&5)==5 && n) {
            decoded=malloc(n+2); if (!decoded) goto done;
            decoded[0]=decoded[1]=255; memcpy(decoded+2,p,n); p=decoded; n+=2;
        }
        if(kind==10 || kind==17 || kind==19 || kind==21) {
            if(resource_count==2048){free(decoded);goto done;}
            uint8_t *copy=malloc(n+1);if(!copy){free(decoded);goto done;}
            memcpy(copy,p,n);copy[n]=0;
            resources[resource_count].id=id;resources[resource_count].kind=kind;
            resources[resource_count].size=n;resources[resource_count++].data=copy;
        } else if (kind==9) {
            size_t wanted=id<11?32768:24576;
            if (n!=wanted) { free(decoded); goto done; }
            if (id<11) { memcpy(terrain[10-id],p,n); *found|=1u<<(10-id); }
            else { memcpy(life[id-13],p,n); *found|=1u<<(id-11); }
        } else if (!picture(id,p,n)) {
            snprintf(error,sizeof(error),"Native asset catalog: unsupported/corrupt %s picture %u",stem,id);
            free(decoded); goto done;
        }
        free(decoded);
    }
    okay=1;
done:
    free(ndx);free(dat);return okay;
}
int enhanced_assets_load(const char *root)
{
    unsigned found=0;
    if (ready) return 1;
    if(!database(root,"HCEGANT",&found) || found!=15 || art_count!=212 ||
       !database(root,"SHARED",NULL) || art_count!=252)goto failed;
    font=read_file(root,"FONT2",&font_size);
    if (!font || font_size<26 || be(font+2)!=0 || be(font+4)!=255 ||
        26+(size_t)be(font+24)*2*be(font+14)+258*4>font_size) {
        snprintf(error,sizeof(error),"Native asset catalog: invalid/missing FONT2");goto failed;
    }
    ready=1;error[0]=0;atexit(enhanced_assets_free);
    fprintf(stderr,"Enhanced immutable catalog: 2 terrain sets, 2 life banks, %u pictures, FONT2; native ownership\n",art_count);
    return 1;
failed:
    enhanced_assets_free();return 0;
}
const char *enhanced_assets_error(void) { return error; }
void enhanced_assets_free(void)
{
    for (unsigned i=0;i<art_count;++i) free((void *)art[i].pixels);
    art_count=0;free(font);font=NULL;ready=0;
    for(unsigned i=0;i<resource_count;++i)free(resources[i].data);
    resource_count=0;
}
const uint8_t *enhanced_resource(int id,int kind,size_t *size) {
    for(unsigned i=0;i<resource_count;++i)if(resources[i].id==id&&resources[i].kind==kind){
        if(size)*size=resources[i].size;return resources[i].data;
    }
    if(size)*size=0;return NULL;
}
const EnhancedArt *enhanced_art(int id)
{
    for (unsigned i=0;i<art_count;++i) if (art[i].id==id) return &art[i];
    return NULL;
}
int enhanced_asset_cell(int set,unsigned ground,unsigned code,uint8_t pixels[256])
{
    uint8_t composed[128]; const uint8_t *bits; int bank,mode=0; static const int modes[]={0,3,1};
    if (!ready || set<0 || set>1 || ground>255) return 0;
    bits=terrain[set]+ground*128;
    if (code) {
        if (code>=0x380) {code-=0x280;bank=1;} else if (code>=0x200) {code-=0x200;bank=0;}
        else if (code>=0x100) {code-=0x100;bank=1;} else return 0;
        if (code>>7>2) return 0;
        mode=(code>=0xf0 && code<=0xff)?0:modes[code>>7];
        sim_graphics_tile_compose(bits,life[bank]+(code&127)*192,(int16_t)mode,SIM_GRAPHICS_TILE_COMPOSE_303F,composed);
        bits=composed;
    }
    for (unsigned y=0;y<16;++y) for (unsigned x=0;x<16;++x) {
        unsigned index=0;for (unsigned p=0;p<4;++p) index|=((bits[y*8+p*2+x/8]>>(7-(x&7)))&1)<<p;
        pixels[y*16+x]=(uint8_t)index;
    }
    return 1;
}
static unsigned glyph(unsigned c) {
    const uint8_t *ow=font+26+(size_t)be(font+24)*2*be(font+14)+258*2;
    return be(ow+c*2)==65535 ? 256:c;
}
static int advance(unsigned c) {
    const uint8_t *ow=font+26+(size_t)be(font+24)*2*be(font+14)+258*2;
    return (be(ow+c*2)&255)+((int16_t)be(font+8)<0);
}
int enhanced_font_height(void) { return ready?(int)be(font+14)-1:0; }
int enhanced_font_width(const char *text) {
    int n=0,max=0;if (!ready || !text) return 0;
    for (const unsigned char *p=(const unsigned char *)text;*p;++p) {
        if (*p=='\\' && p[1]=='n') { if(n>max)max=n;n=0;++p; } else n+=advance(glyph(*p));
    }
    return n>max?n:max;
}
void enhanced_font_draw(uint8_t *dst,int w,int h,int stride,int x,int y,const char *text,uint8_t color)
{
    if (!ready || !text) return;
    int pen=x,fh=enhanced_font_height(),rowbytes=be(font+24)*2,kern=(int16_t)be(font+8);
    const uint8_t *loc=font+26+(size_t)rowbytes*be(font+14),*ow=loc+258*2;
    for (const unsigned char *p=(const unsigned char *)text;*p;++p) {
        if (*p=='\\' && p[1]=='n') {pen=x;y+=fh;++p;continue;}
        unsigned c=glyph(*p),left=be(loc+c*2),right=be(loc+(c+1)*2);
        int offset=kern<0?0:kern+(int)(be(ow+c*2)>>8);
        for (int yy=0;yy<fh;++yy) for (unsigned xx=left;xx<right;++xx) {
            int dx=pen+offset+(int)(xx-left),dy=y+yy;
            if (dx>=0 && dx<w && dy>=0 && dy<h &&
                (font[26+(size_t)(yy+1)*rowbytes+xx/8]&(128>>(xx&7)))) dst[(size_t)dy*stride+dx]=color;
        }
        pen+=advance(c);
    }
}
