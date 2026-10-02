/* Native typed-leaf model for m295C's real backend dispatch wrappers. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct { uint8_t type,num,c2,c3,c4,c5; } Channel;
static void out(int port,int size,int value)
{ printf("out|port=%x|size=%d|value=%x\n",port,size,value); }
static void opl(int reg,int value)
{ out(0x388,1,reg); out(0x389,1,value); }
static void chip(int reg,int value)
{ out(0x220,1,reg); out(0x221,1,value); }

static void release(int kind,int dev,int note,int ch,int loaded,int owner,int info0,int info2)
{
    Channel c[5]={{(uint8_t)kind,(uint8_t)ch,9,(uint8_t)dev,(uint8_t)note,4},
                  {(uint8_t)kind,(uint8_t)(kind==7?10:ch+1),0,(uint8_t)dev,(uint8_t)note,5},
                  {(uint8_t)kind,(uint8_t)(ch+2),9,(uint8_t)(dev+1),(uint8_t)note,6},
                  {(uint8_t)kind,(uint8_t)(ch+3),9,(uint8_t)dev,(uint8_t)(note+1),7},
                  {0,0,0,0,0,0}};
    int i, voice_owner[2]={owner,owner};
    for(i=0;c[i].type;i++) if(c[i].c4==(uint8_t)note && c[i].c3==(uint8_t)dev) {
        int b=c[i].num;
        if(kind==1) {
            puts("pause"); if(voice_owner[b] && loaded==1) puts("queue_sample");
            voice_owner[b]=0; puts("resume");
        } else if(kind==2) {
            opl(b+0xa0,0); opl(b+0xb0,0);
        } else if(kind==3) {
            static const uint16_t f[12]={0x1ddd,0x1c31,0x1a9c,0x191b,0x17b4,0x165e,
              0x151f,0x13ee,0x12cf,0x11c1,0x10c1,0x0fd1};
            uint16_t v=(uint16_t)(f[note%12]>>(note/12));
            int chan=b*32;
            out(0x205,1,(v&15)+((uint8_t)chan+0x80));
            out(0x205,1,v>>4);
            out(0x205,1,(0x0f-(0>>3))+((uint8_t)chan+0x80)+0x10);
        } else if(kind==4) {
            chip(b+8,0); chip(b*2,0); chip(b*2+1,0);
        } else if(kind==5) {
            uint16_t f=0x3574>>1; uint16_t reg=(uint8_t)(b*32)+0x80; reg&=0xe0;
            uint16_t low=(f&15)+reg, hi=((f&0x3f0)>>4);
            out(0x220,2,(hi<<8)|(low&255)); out(0x220,1,reg+0x10+0x0f);
        } else if(kind==6) {
            out(0x331,1,0xd7); out(0x330,1,b+0x80); out(0x330,1,note+info2); out(0x330,1,0);
        } else if(kind==7) {
            out(0x331,1,0xd7); out(0x330,1,0x89); out(0x330,1,info0); out(0x330,1,0);
        }
        c[i].c4=0; c[i].c2=0; c[i].c5=15;
    }
    for(i=0;i<5;i++) printf("channel|index=%d|bytes=%u,%u,%u,%u,%u,%u\n",i,
      c[i].type,c[i].num,c[i].c2,c[i].c3,c[i].c4,c[i].c5);
    printf("voice_owner|0=%d|1=%d\n",voice_owner[0],voice_owner[1]);
    printf("queue_count=%d\n",owner && loaded==1 && kind==1 ? 2 : 0);
}
int main(int argc,char **argv) {
    if(argc!=9)return 2;
    release(atoi(argv[1]),atoi(argv[2]),atoi(argv[3]),atoi(argv[4]),atoi(argv[5]),
            atoi(argv[6]),atoi(argv[7]),atoi(argv[8]));
    return 0;
}
