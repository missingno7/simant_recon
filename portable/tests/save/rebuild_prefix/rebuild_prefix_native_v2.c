#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#define far
#define fd_50F6_0480 Barrier
int TERRAINset, CurGndTileID, Barrier;
int ListIndexA, ListIndexB, ListIndexR;
unsigned char LifeA[128][64], LifeB[64][64], LifeR[64][64];
unsigned char AlistX[1000], AlistY[1000], AlistT[1000];
unsigned char BlistX[500], BlistY[500], BlistT[500];
unsigned char RlistX[500], RlistY[500], RlistT[500];
struct ProviderEvent { int16_t set, barrier_at_entry, tile_at_entry; };
static struct ProviderEvent events[2]; static int event_count;
void f_0250_0256(int set) {
    if (event_count >= 2) abort();
    events[event_count].set = (int16_t)set;
    events[event_count].barrier_at_entry = (int16_t)Barrier;
    events[event_count].tile_at_entry = (int16_t)CurGndTileID; ++event_count;
}
void OverlayTileSet(int type, int id) {
    if (type == 0) {
        if (id == 0x3e9) {
            f_0250_0256(1);
            fd_50F6_0480 = 0x90;
        } else if (id == 0x3e8) {
            f_0250_0256(0);
            fd_50F6_0480 = 0x50;
        }
    }
}
void native_rebuild_prefix(void) {
    int x;
    int y;
    int i;

    if (TERRAINset != 1)
        CurGndTileID = 1000;
    else
        CurGndTileID = 1001;
    OverlayTileSet(0, CurGndTileID);
    for (x = 0; x < 128; x++)
        for (y = 0; y < 64; y++)
            LifeA[x][y] = 0;
    for (x = 0; x < 64; x++)
        for (y = 0; y < 64; y++)
            LifeB[x][y] = 0;
    for (x = 0; x < 64; x++)
        for (y = 0; y < 64; y++)
            LifeR[x][y] = 0;
    for (i = ListIndexA; i >= 0; i--)
        LifeA[AlistX[i]][AlistY[i]] = AlistT[i];
    for (i = ListIndexB; i >= 0; i--)
        LifeB[BlistX[i]][BlistY[i]] = BlistT[i];
    for (i = ListIndexR; i >= 0; i--)
        LifeR[RlistX[i]][RlistY[i]] = RlistT[i];
}
int main(void) {
    int16_t v;
    if (fread(&v,2,1,stdin)!=1) return 2;
    TERRAINset=v;
    if (fread(&v,2,1,stdin)!=1) return 2;
    Barrier=v;
    if (fread(&v,2,1,stdin)!=1) return 2;
    ListIndexA=v;
    if (fread(&v,2,1,stdin)!=1) return 2;
    ListIndexB=v;
    if (fread(&v,2,1,stdin)!=1) return 2;
    ListIndexR=v;
    if (fread(LifeA,1,sizeof(LifeA),stdin)!=sizeof(LifeA)) return 2;
    if (fread(LifeB,1,sizeof(LifeB),stdin)!=sizeof(LifeB)) return 2;
    if (fread(LifeR,1,sizeof(LifeR),stdin)!=sizeof(LifeR)) return 2;
    if (fread(AlistX,1,sizeof(AlistX),stdin)!=sizeof(AlistX)) return 2;
    if (fread(AlistY,1,sizeof(AlistY),stdin)!=sizeof(AlistY)) return 2;
    if (fread(AlistT,1,sizeof(AlistT),stdin)!=sizeof(AlistT)) return 2;
    if (fread(BlistX,1,sizeof(BlistX),stdin)!=sizeof(BlistX)) return 2;
    if (fread(BlistY,1,sizeof(BlistY),stdin)!=sizeof(BlistY)) return 2;
    if (fread(BlistT,1,sizeof(BlistT),stdin)!=sizeof(BlistT)) return 2;
    if (fread(RlistX,1,sizeof(RlistX),stdin)!=sizeof(RlistX)) return 2;
    if (fread(RlistY,1,sizeof(RlistY),stdin)!=sizeof(RlistY)) return 2;
    if (fread(RlistT,1,sizeof(RlistT),stdin)!=sizeof(RlistT)) return 2;
    native_rebuild_prefix();
    if (fwrite(&CurGndTileID,2,1,stdout)!=1 || fwrite(&Barrier,2,1,stdout)!=1) return 3;
    { int16_t n=(int16_t)event_count; if (fwrite(&n,2,1,stdout)!=1) return 3; }
    if (fwrite(events,sizeof(events[0]),(size_t)event_count,stdout)!=(size_t)event_count) return 3;
    if (fwrite(LifeA,1,sizeof(LifeA),stdout)!=sizeof(LifeA)) return 3;
    if (fwrite(LifeB,1,sizeof(LifeB),stdout)!=sizeof(LifeB)) return 3;
    if (fwrite(LifeR,1,sizeof(LifeR),stdout)!=sizeof(LifeR)) return 3;
    return 0;
}
