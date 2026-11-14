/* DOSBox-X v5 observation and synthetic-input timing extension.
 * State capture is read-only. Only script scheduling and foreground CPU budget
 * change: the real devices/PIC/interrupt code deliver while foreground waits. */
struct CompactPoint { char kind; uint32_t address, after; };
struct CompactView { uint32_t address, bytes, sentinel; };
static std::vector<CompactView> compact_views;
static uint32_t compact_limit=0,compact_interval=256;
static std::string compact_output;
static FILE *compact_fingerprints=NULL, *compact_order=NULL;
static bool compact_key_visible=false;
static std::vector<CompactPoint> compact_points;
static FILE *compact_file = NULL;
static uint64_t compact_pump = 0, compact_step = 0;
static unsigned compact_phase = 0;
static char compact_anchor='R';
static uint32_t compact_return = 0, compact_countdown = 0;
static uint32_t compact_keyboard_hook=0,compact_peek_return=0,compact_read_return=0;
struct CompactStream { char kind; uint32_t caller,value; uint64_t count,total; };
static std::vector<CompactStream> compact_streams;
static uint64_t compact_queries=0;
static uint64_t compact_reads=0,compact_hash=1469598103934665603ull;
static void AcceptanceRunEvent(Bitu event_index);
static std::vector<Bitu> compact_due;
static bool compact_dispatch=false, compact_holding=false, compact_delivered=false;
static uint32_t compact_hold_pc=0, compact_after=0;
static uint16_t compact_hold_ss=0, compact_hold_sp=0;
static double compact_hold_time=0;
static AcceptanceAction compact_action;
static bool compact_repeat_pending=false;
static unsigned compact_repeat_key=0;
static uint64_t compact_repeat_due=0;
static std::string compact_repeat_name;
extern bool CompactRepeatReady(unsigned key);
extern void CompactDeliverRepeat(unsigned key);
static void CompactInput(const AcceptanceEvent &event, double ms);
/* Hardware repeat expiry is another synthetic keyboard request. Leave the
 * device's wait==0 state intact until its next boundary; an earlier due key-up
 * can cancel it through KEYBOARD_AddKey's normal release path. */
bool CompactDeferRepeat(unsigned key) {
    if (!compact_file) return false;
    if (compact_repeat_pending) abort();
    compact_repeat_pending=true;compact_repeat_key=key;
    compact_repeat_due=(uint64_t)(PIC_FullIndex()-acceptance_start_time);
    fprintf(compact_file,"N repeat_due %.6f %u\n",PIC_FullIndex()-acceptance_start_time,key);
    return true;
}
static void CompactBeginHold(uint32_t pc, uint64_t scheduled, AcceptanceAction action) {
    compact_holding=true;compact_delivered=false;compact_action=action;
    compact_hold_pc=pc;compact_hold_ss=SegValue(ss);compact_hold_sp=reg_sp;
    compact_hold_time=PIC_FullIndex();
    fprintf(compact_file,"U raise %.6f %llu %X %u %u %llu %llu %u %llu %llu\n",compact_hold_time-acceptance_start_time,
        (unsigned long long)scheduled,pc,(unsigned)compact_hold_ss,(unsigned)compact_hold_sp,
        (unsigned long long)compact_pump,(unsigned long long)compact_step,compact_phase,
        (unsigned long long)compact_reads,(unsigned long long)compact_queries);
}
static bool CompactHeld() {
    return compact_holding && SegPhys(cs)+reg_eip==compact_hold_pc &&
        SegValue(ss)==compact_hold_ss && reg_sp==compact_hold_sp;
}
static bool CompactDefer(Bitu index) {
    if (!compact_file || compact_dispatch || index>=acceptance_events.size() ||
        acceptance_events[index].action>ACCEPT_MOUSE_BUTTON_UP) return false;
    compact_due.push_back(index);
    return true;
}
/* Called after the observation hook, before the core fetches any instruction.
 * Returning to Normal_Loop consumes this CPU slice without changing PC/flags;
 * PIC_RunQueue and actual IRQ bodies still run, including IRQ0 while waiting.
 * IF is never forced. A masked/unhandled device is an explicit failure. */
