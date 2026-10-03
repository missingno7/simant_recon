#include <stdint.h>
#include <stdio.h>
#include "source_bounded_additive.h"
void AddAntLion(int16_t,int16_t);
int16_t LionIndex=0; int8_t Dx8[8]={0,1,1,1,0,-1,-1,-1}; int8_t Dy8[8]={-1,-1,0,1,1,1,0,-1};
int16_t IsClearTile(int16_t p,int16_t x,int16_t y){(void)p;(void)x;(void)y;return 0;}
void SetMap(int16_t p,int16_t x,int16_t y,int16_t v){(void)p;(void)x;(void)y;(void)v;}
int main(void){
 AddAntLion(23,41);
 if(LionIndex!=1)return 1;
 if(native_state_LionListX.values[0]!=23||native_state_LionListY.values[0]!=41)return 2;
 if(native_state_LionListM.values[0]!=0||native_state_LionListS.values[0]!=0||native_state_LionListT.values[0]!=0)return 3;
 if(native_state_LionListX.values[9]!=0)return 4;
 puts("PASS: actual generated AddAntLion writes its six source-owned list fields through V5 native owner views");
 return 0;
}
