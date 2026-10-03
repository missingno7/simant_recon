#include "../../../whole_program/platform/handles.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t rng=0x171C5916u;
static uint32_t next_rand(void){rng=rng*1664525u+1013904223u;return rng;}
static void directed(void)
{
    SimHandleManager *m=sim_handles_create(96,32);SimHandle a=NULL,b=NULL,c=NULL,t=NULL,real=NULL;
    SimHandleInfo info;char *p;size_t i;
    assert(m);
    assert(sim_handles_allocate(m,25,SIM_HANDLE_SOFT|0x10,"soft-a",&a)==SIM_HANDLE_OK);
    assert(sim_handles_allocate(m,32,SIM_HANDLE_HARD,"hard-b",&b)==SIM_HANDLE_OK);
    assert(sim_handles_lock(m,a,&p)==SIM_HANDLE_OK);memset(p,0x5a,25);
    assert(sim_handles_free(m,a)==SIM_HANDLE_LOCKED);
    assert(sim_handles_resize(m,a,60,SIM_HANDLE_SOFT)==SIM_HANDLE_LOCKED);
    assert(sim_handles_discard(m,a)==SIM_HANDLE_LOCKED);
    assert(sim_handles_unlock(m,a,&t)==SIM_HANDLE_OK && t);
    assert(sim_handles_resolve(m,t,&real)==SIM_HANDLE_OK && real==a);
    assert(sim_handles_info(m,a,&info)==SIM_HANDLE_OK&&info.size==25&&info.type==SIM_HANDLE_SOFT&&info.attributes==0x10&&info.lock_count==0);
    assert(sim_handles_resize(m,t,41,SIM_HANDLE_SOFT)==SIM_HANDLE_OK);
    assert(sim_handles_lock(m,a,&p)==SIM_HANDLE_OK);
    for(i=0;i<25;i++)assert((unsigned char)p[i]==0x5a);
    assert(sim_handles_unlock(m,a,NULL)==SIM_HANDLE_OK);
    assert(sim_handles_discard(m,a)==SIM_HANDLE_OK);
    assert(sim_handles_info(m,a,&info)==SIM_HANDLE_OK&&info.is_discarded&&info.size==41);
    assert(sim_handles_lock(m,a,&p)==SIM_HANDLE_DISCARDED_DATA);
    /* A fresh resident soft block is reclaimed when a valid heap budget is exhausted. */
    assert(sim_handles_allocate(m,20,SIM_HANDLE_SOFT,"soft-c",&c)==SIM_HANDLE_OK);
    assert(sim_handles_allocate(m,64,SIM_HANDLE_HARD,"pressure",&real)==SIM_HANDLE_OK);
    assert(sim_handles_info(m,c,&info)==SIM_HANDLE_OK&&info.is_discarded);
    assert(sim_handles_allocate(m,1,SIM_HANDLE_HARD,"full",&t)==SIM_HANDLE_NO_MEMORY);
    assert(sim_handles_free(m,b)==SIM_HANDLE_OK);
    assert(sim_handles_free(m,a)==SIM_HANDLE_OK);
    assert(sim_handles_free(m,c)==SIM_HANDLE_OK);
    assert(sim_handles_free(m,a)==SIM_HANDLE_INVALID_HANDLE);
    assert(sim_handles_info(m,real,&info)==SIM_HANDLE_OK&&info.size==64);
    assert(sim_handles_free(m,real)==SIM_HANDLE_OK);
    sim_handles_destroy(m);
}