bool CompactYield(void) {
    if (!compact_file) return false;
    const uint32_t pc=SegPhys(cs)+reg_eip;
    if (CompactHeld()) {
        if (compact_delivered) {
            fprintf(compact_file,"U return %.6f %X %u %u\n",PIC_FullIndex()-acceptance_start_time,
                    pc,(unsigned)compact_hold_ss,(unsigned)compact_hold_sp);
            compact_holding=false;
            compact_after=pc; // Serialize other already-due transitions here.
        } else {
            if (PIC_FullIndex()-compact_hold_time>1000) {
                LOG_MSG("QUIET INPUT: no handler after 1000ms at %X",pc);abort();
            }
            CPU_Cycles=0;return true;
        }
    }
    if (!compact_holding && compact_after==pc && !compact_due.empty()) {
        FillFlags();
        if (!(reg_flags & FLAG_IF)) { compact_after=0;return false; }
        const Bitu index=compact_due.front();compact_due.erase(compact_due.begin());
        CompactBeginHold(pc,acceptance_events[index].at_ms,acceptance_events[index].action);
        compact_dispatch=true;AcceptanceRunEvent(index);compact_dispatch=false;
        CPU_Cycles=0;return true;
    }
    if (!compact_holding && compact_after==pc && compact_repeat_pending && compact_due.empty()) {
        FillFlags();
        if (!(reg_flags & FLAG_IF)) { compact_after=0;return false; }
        compact_repeat_pending=false;
        if (CompactRepeatReady(compact_repeat_key)) {
            if (compact_repeat_name.empty()) abort();
            AcceptanceEvent event;
            event.action=ACCEPT_KEY_DOWN;event.at_ms=compact_repeat_due;
            event.key=compact_repeat_name;event.description="key_down "+event.key+" (hardware repeat)";
            CompactBeginHold(pc,event.at_ms,event.action);
            CompactInput(event,PIC_FullIndex()-acceptance_start_time);
            CompactDeliverRepeat(compact_repeat_key);
            CPU_Cycles=0;return true;
        }
        fprintf(compact_file,"N repeat_cancel %.6f %u\n",PIC_FullIndex()-acceptance_start_time,compact_repeat_key);
    }
    if (!compact_holding && compact_after==pc) compact_after=0;
    return false;
}
static void CompactBoundary(uint32_t after) {
    if (!compact_holding) compact_after=after;
}
static void CompactFlush() {
    for (size_t i=0;i<compact_streams.size();++i) {
        CompactStream &s=compact_streams[i];
        if (!s.count) continue;
        fprintf(compact_file,"R %c %X %u %llu\n",s.kind,s.caller,s.value,(unsigned long long)s.count);
        s.count=0;
    }
}
static void CompactClose() {
    if (!compact_file) return;
    CompactFlush();
    fprintf(compact_file,"Z %llu %llu %u\n",(unsigned long long)compact_pump,
            (unsigned long long)compact_step,compact_phase);
    fclose(compact_file); compact_file = NULL;
    if (compact_fingerprints) { fclose(compact_fingerprints); compact_fingerprints=NULL; }
    if (compact_order) { fclose(compact_order); compact_order=NULL; }
}
static void CompactInit() {
    const char *path = getenv("SIMANT_CAPTURE_OBSERVER");
    if (!path) return;
    FILE *spec = fopen(path,"r");
    char line[2048], output[1800];
    if (!spec || !fgets(output,sizeof(output),spec)) abort();
    output[strcspn(output,"\r\n")] = 0;
    compact_file = fopen(output,"wb");
    compact_output=output;
    if (!compact_file) abort();
    compact_order=fopen((compact_output+".order").c_str(),"wb");
    if (!compact_order) abort();
    while (fgets(line,sizeof(line),spec)) {
        CompactView v;
        if (line[0]=='H') {
            if (sscanf(line,"H %x %u %u",&v.address,&v.bytes,&v.sentinel)!=3 || !v.bytes) abort();
            compact_views.push_back(v); continue;
        }
        if (line[0]=='L') {
            if (sscanf(line,"L %u %u",&compact_limit,&compact_interval)!=2 || !compact_limit || !compact_interval) abort();
            continue;
        }
        CompactPoint p; p.after=0;
        if (sscanf(line,"%c %x %x",&p.kind,&p.address,&p.after)<2) abort();
        if (p.kind=='p') { compact_peek_return=p.address;continue; }
        if (p.kind=='q') { compact_read_return=p.address;continue; }
        if (p.kind=='F' && !p.address) {
            uint32_t entry=mem_readw(0x58)+16u*mem_readw(0x5a);
            /* Pinned callback.cpp: CB_INT16 = STI; FE38 callback-id; IRET.
             * The callback samples the BIOS ring atomically in host code. */
            if (mem_readb(entry)!=0xfb || mem_readw(entry+1)!=0x38fe || mem_readb(entry+5)!=0xcf) abort();
            p.address=entry+1;p.after=entry+5;
            fprintf(compact_file,"B %X %u\n",p.address,(unsigned)mem_readw(entry+3));
        }
        if (p.kind=='D') { compact_countdown=p.address; continue; }
        if (p.kind=='O') { compact_keyboard_hook=p.address; continue; }
        compact_points.push_back(p);
    }
    fclose(spec);
    if (!compact_views.empty()) {
        compact_fingerprints=fopen((compact_output+".hash").c_str(),"wb");
        if (!compact_fingerprints) abort();
    }
    atexit(CompactClose);
    fprintf(compact_file,"# simant-compact-observer-v5 per-site ordinal RLE\n");
    DOSBOX_AcceptanceExecArmed = true;
}
static void CompactInput(const AcceptanceEvent &event, double ms) {
    if (!compact_file || event.action > ACCEPT_MOUSE_BUTTON_UP) return;
    if (event.action==ACCEPT_KEY_DOWN) compact_repeat_name=event.key;
    CompactFlush();
    fprintf(compact_file,"I %.6f %llu %llu %u %s\n",(double)event.at_ms,
        (unsigned long long)compact_pump,(unsigned long long)compact_step,
        compact_phase,event.description.c_str());
}
static void CompactInstruction(uint32_t pc) {
    if (!compact_file) return;
    if (compact_return && pc==compact_return) {
        CompactFlush();compact_phase=0;compact_return=0;fputc(251,compact_order);CompactBoundary(pc);
        fprintf(compact_file,"E %.6f %llu %llu 0\n",PIC_FullIndex()-acceptance_start_time,
            (unsigned long long)compact_pump,(unsigned long long)compact_step);
    }
    for (size_t i=0;i<compact_points.size();++i) {
        const CompactPoint &p=compact_points[i];
        if (pc!=p.address) continue;
        if (p.kind=='G') { compact_key_visible=false;continue; }
        if (p.kind=='A') {
            if (!reg_ax) { compact_key_visible=false;continue; }
            if (compact_key_visible || reg_ax<256) continue;
            compact_key_visible=true;CompactFlush();
            fprintf(compact_file,"A %.6f %llu %u %u\n",PIC_FullIndex()-acceptance_start_time,
                    (unsigned long long)compact_step,compact_phase,(unsigned)reg_ax);
            for (size_t j=0;j<compact_streams.size();++j) {
                const CompactStream &s=compact_streams[j];
                fprintf(compact_file,"J %c %X %llu\n",s.kind,s.caller,(unsigned long long)s.total);
            }
            continue;
        }
        /* Menus disable the game's scan processor, but BIOS INT 15h/AH=4Fh
         * still observes the real hardware scan. Keep the established K point
         * when enabled; observe the BIOS intercept only while disabled. */
        if (p.kind=='Y' && (!compact_keyboard_hook || mem_readb(compact_keyboard_hook) || reg_ah!=0x4f)) continue;
        if (p.kind=='K' || p.kind=='M' || p.kind=='Y') {
            if (compact_holding && ((p.kind=='M' && compact_action>=ACCEPT_MOUSE_MOVE) ||
                (p.kind!='M' && compact_action<=ACCEPT_KEY_UP && (reg_ax&255)!=0xe0)))
                compact_delivered=true;
            CompactFlush();
            fprintf(compact_file,"D %c %.6f %llu %llu %u %llu %u %u %u %u %c %llu\n",p.kind=='Y'?'K':p.kind,
                PIC_FullIndex()-acceptance_start_time,(unsigned long long)compact_pump,
                (unsigned long long)compact_step,compact_phase,(unsigned long long)compact_reads,
                (unsigned)reg_ax,(unsigned)reg_bx,(unsigned)reg_cx,(unsigned)reg_dx,compact_anchor,(unsigned long long)compact_queries);
            for (size_t j=0;j<compact_streams.size();++j) {
                const CompactStream &s=compact_streams[j];
                fprintf(compact_file,"J %c %X %llu\n",s.kind,s.caller,(unsigned long long)s.total);
            }
            continue;
        }
        if (p.kind=='a' || p.kind=='b' || p.kind=='c' || p.kind=='d') {
            CompactBoundary(p.after?p.after:pc);++compact_queries;fputc(p.kind=='a'?246:p.kind=='b'?247:p.kind=='c'?248:249,compact_order);continue;
        }
        if (p.kind=='F') {
            uint32_t stack=SegPhys(ss)+reg_sp;
            uint32_t caller=mem_readw(stack)+16u*mem_readw(stack+2);
            bool peek=caller==compact_peek_return && reg_ah==1;
            bool pop=caller==compact_read_return && reg_ah==0 && mem_readw(0x41a)!=mem_readw(0x41c);
            if (peek || pop) { CompactBoundary(p.after);++compact_queries;fputc(peek?252:253,compact_order); }
            continue;
        }
        if (p.kind=='P' || p.kind=='W') { CompactBoundary(p.after?p.after:pc);++compact_pump;compact_anchor=p.kind=='P'?'Q':'W';fputc(p.kind=='P'?254:255,compact_order);continue; }
        if (p.kind=='S' || p.kind=='E') {
            CompactBoundary(pc);CompactFlush();
            if (p.kind=='S') {
                fputc(250,compact_order);
                ++compact_step; compact_phase=1;
                compact_return=mem_readw(SegPhys(ss)+reg_sp)+16u*mem_readw(SegPhys(ss)+reg_sp+2);
            }
            else compact_phase=0;
            fprintf(compact_file,"%c %.6f %llu %llu %u %llu %llu %llu\n",p.kind,
                PIC_FullIndex()-acceptance_start_time,
                (unsigned long long)compact_pump,(unsigned long long)compact_step,
                compact_phase,(unsigned long long)compact_reads,(unsigned long long)compact_hash,(unsigned long long)compact_queries);
            if (p.kind=='S' && compact_fingerprints) {
                FILE *dump=NULL;
                if (compact_step==1 || compact_step%compact_interval==0 || compact_step==compact_limit) {
                    char suffix[80];sprintf(suffix,".frame.%llu",(unsigned long long)compact_step);
                    dump=fopen((compact_output+suffix).c_str(),"wb");if (!dump) abort();
                }
                for (size_t j=0;j<compact_views.size();++j) {
                    const CompactView &v=compact_views[j];uint32_t hash=2166136261u;
                    uint32_t length=v.bytes;
                    if (v.sentinel) for (uint32_t k=0;k+1<length;k+=2)
                        if (mem_readw(v.address+k)==0x8000) { length=k+2;break; }
                    for (uint32_t k=0;k<v.bytes;++k) {
                        uint8_t b=mem_readb(v.address+k);
                        if (k<length) hash=(hash^b)*16777619u;
                        if (dump) fwrite(&b,1,1,dump);
                    }
                    fwrite(&hash,4,1,compact_fingerprints);
                }
                if (dump) fclose(dump);
                if (compact_step==compact_limit) {
                    CompactClose();DOSBOX_AcceptanceExit();return;
                }
            }
            continue;
        }
        const bool old = DOSBOX_AcceptanceSuppressMemoryWatch;
        DOSBOX_AcceptanceSuppressMemoryWatch = true;
        uint32_t stack = SegPhys(ss) + reg_sp;
        uint32_t caller = mem_readw(stack) + 16u * mem_readw(stack+2);
        uint32_t value = (uint32_t)reg_ax | ((uint32_t)reg_dx<<16);
        if (p.kind=='C') { value=mem_readw(compact_countdown); caller=0; }
        if (p.kind=='V') { value=mem_readw(0x46c); caller=0; }
        DOSBOX_AcceptanceSuppressMemoryWatch = old;
        CompactBoundary(p.after?p.after:pc);
        ++compact_reads;
        compact_anchor='R';
        compact_hash=(compact_hash^((uint64_t)caller^((uint64_t)(unsigned char)p.kind<<32)^((uint64_t)value<<8)))*1099511628211ull;
        size_t index=0;
        while (index<compact_streams.size() && (compact_streams[index].kind!=p.kind || compact_streams[index].caller!=caller)) ++index;
        if (index==compact_streams.size()) {
            if (index>=246) abort();
            CompactStream s={p.kind,caller,value,0,0};compact_streams.push_back(s);
            fprintf(compact_file,"O %u %c %X\n",(unsigned)index,p.kind,caller);
        }
        const unsigned char site=(unsigned char)index;
        if (fwrite(&site,1,1,compact_order)!=1) abort();
        CompactStream &s=compact_streams[index];
        if (s.count && s.value!=value) {
            fprintf(compact_file,"R %c %X %u %llu\n",s.kind,s.caller,s.value,(unsigned long long)s.count);
            s.count=0;
        }
        s.value=value;++s.count;++s.total;
    }
}
