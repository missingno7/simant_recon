/* Read-only DOSBox-X observation extension. Included by build_observer.py.
 * No guest writes, register writes, or scheduling changes. RLE preserves every
 * primitive clock return, including repeated values in busy waits. */
struct CompactPoint { char kind; uint32_t address; };
struct CompactView { uint32_t address, bytes, sentinel; };
static std::vector<CompactView> compact_views;
static uint32_t compact_limit=0,compact_interval=256;
static std::string compact_output;
static FILE *compact_fingerprints=NULL;
static bool compact_key_visible=false;
static std::vector<CompactPoint> compact_points;
static FILE *compact_file = NULL;
static uint64_t compact_pump = 0, compact_step = 0;
static unsigned compact_phase = 0;
static char compact_anchor='R';
static uint32_t compact_return = 0, compact_countdown = 0;
static uint32_t compact_keyboard_hook=0;
struct CompactStream { char kind; uint32_t caller,value; uint64_t count,total; };
static std::vector<CompactStream> compact_streams;
static uint64_t compact_reads=0,compact_hash=1469598103934665603ull;
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
        CompactPoint p;
        if (sscanf(line,"%c %x",&p.kind,&p.address)!=2) abort();
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
    fprintf(compact_file,"# simant-compact-observer-v2 per-site ordinal RLE\n");
    DOSBOX_AcceptanceExecArmed = true;
}
static void CompactInput(const AcceptanceEvent &event, double ms) {
    if (!compact_file || event.action > ACCEPT_MOUSE_BUTTON_UP) return;
    CompactFlush();
    fprintf(compact_file,"I %.6f %llu %llu %u %s\n",ms,
        (unsigned long long)compact_pump,(unsigned long long)compact_step,
        compact_phase,event.description.c_str());
}
static void CompactInstruction(uint32_t pc) {
    if (!compact_file) return;
    if (compact_return && pc==compact_return) {
        CompactFlush();compact_phase=0;compact_return=0;
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
            CompactFlush();
            fprintf(compact_file,"D %c %.6f %llu %llu %u %llu %u %u %u %u %c\n",p.kind=='Y'?'K':p.kind,
                PIC_FullIndex()-acceptance_start_time,(unsigned long long)compact_pump,
                (unsigned long long)compact_step,compact_phase,(unsigned long long)compact_reads,
                (unsigned)reg_ax,(unsigned)reg_bx,(unsigned)reg_cx,(unsigned)reg_dx,compact_anchor);
            for (size_t j=0;j<compact_streams.size();++j) {
                const CompactStream &s=compact_streams[j];
                fprintf(compact_file,"J %c %X %llu\n",s.kind,s.caller,(unsigned long long)s.total);
            }
            continue;
        }
        if (p.kind=='P' || p.kind=='W') { ++compact_pump;compact_anchor=p.kind=='P'?'Q':'W';continue; }
        if (p.kind=='S' || p.kind=='E') {
            CompactFlush();
            if (p.kind=='S') {
                ++compact_step; compact_phase=1;
                compact_return=mem_readw(SegPhys(ss)+reg_sp)+16u*mem_readw(SegPhys(ss)+reg_sp+2);
            }
            else compact_phase=0;
            fprintf(compact_file,"%c %.6f %llu %llu %u %llu %llu\n",p.kind,
                PIC_FullIndex()-acceptance_start_time,
                (unsigned long long)compact_pump,(unsigned long long)compact_step,
                compact_phase,(unsigned long long)compact_reads,(unsigned long long)compact_hash);
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
        ++compact_reads;
        compact_anchor='R';
        compact_hash=(compact_hash^((uint64_t)caller^((uint64_t)(unsigned char)p.kind<<32)^((uint64_t)value<<8)))*1099511628211ull;
        size_t index=0;
        while (index<compact_streams.size() && (compact_streams[index].kind!=p.kind || compact_streams[index].caller!=caller)) ++index;
        if (index==compact_streams.size()) { CompactStream s={p.kind,caller,value,0,0};compact_streams.push_back(s); }
        CompactStream &s=compact_streams[index];
        if (s.count && s.value!=value) {
            fprintf(compact_file,"R %c %X %u %llu\n",s.kind,s.caller,s.value,(unsigned long long)s.count);
            s.count=0;
        }
        s.value=value;++s.count;++s.total;
    }
}