static void randomized(void)
{
    SimHandleManager*m=sim_handles_create(8192,128);SimHandle h[128]={0};unsigned step;
    assert(m);
    for(step=0;step<2000;step++){
        unsigned k=next_rand()%128u, op=next_rand()%7u;SimHandleInfo info;SimHandleStatus st;char*p=NULL;
        if(op==0||!h[k]){
            int32_t n=(int32_t)(1+next_rand()%300u);int16_t type=(int16_t)(next_rand()%4u);
            st=sim_handles_allocate(m,n,type,"rnd",&h[k]);
            assert(st==SIM_HANDLE_OK||st==SIM_HANDLE_NO_MEMORY||st==SIM_HANDLE_HANDLE_LIMIT);
        }else if(op==1){
            st=sim_handles_lock(m,h[k],&p);
            if(st==SIM_HANDLE_OK){assert(p);assert(sim_handles_unlock(m,h[k],NULL)==SIM_HANDLE_OK);}
            else assert(st==SIM_HANDLE_DISCARDED_DATA||st==SIM_HANDLE_LOCK_LIMIT);
        }else if(op==2){
            if(sim_handles_info(m,h[k],&info)==SIM_HANDLE_OK){
                st=sim_handles_unlock(m,h[k],NULL);
                if(info.lock_count)assert(st==SIM_HANDLE_OK);else assert(st==SIM_HANDLE_UNLOCKED);
            }
        }else if(op==3){
            if(sim_handles_info(m,h[k],&info)==SIM_HANDLE_OK){
                if(info.lock_count){st=sim_handles_resize(m,h[k],(int32_t)(1+next_rand()%300u),info.type);assert(st==SIM_HANDLE_LOCKED);}
                else if(info.is_discarded){st=sim_handles_resize(m,h[k],32,SIM_HANDLE_HARD);assert(st==SIM_HANDLE_DISCARDED_DATA);}
                else {st=sim_handles_resize(m,h[k],(int32_t)(1+next_rand()%300u),info.type);assert(st==SIM_HANDLE_OK||st==SIM_HANDLE_NO_MEMORY);}
            }
        }else if(op==4){
            if(sim_handles_info(m,h[k],&info)==SIM_HANDLE_OK){st=sim_handles_discard(m,h[k]);assert(st==(info.lock_count?SIM_HANDLE_LOCKED:SIM_HANDLE_OK));}
        }else if(op==5){
            if(sim_handles_info(m,h[k],&info)==SIM_HANDLE_OK){st=sim_handles_free(m,h[k]);if(info.lock_count)assert(st==SIM_HANDLE_LOCKED);else{assert(st==SIM_HANDLE_OK);h[k]=NULL;}}
        }else{
            if(sim_handles_info(m,h[k],&info)==SIM_HANDLE_OK&&!info.is_discarded){
                assert(sim_handles_lock(m,h[k],&p)==SIM_HANDLE_OK&&p);
                ((unsigned char*)p)[0]=(unsigned char)(k^step);
                assert(sim_handles_unlock(m,h[k],NULL)==SIM_HANDLE_OK);
            }
        }
        if(h[k]&&sim_handles_info(m,h[k],&info)==SIM_HANDLE_OK){
            assert(info.is_discarded || info.size>0);
            if(!info.is_discarded){assert(sim_handles_lock(m,h[k],&p)==SIM_HANDLE_OK&&p);assert(sim_handles_unlock(m,h[k],NULL)==SIM_HANDLE_OK);}
        }
    }
    for(step=0;step<128;step++)if(h[step]){SimHandleInfo info;if(sim_handles_info(m,h[step],&info)==SIM_HANDLE_OK){while(info.lock_count){assert(sim_handles_unlock(m,h[step],NULL)==SIM_HANDLE_OK);--info.lock_count;}assert(sim_handles_free(m,h[step])==SIM_HANDLE_OK);}}
    sim_handles_destroy(m);
}

static void public_symbols(void)
{
    char **h,*p,**t;
    assert(sim_handles_global_configure(1024,32)==SIM_HANDLE_OK);
    h=f_2CFB_0002(48,SIM_HANDLE_FIRM,"alias");assert(h);
    t=f_171C_1A9E(16,SIM_HANDLE_HARD,"indexed");assert(t);
    assert((((uintptr_t)t)&(uintptr_t)0xFFFF0000u)==(uintptr_t)0x0F0F0000u);
    p=f_171C_1B84(t);assert(p);memset(p,0x41,16);
    assert(f_171C_1AD4(t)==1);assert(f_171C_1C1C(t)==16);
    assert(f_171C_1BBA(t)!=NULL);assert(f_171C_1AD4(h)==0);
    { char **resized=f_171C_1B2C(t,20,SIM_HANDLE_HARD);assert(resized&&(((uintptr_t)resized&0xFFFF0000u)!=0x0F0F0000u));assert(f_171C_1C1C(t)==20); }
    f_2CFB_002F(h,SIM_HANDLE_SOFT);assert(f_171C_1686(h)==SIM_HANDLE_SOFT);
    assert(f_171C_1750()==(int32_t)(1024-80));
    assert(f_171C_1772()==48);
    f_2CFB_0007(h);f_171C_13E4(t);
}

static void pointer_relation(void)
{
    void*p=dos_malloc(37);assert(p);memset(p,0x33,37);
    p=f_171C_2302(p,80);assert(p);for(unsigned i=0;i<37;i++)assert(((unsigned char*)p)[i]==0x33);
    dos_free(p);
}

int main(void){directed();randomized();public_symbols();pointer_relation();puts("portable handle contract tests passed");return 0;}
