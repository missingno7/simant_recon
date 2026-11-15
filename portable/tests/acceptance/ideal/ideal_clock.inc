#include "native_clock_v1.h"
extern double IdealNext(double);
extern void IdealMove(double);
extern void IdealStart();
extern void IdealResetPITPhase();
extern unsigned long long IdealSlices;
extern long long IdealSliceMin,IdealSliceMax;
struct IdealSiteV2 {
    char mode;std::string service;
    unsigned segment=0,base=0,index=0,displacement=0;std::string signature;
};
static uint16_t IdealRegister(unsigned reg) {
    switch(reg) {
    case 0:return 0;case 1:return reg_bx;case 2:return reg_bp;case 3:return reg_si;case 4:return reg_di;
    case 5:return reg_ax;case 6:return reg_cx;case 7:return reg_dx;case 8:return reg_sp;default:abort();
    }
}
static uint16_t IdealSegment(unsigned seg) {
    switch(seg) {case 1:return SegValue(es);case 2:return SegValue(cs);case 3:return SegValue(ss);case 4:return SegValue(ds);default:abort();}
}
static std::unordered_map<uint32_t,IdealSiteV2> ideal_sites;
static bool ideal_ready=false,ideal_busy=false,ideal_yield=false;
static uint32_t ideal_pc=0;
static uint16_t ideal_ss=0,ideal_sp=0;
static uint64_t ideal_ns=0,ideal_target_ns=0,ideal_quantum_ns=1000000;
static uint64_t ideal_instructions=0,ideal_reads=0,ideal_moves=0,ideal_stall=0;
static uint64_t ideal_pit_reads=0,ideal_vga_reads=0;
static bool ideal_video_written=false;
static uint64_t ideal_video_write_ns=0,ideal_video_writes=0,ideal_palette_writes=0;
void IdealVideoWrite(unsigned kind) {
    if(!IdealActive) return;
    ideal_video_written=true;
    ideal_video_write_ns=(uint64_t)((double)PIC_FullIndex()*1000000.0+0.5);
    if(kind) ++ideal_palette_writes;else ++ideal_video_writes;
}
static uint32_t ideal_queue_capacity=0,ideal_queue_write=0,ideal_queue_read=0;
static size_t ideal_input_next=0;
static FILE *ideal_log=NULL;
extern uint32_t PIT0_GetAssignedCounter();
static void IdealCheckpoint() {
    if(ideal_log) fprintf(ideal_log,"S %llu %llu %u %u\n",(unsigned long long)compact_step,
        (unsigned long long)ideal_ns,(uint32_t)(mem_readd(0x46c)-0x1800b0u/2u),PIT0_GetAssignedCounter());
}
struct IdealScopeV2 {uint32_t return_pc;uint16_t ss,sp;};
static std::vector<IdealScopeV2> ideal_scopes,ideal_internal_scopes;
static bool IdealAtOrigin(uint32_t pc) {
    return pc==ideal_pc && SegValue(ss)==ideal_ss && reg_sp==ideal_sp;
}
/* A CPU slice may end inside an ISR. It must not dispatch another equal-time
 * event until that complete guest handler returns to this transaction's PC. */
