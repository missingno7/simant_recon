/* Read-only DOSBox-X observation extension. Included by build_observer.py.
 * No guest writes, register writes, or scheduling changes. RLE preserves every
 * primitive clock return, including repeated values in busy waits. */
struct CompactPoint { char kind; uint32_t address; };
static std::vector<CompactPoint> compact_points;
static FILE *compact_file = NULL;
static uint64_t compact_pump = 0, compact_step = 0;
static unsigned compact_phase = 0;
static uint32_t compact_return = 0, compact_countdown = 0;
struct CompactStream { char kind; uint32_t caller,value; uint64_t count; };
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
}
static void CompactInit() {
    const char *path = getenv("SIMANT_CAPTURE_OBSERVER");
    if (!path) return;
    FILE *spec = fopen(path,"r");
    char line[2048], output[1800];
    if (!spec || !fgets(output,sizeof(output),spec)) abort();
    output[strcspn(output,"\r\n")] = 0;
    compact_file = fopen(output,"wb");
    if (!compact_file) abort();
    while (fgets(line,sizeof(line),spec)) {
        CompactPoint p;
        if (sscanf(line,"%c %x",&p.kind,&p.address)!=2) abort();
        if (p.kind=='D') { compact_countdown=p.address; continue; }
        compact_points.push_back(p);
    }
    fclose(spec);
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
        if (p.kind=='K' || p.kind=='M') {
            CompactFlush();
            fprintf(compact_file,"D %c %.6f %llu %llu %u %llu %u %u %u %u\n",p.kind,
                PIC_FullIndex()-acceptance_start_time,(unsigned long long)compact_pump,
                (unsigned long long)compact_step,compact_phase,(unsigned long long)compact_reads,
                (unsigned)reg_ax,(unsigned)reg_bx,(unsigned)reg_cx,(unsigned)reg_dx);
            continue;
        }
        if (p.kind=='P') { ++compact_pump; continue; }
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
        compact_hash=(compact_hash^((uint64_t)caller^((uint64_t)(unsigned char)p.kind<<32)^((uint64_t)value<<8)))*1099511628211ull;
        size_t index=0;
        while (index<compact_streams.size() && (compact_streams[index].kind!=p.kind || compact_streams[index].caller!=caller)) ++index;
        if (index==compact_streams.size()) { CompactStream s={p.kind,caller,value,0};compact_streams.push_back(s); }
        CompactStream &s=compact_streams[index];
        if (s.count && s.value!=value) {
            fprintf(compact_file,"R %c %X %u %llu\n",s.kind,s.caller,s.value,(unsigned long long)s.count);
            s.count=0;
        }
        s.value=value;++s.count;
    }
}
