#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "native_owners.h"
#include "source_bounded_additive.h"
#include "portable/whole_program/platform/graphics.h"
int16_t LoadGame(void);
int16_t o09_35F5_0188(int16_t useLast);
void f_004A_02AD(void);
int16_t fd_3D57_02C2=0, fd_50F6_0EAC=0, fd_3D57_07AA=1;
char fd_50F6_3862[100]="bounded.v3";
int16_t fd_50F6_0354=0, TERRAINset=1, CurGndTileID=0;
int32_t fd_50F6_0214=0,fd_50F6_0204=0,fd_50F6_0472=0;
uint8_t LifeA[128][64],LifeB[64][64],LifeR[64][64];
int16_t ListIndexA=-1,ListIndexB=-1,ListIndexR=-1;
uint8_t AlistX[500],AlistY[500],AlistT[500],BlistX[500],BlistY[500],BlistT[500],RlistX[500],RlistY[500],RlistT[500];
int16_t fd_50F6_0A06=1,fd_50F6_0496=0,fd_50F6_04C2=0,MeLocY=0,MeLocX=0,MePlane=0;
struct TestPoint { int16_t x,y; };
struct TestPoint fd_50F6_0508={6,8},fd_50F6_0596={0,0},fd_50F6_06A6={0,0},fd_50F6_072E={0,0};
int16_t fd_50F6_0FB6=20,fd_50F6_0FFA=14;
static uint8_t wire[256]; static size_t wire_len=0,wire_pos=0; static int open_count=0;
int16_t dos_open(char *path,int16_t flags,...){(void)path;if(flags&0x0100){open_count++;wire_len=wire_pos=0;return 3;}if((flags&0x0002)!=0){open_count++;return -1;}wire_pos=0;return 3;}
int16_t dos_write(int16_t fd,void *p,uint16_t n){(void)fd;if(wire_len+n>sizeof wire)return -1;memcpy(wire+wire_len,p,n);wire_len+=n;return n;}
int16_t dos_read(int16_t fd,void *p,uint16_t n){(void)fd;size_t avail=wire_len-wire_pos;if(n>avail)n=(uint16_t)avail;memcpy(p,wire+wire_pos,n);wire_pos+=n;return n;}
int16_t dos_close(int16_t fd){(void)fd;return 0;}
int16_t dos_remove(char *p){(void)p;return 0;}
int16_t dos_sprintf(char *p,const char *fmt,...){va_list a;va_start(a,fmt);int n=vsprintf(p,fmt,a);va_end(a);return (int16_t)n;}
char *_fstrcpy(char *d,const char *s){return strcpy(d,s);}
void WinPrintf(char *fmt,...){(void)fmt;}
void f_1C62_00AC(char *s){(void)s;}
void f_1C62_00C0(char *s){(void)s;}
int16_t f_1C62_0415(char *s,int16_t x){(void)s;(void)x;return 1;}
void f_15D9_009C(void *p,int32_t a,int16_t b){(void)p;(void)a;(void)b;}
int16_t o15_384C_0239(int16_t a){(void)a;return 2;}
void EditMessage(void *p,int32_t a,int16_t b){(void)p;(void)a;(void)b;}
void SetMenuEntries(void){}
void PauseGame(int16_t a){(void)a;}
int16_t dos_errno=0;
void o11_35F5_0000(void){}
void o11_35F5_0088(int16_t x){(void)x;}
void RandYard(void){}
void StopSong(void){}
void OverlayTileSet(int16_t t,int16_t id){(void)t;(void)id;}
void SetMyLife(int16_t p,int16_t x,int16_t y,int16_t t,int16_t d,int16_t l){(void)p;(void)x;(void)y;(void)t;(void)d;(void)l;}
void FullCount(void){}
void SetDefaultWindows(void){}
void CenterEdit(int16_t x,int16_t y){(void)x;(void)y;}
void SetDefaultWindPrompt(int16_t m){(void)m;}
void UpdateEdit(void){}
void f_0250_0ED2(void){}
int main(void){
    native_state_Cycle.signed_value=(int16_t)0x1234;
    native_state_ListIndexB.signed_value=(int16_t)0x2233;
    native_state_ListIndexR.signed_value=(int16_t)0x4455;
    native_state_LionListM.values[0]=(uint8_t)0x0010;
    native_state_LionListM.values[1]=(uint8_t)0x0011;
    native_state_LionListM.values[2]=(uint8_t)0x0012;
    native_state_LionListM.values[3]=(uint8_t)0x0013;
    native_state_LionListM.values[4]=(uint8_t)0x0014;
    native_state_LionListM.values[5]=(uint8_t)0x0015;
    native_state_LionListM.values[6]=(uint8_t)0x0016;
    native_state_LionListM.values[7]=(uint8_t)0x0017;
    native_state_LionListM.values[8]=(uint8_t)0x0018;
    native_state_LionListM.values[9]=(uint8_t)0x0019;
    native_state_LionListS.values[0]=(uint8_t)0x0020;
    native_state_LionListS.values[1]=(uint8_t)0x0021;
    native_state_LionListS.values[2]=(uint8_t)0x0022;
    native_state_LionListS.values[3]=(uint8_t)0x0023;
    native_state_LionListS.values[4]=(uint8_t)0x0024;
    native_state_LionListS.values[5]=(uint8_t)0x0025;
    native_state_LionListS.values[6]=(uint8_t)0x0026;
    native_state_LionListS.values[7]=(uint8_t)0x0027;
    native_state_LionListS.values[8]=(uint8_t)0x0028;
    native_state_LionListS.values[9]=(uint8_t)0x0029;
    native_state_LionListT.values[0]=(uint8_t)0x0030;
    native_state_LionListT.values[1]=(uint8_t)0x0031;
    native_state_LionListT.values[2]=(uint8_t)0x0032;
    native_state_LionListT.values[3]=(uint8_t)0x0033;
    native_state_LionListT.values[4]=(uint8_t)0x0034;
    native_state_LionListT.values[5]=(uint8_t)0x0035;
    native_state_LionListT.values[6]=(uint8_t)0x0036;
    native_state_LionListT.values[7]=(uint8_t)0x0037;
    native_state_LionListT.values[8]=(uint8_t)0x0038;
    native_state_LionListT.values[9]=(uint8_t)0x0039;
    native_state_LionListX.values[0]=(uint8_t)0x0040;
    native_state_LionListX.values[1]=(uint8_t)0x0041;
    native_state_LionListX.values[2]=(uint8_t)0x0042;
    native_state_LionListX.values[3]=(uint8_t)0x0043;
    native_state_LionListX.values[4]=(uint8_t)0x0044;
    native_state_LionListX.values[5]=(uint8_t)0x0045;
    native_state_LionListX.values[6]=(uint8_t)0x0046;
    native_state_LionListX.values[7]=(uint8_t)0x0047;
    native_state_LionListX.values[8]=(uint8_t)0x0048;
    native_state_LionListX.values[9]=(uint8_t)0x0049;
    native_state_LionListY.values[0]=(uint8_t)0x0050;
    native_state_LionListY.values[1]=(uint8_t)0x0051;
    native_state_LionListY.values[2]=(uint8_t)0x0052;
    native_state_LionListY.values[3]=(uint8_t)0x0053;
    native_state_LionListY.values[4]=(uint8_t)0x0054;
    native_state_LionListY.values[5]=(uint8_t)0x0055;
    native_state_LionListY.values[6]=(uint8_t)0x0056;
    native_state_LionListY.values[7]=(uint8_t)0x0057;
    native_state_LionListY.values[8]=(uint8_t)0x0058;
    native_state_LionListY.values[9]=(uint8_t)0x0059;
    native_state_SowX.signed_values[0]=(int16_t)0x1001;
    native_state_SowX.signed_values[1]=(int16_t)0x1002;
    native_state_SowX.signed_values[2]=(int16_t)0x1003;
    native_state_SowY.signed_values[0]=(int16_t)0x2001;
    native_state_SowY.signed_values[1]=(int16_t)0x2002;
    native_state_SowY.signed_values[2]=(int16_t)0x2003;
    native_state_SowDir.signed_values[0]=(int16_t)0x3001;
    native_state_SowDir.signed_values[1]=(int16_t)0x3002;
    native_state_SowDir.signed_values[2]=(int16_t)0x3003;
    native_state_SowSave.signed_values[0]=(int16_t)0x4001;
    native_state_SowSave.signed_values[1]=(int16_t)0x4002;
    native_state_SowSave.signed_values[2]=(int16_t)0x4003;
    native_state_PillarMap.signed_values[0]=(int16_t)0x5001;
    native_state_PillarMap.signed_values[1]=(int16_t)0x5002;
    native_state_PillarMap.signed_values[2]=(int16_t)0x5003;
    native_state_PillarMap.signed_values[3]=(int16_t)0x5004;
    native_state_PillarMap.signed_values[4]=(int16_t)0x5005;
    native_state_PillarMap.signed_values[5]=(int16_t)0x5006;
    if(native_state_Cycle.raw_bytes[0]!=0x34||native_state_Cycle.raw_bytes[1]!=0x12)return 20;
    if(o09_35F5_0188(1)!=1)return 21;
    {const uint8_t expected[]={0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x40,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x01,0x50,0x02,0x50,0x03,0x50,0x04,0x50,0x05,0x50,0x06,0x50,0x01,0x30,0x02,0x30,0x03,0x30,0x01,0x40,0x02,0x40,0x03,0x40,0x01,0x10,0x02,0x10,0x03,0x10,0x01,0x20,0x02,0x20,0x03,0x20,0x34,0x12,0x33,0x22,0x55,0x44};
     if(wire_len!=sizeof expected||memcmp(wire,expected,sizeof expected)!=0)return 22;}
    puts("PASS: actual generated S09 SaveGame writes all 13 V5 SaveRec rows in DOS little-endian order; Cycle raw byte alias agrees");
    return 0;
}