static bool ideal_async_busy=false;
static uint32_t ideal_async_pc=0,ideal_dispatch_pc=0;
static uint16_t ideal_async_ss=0,ideal_async_sp=0,ideal_dispatch_ss=0,ideal_dispatch_sp=0;
static bool IdealAtAsyncOrigin() {
    return SegPhys(cs)+reg_eip==ideal_async_pc && SegValue(ss)==ideal_async_ss && reg_sp==ideal_async_sp;
}
bool IdealDispatchAllowed() {
    if(compact_holding) return CompactHeld();
    if(ideal_async_busy) return IdealAtAsyncOrigin();
    if(ideal_busy) return IdealAtOrigin(SegPhys(cs)+reg_eip);
    return true; /* pending zero-time reload edges also obey guest STI */
}
void IdealBeforeIRQDispatch() {
    ideal_dispatch_pc=SegPhys(cs)+reg_eip;ideal_dispatch_ss=SegValue(ss);ideal_dispatch_sp=reg_sp;
}
void IdealAfterIRQDispatch() {
    if(!ideal_busy && !compact_holding && !ideal_async_busy &&
       (ideal_dispatch_pc!=SegPhys(cs)+reg_eip || ideal_dispatch_ss!=SegValue(ss) || ideal_dispatch_sp!=reg_sp)) {
        ideal_async_busy=true;ideal_async_pc=ideal_dispatch_pc;
        ideal_async_ss=ideal_dispatch_ss;ideal_async_sp=ideal_dispatch_sp;
    }
}
static void IdealStats() {
    if(!ideal_log) return;
    fprintf(ideal_log,"STATS instructions=%llu reads=%llu moves=%llu ns=%llu pit_reads=%llu vga_reads=%llu sound_isrs=%llu\n",
        (unsigned long long)ideal_instructions,(unsigned long long)ideal_reads,
        (unsigned long long)ideal_moves,(unsigned long long)ideal_ns,
        (unsigned long long)ideal_pit_reads,(unsigned long long)ideal_vga_reads,(unsigned long long)compact_sound_isrs);
    fprintf(ideal_log,"SLICES count=%llu min=%lld max=%lld\n",IdealSlices,IdealSliceMin,IdealSliceMax);
    fflush(ideal_log);
    fprintf(ideal_log,"VIDEO aperture=%llu palette=%llu\n",(unsigned long long)ideal_video_writes,(unsigned long long)ideal_palette_writes);
}
static void IdealInit() {
    ideal_ready=true;
    const char *path=getenv("SIMANT_IDEAL");if(!path) return;
    FILE *f=fopen(path,"r");if(!f) abort();
    if(fscanf(f,"%llu",&ideal_quantum_ns)!=1 || !ideal_quantum_ns || ideal_quantum_ns>1000000) abort();
    char line[512],mode,service[200];unsigned pc;
    while(fgets(line,sizeof(line),f)) {
        unsigned segment,base,index,displacement;char signature[64];
        if(sscanf(line,"B %x %u %u %u %x %63s",&pc,&segment,&base,&index,&displacement,signature)==6) {
            IdealSiteV2 site;site.mode='B';site.service="dos_keyboard_modifiers";
            site.segment=segment;site.base=base;site.index=index;site.displacement=displacement;site.signature=signature;
            ideal_sites[pc]=site;continue;
        }
        if(sscanf(line,"QUEUE %x %x %x",&ideal_queue_capacity,&ideal_queue_write,&ideal_queue_read)==3) continue;
        if(sscanf(line,"%c %x %199s",&mode,&pc,service)==3) ideal_sites[pc]={mode,service};
    }
    fclose(f);
    ideal_log=fopen((compact_output+".ideal").c_str(),"w");if(!ideal_log) abort();
}
static void IdealAdmitInputs() {
    uint32_t elapsed=(uint32_t)(mem_readd(0x46c)-0x1800b0u/2u);
    while(ideal_input_next<acceptance_events.size()) {
        const AcceptanceEvent &event=acceptance_events[ideal_input_next];
        if(!event.at_ms) { ++ideal_input_next;continue; }
        if(event.at_ms>elapsed) break;
        if(event.action<=ACCEPT_MOUSE_BUTTON_UP) compact_due.push_back((Bitu)ideal_input_next);
        else if(event.action==ACCEPT_EXIT) {
            fprintf(ideal_log,"SCRIPT_END tick=%u step=%llu\n",elapsed,(unsigned long long)compact_step);
            IdealStats();CompactClose();DOSBOX_AcceptanceExit();
        }
        ++ideal_input_next;
    }
}
static bool IdealBefore(uint32_t pc) {
    ++ideal_instructions;
    static uint32_t traced_bios=0;
    if(ideal_log && IdealActive && traced_bios!=mem_readd(0x46c)) {
        traced_bios=mem_readd(0x46c);
        fprintf(ideal_log,"T %.6f %u %X\n",(double)PIC_FullIndex()*1000000.0,traced_bios,pc);
    }
    if(!compact_file) return false;
    if(!ideal_ready) IdealInit();
    if(ideal_async_busy && IdealAtAsyncOrigin()) ideal_async_busy=false;
    while(!ideal_internal_scopes.empty() && ideal_internal_scopes.back().return_pc==pc &&
        ideal_internal_scopes.back().ss==SegValue(ss) && ideal_internal_scopes.back().sp==reg_sp) ideal_internal_scopes.pop_back();
    while(!ideal_scopes.empty() && ideal_scopes.back().return_pc==pc &&
        ideal_scopes.back().ss==SegValue(ss) && ideal_scopes.back().sp==reg_sp) ideal_scopes.pop_back();
    ideal_yield=false;
    if(ideal_busy) {
        if(!IdealAtOrigin(pc)) return false;
        if(++ideal_stall>2000000) {IdealStats();LOG_MSG("IDEAL transaction stalled at %X",pc);abort();}
        const double target=(double)ideal_target_ns/1000000.0;
        if((double)PIC_FullIndex()+1e-10<target || IdealNext(target+1e-6)<=(double)PIC_FullIndex()+1e-10) {
            IdealMove(target);++ideal_moves;ideal_yield=true;return true;
        }
        ideal_ns=ideal_target_ns;ideal_busy=false;ideal_stall=0;
        IdealAdmitInputs();
        if(!compact_holding) compact_after=pc;
        return false;
    }
    if(compact_holding) return false;
    auto found=ideal_sites.find(pc);
    if(found==ideal_sites.end()) {
        if(IdealActive) {
            unsigned op=mem_readb(pc);
            if((op==0xe4 && mem_readb(pc+1)==0x40) || (op==0xec && reg_dx==0x40)) ++ideal_pit_reads;
            if((op==0xe4 && mem_readb(pc+1)==0xda) || (op==0xec && reg_dx==0x3da)) ++ideal_vga_reads;
        }
        return false;
    }
    const IdealSiteV2 &site=found->second;
    if(site.mode=='B') {
        /* Static instruction census, live effective address. Other far-byte
         * reads in those functions consume no Q, nor do overwritten overlays. */
        for(size_t i=0;i<site.signature.size()/2;++i) {
            unsigned byte;if(sscanf(site.signature.substr(2*i,2).c_str(),"%x",&byte)!=1) abort();
            if(mem_readb(pc+(uint32_t)i)!=byte) return false;
        }
        uint16_t offset=(uint16_t)(IdealRegister(site.base)+IdealRegister(site.index)+site.displacement);
        if(((16u*IdealSegment(site.segment)+offset)&0xfffffu)!=0x417) return false;
    }
    if(site.mode=='A') {
        IdealStart();IdealResetPITPhase();
        // Explicit native machine initial policy, not expected simulation data.
        mem_writed(0x46c,0x1800b0u/2u);mem_writeb(0x470,0);mem_writed(0x46c0,0);
        acceptance_start_time=0;
        PIC_RemoveEvents(AcceptanceRunEvent);compact_due.clear();
        fprintf(ideal_log,"START native-clock-v1 Q=%llu pc=%X\n",(unsigned long long)ideal_quantum_ns,pc);
        ideal_sites.erase(found);return false;
    }
    if(!IdealActive) return false;
    if(site.mode=='I') {
        uint32_t stack=SegPhys(ss)+reg_sp;
        ideal_internal_scopes.push_back({mem_readw(stack)+16u*mem_readw(stack+2),SegValue(ss),(uint16_t)(reg_sp+4)});
        return false;
    }
    if(ideal_async_busy || !ideal_internal_scopes.empty()) return false;
    FillFlags();
    bool entry_if=(reg_flags&FLAG_IF)!=0;
    const char *service=site.service.c_str();
    if(!ideal_scopes.empty() && !strcmp(service,"mouse_refresh_cursor")) return false;
    if(site.mode=='F') {
        entry_if=(mem_readw(SegPhys(ss)+reg_sp+4)&FLAG_IF)!=0;
        if(reg_ah==0 || reg_ah==0x10) service="host_read_key_blocking";
        else if(reg_ah==1 || reg_ah==0x11) service="host_key_available";
        else if(reg_ah==2 || reg_ah==0x12) service="dos_keyboard_modifiers";
        else return false;
    }
    if(site.mode=='E') {
        // The native enqueue samples its BIOS stamp only when its ring has room.
        unsigned next=mem_readw(ideal_queue_write)+1;
        if(next>=mem_readw(ideal_queue_capacity)) next=0;
        if(next==mem_readw(ideal_queue_read)) return false;
    }
    if(!entry_if || !compact_timers.empty()) return false;
    uint64_t charge=DosClockReadQuantum(service,ideal_quantum_ns);
    if(!charge) return false;
    if(ideal_video_written && DosClockDisplayFrame(ideal_video_write_ns)!=DosClockDisplayFrame(ideal_ns)) ideal_video_written=false;
    charge=DosClockDisplayCharge(ideal_ns,charge,ideal_video_written);
    if(site.mode=='M') {
        uint32_t stack=SegPhys(ss)+reg_sp;
        ideal_scopes.push_back({mem_readw(stack)+16u*mem_readw(stack+2),SegValue(ss),(uint16_t)(reg_sp+4)});
    }
    ideal_pc=pc;ideal_ss=SegValue(ss);ideal_sp=reg_sp;
    ideal_target_ns=ideal_ns+charge;ideal_busy=true;++ideal_reads;
    uint32_t trace_stack=SegPhys(ss)+reg_sp;
    uint32_t trace_caller=mem_readw(trace_stack)+16u*mem_readw(trace_stack+2);
    fprintf(ideal_log,"R %llu %llu %X %s %X %X:%X\n",(unsigned long long)ideal_reads,(unsigned long long)ideal_target_ns,pc,service,trace_caller,SegValue(ss),reg_sp);
    IdealMove((double)ideal_target_ns/1000000.0);++ideal_moves;
    ideal_yield=true;return true;
}
static bool IdealYield() {
    if(ideal_yield) {ideal_yield=false;CPU_Cycles=0;return true;}
    return false;
}
