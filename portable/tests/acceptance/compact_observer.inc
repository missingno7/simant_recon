#include <unordered_map>
/* DOSBox-X v6 observation and synthetic-input timing extension.
 * State capture is read-only. Only script scheduling and foreground CPU budget
 * change: the real devices/PIC/interrupt code deliver while foreground waits. */
struct CompactPoint { char kind; uint32_t address, after; };
struct CompactView { uint32_t address, bytes, sentinel; };
static std::vector<CompactView> compact_views;
static uint32_t compact_limit=0,compact_interval=256;
static std::vector<uint32_t> compact_frame_times;
#include "vga.h"
extern void CompactMouseFrame(uint32_t words[8], uint16_t masks[32]);
/* Read host-owned planar RAM: CPU aperture reads would change VGA latches.
 * DOSBox vga_draw.cpp M_EGA: interleaved planes, start*4<<addr_shift,
 * address_add=scan_len*(8<<addr_shift). No redraw, guest IO or CPU writes. */
static void CompactScreen(const std::string &path) {
    if (vga.mode!=M_EGA || vga.draw.width!=640 || vga.draw.height!=480 ||
        vga.config.hlines_skip || vga.draw.address_line_total!=1 ||
        vga.config.line_compare<479) { LOG_MSG("Unsupported checkpoint VGA mode");abort(); }
    uint32_t h[24]={0x37464153,640,480,0x12,(uint32_t)vga.config.real_start,
        (uint32_t)(vga.draw.address_add/4),vga.config.pel_panning,vga.config.addr_shift,
        (uint32_t)vga.config.line_compare,vga.attr.color_plane_enable,vga.dac.bits,
        vga.dac.pel_mask,vga.attr.color_select,vga.attr.mode_control};
    uint16_t masks[32]={0};CompactMouseFrame(h+14,masks);
    h[22]=vga.draw.bytes_skip;h[23]=vga.config.hlines_skip;
    uint8_t attr[16],dac[768],valid[256],rgb[48];
    memset(valid,1,sizeof(valid));
    for (unsigned i=0;i<256;++i) {
        dac[i*3]=vga.dac.rgb[i].red;dac[i*3+1]=vga.dac.rgb[i].green;dac[i*3+2]=vga.dac.rgb[i].blue;
    }
    for (unsigned i=0;i<16;++i) {
        attr[i]=vga.attr.palette[i];
        unsigned index=vga.dac.combine[i]&vga.dac.pel_mask;
        for (unsigned c=0;c<3;++c) {
            uint8_t b=dac[index*3+c];rgb[i*3+c]=vga.dac.bits==6 ? (b<<2)|(b>>4) : b;
        }
    }
    std::vector<uint8_t> pixels(640*480);
    const uint32_t start=(vga.config.real_start+vga.draw.bytes_skip)*4u<<vga.config.addr_shift;
    const uint32_t mask=vga.draw.linear_mask;
    for (unsigned y=0;y<480;++y) for (unsigned x=0;x<640;++x) {
        unsigned px=x+vga.config.pel_panning;
        uint32_t addr=(start+y*vga.draw.address_add+(px/8)*4u)&mask;
        unsigned color=0;
        for (unsigned p=0;p<4;++p) color|=((vga.mem.linear[addr+p]>>(7-(px&7)))&1)<<p;
        pixels[y*640+x]=(uint8_t)(color&vga.attr.color_plane_enable);
    }
    FILE *f=fopen(path.c_str(),"wb");if (!f) abort();
    fwrite(h,sizeof(h),1,f);fwrite(attr,1,16,f);fwrite(dac,1,768,f);
    fwrite(valid,1,256,f);fwrite(rgb,1,48,f);fwrite(masks,1,64,f);
    fwrite(&pixels[0],1,pixels.size(),f);if (fclose(f)) abort();
}
static std::string compact_output;
static FILE *compact_fingerprints=NULL, *compact_order=NULL;
static FILE *compact_audio_timer=NULL, *compact_audio_commands=NULL;
static uint64_t CompactOrdinal();
static uint64_t compact_step;
static unsigned compact_phase;
static FILE *compact_content=NULL;
static uint64_t compact_audio_tick=0;
static uint32_t compact_channels=0,compact_volume=0;
static unsigned compact_opl_index[2]={0,0};
static bool compact_dac_argument=false;
static bool compact_voice_active[2]={false,false};
static uint32_t CompactFar(uint32_t a) { return mem_readw(a)+16u*mem_readw(a+2); }
static void CompactContentHead(char tag) {
    fprintf(compact_content,"%c %llu %llu %llu %u",tag,(unsigned long long)compact_audio_tick,
        (unsigned long long)CompactOrdinal(),(unsigned long long)compact_step,compact_phase);
}
static void CompactSampleBoundary(unsigned stop,unsigned ch) {
    if(ch>=2) abort();
    compact_voice_active[ch]=!stop;
    CompactContentHead(stop?'X':'S');fprintf(compact_content," %u",ch);
    if(!stop) {
        uint32_t c=compact_channels+20*ch,s=CompactFar(c+2);
        if(!s) abort();
        unsigned size=mem_readw(s+4);uint32_t data=CompactFar(CompactFar(s));
        fprintf(compact_content," %u %u %u %u %u %u %u ",mem_readw(s+29),mem_readw(c+10),
            (uint16_t)(mem_readw(c+12)-mem_readw(compact_volume))>>8,mem_readw(c+6),mem_readw(c+8),
            mem_readb(c+15)&128,size);
        for(unsigned j=0;j<size;++j) fprintf(compact_content,"%02X",mem_readb(data+j));
    }
    fputc('\n',compact_content);
}
static std::vector<CompactView> compact_audio_views;
static std::vector<uint32_t> compact_audio_hashes;
static void CompactProgress(char tag) {
    if(tag=='Q') for(unsigned ch=0;ch<2;++ch)
        if(compact_voice_active[ch] && !CompactFar(compact_channels+20*ch+2)) CompactSampleBoundary(1,ch);
    std::vector<uint32_t> hashes;
    for(size_t i=0;i<compact_audio_views.size();++i) {
        const CompactView &v=compact_audio_views[i];uint32_t h=2166136261u;
        for(unsigned j=0;j<v.bytes;++j) h=(h^mem_readb(v.address+j))*16777619u;
        hashes.push_back(h);
    }
    if(tag=='Q' && hashes==compact_audio_hashes) return;
    compact_audio_hashes=hashes;CompactContentHead(tag);
    for(size_t i=0;i<hashes.size();++i) fprintf(compact_content," %08X",hashes[i]);
    fputc('\n',compact_content);
}
static void CompactSampleMix(unsigned a,unsigned b) {
    for(unsigned ch=0;ch<2;++ch) {
        uint32_t c=compact_channels+20*ch,s=CompactFar(c+2);
        CompactContentHead('P');fprintf(compact_content," %u %d %u %u\n",ch,s?(int)mem_readw(s+29):-1,
            mem_readw(c),ch?b:a);
    }
}
static bool CompactAudioActive() { return compact_audio_commands!=NULL; }
struct CompactTimerEntry { unsigned kind;uint16_t ss,sp; };
static std::vector<CompactTimerEntry> compact_timers;
static bool compact_key_visible=false;
static std::vector<CompactPoint> compact_points;
static std::unordered_map<uint32_t,std::vector<CompactPoint> > compact_point_index;
static FILE *compact_sound=NULL,*compact_sound_calls=NULL;
static unsigned compact_sound_guard_offset[256],compact_sound_guard_value[256];
static std::vector<uint8_t> compact_sound_code[256];
static uint32_t compact_sound_start[256];
static bool compact_sound_bound[256],compact_sound_skipped[256];
static FILE *compact_file = NULL;
static uint64_t compact_pump = 0;

static char compact_anchor='R';
static uint32_t compact_return = 0, compact_countdown = 0;
static uint32_t compact_keyboard_hook=0,compact_peek_return=0,compact_read_return=0;
struct CompactStream { char kind; uint32_t caller,value; uint64_t count,total; };
static std::vector<CompactStream> compact_streams;
static uint64_t compact_queries=0;
static uint64_t compact_reads=0,compact_hash=1469598103934665603ull;
static uint64_t CompactOrdinal() { return compact_reads+compact_pump+compact_queries+2*compact_step-compact_phase; }
static void CompactAudioWrite(uint32_t port,uint32_t value,uint32_t width,bool output) {
    if (!compact_audio_commands || !output || !DOSBOX_AcceptanceCpuInstructionActive) return;
    if (!((port>=0x388 && port<=0x38b) || (port>=0x220 && port<=0x22f) || port<=0xf || (port>=0x80 && port<=0x8f))) return;
    if (width!=1) { LOG_MSG("Unsupported audio OUT width");abort(); }
    if(compact_content && port>=0x388 && port<=0x38b) {
        unsigned bank=(port-0x388)/2;
        if(!(port&1)) compact_opl_index[bank]=value&255;
        else { CompactContentHead('O');fprintf(compact_content," %u %u %u\n",bank,compact_opl_index[bank],value&255); }
    }
    if(compact_content && !(port>=0x388 && port<=0x38b)) {
        char tag='K';
        if(port==0x22c && compact_dac_argument) compact_dac_argument=false;
        else if(port==0x22c && value==0x10) compact_dac_argument=true;
        else {
            if(port!=0x226 && !(port==0x22c && (value==0xd1 || value==0xd3))) tag='U';
            CompactContentHead(tag);fprintf(compact_content," %u %u\n",port,value&255);
        }
    }
    fprintf(compact_audio_commands,"W %llu %llu %u %X %X\n",(unsigned long long)CompactOrdinal(),
        (unsigned long long)compact_step,compact_phase,port,value&255);
}
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
    if(compact_content) { CompactContentHead('E');fputc('\n',compact_content);fclose(compact_content);compact_content=NULL; }
    if (compact_audio_timer) { fputs("E\n",compact_audio_timer);fclose(compact_audio_timer);compact_audio_timer=NULL; }
    if (compact_audio_commands) {
        fprintf(compact_audio_commands,"E %llu %llu %u\n",(unsigned long long)CompactOrdinal(),(unsigned long long)compact_step,compact_phase);
        fclose(compact_audio_commands);compact_audio_commands=NULL;
    }
    fprintf(compact_file,"Z %llu %llu %u\n",(unsigned long long)compact_pump,
            (unsigned long long)compact_step,compact_phase);
    fclose(compact_file); compact_file = NULL;
    if (compact_fingerprints) { fclose(compact_fingerprints); compact_fingerprints=NULL; }
    if (compact_order) { fclose(compact_order); compact_order=NULL; }
    if (compact_sound) { fclose(compact_sound); compact_sound=NULL; }
    if (compact_sound_calls) {
        fprintf(compact_sound_calls,"E %llu %llu %u\n",(unsigned long long)CompactOrdinal(),(unsigned long long)compact_step,compact_phase);
        fclose(compact_sound_calls);compact_sound_calls=NULL;
    }
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
    compact_content=fopen((compact_output+".content").c_str(),"w");
    if(!compact_content) abort();
    fputs("SIMANT_AUDIO_CONTENT 1\n",compact_content);
    compact_sound=fopen((compact_output+".sound").c_str(),"wb");
    if (!compact_sound) abort();
    compact_sound_calls=fopen((compact_output+".sound-calls").c_str(),"w");
    if (!compact_sound_calls) abort();
    fputs("SIMANT_SOUND_CALLS 1\n",compact_sound_calls);
    compact_audio_timer=fopen((compact_output+".timer").c_str(),"w");
    compact_audio_commands=fopen((compact_output+".audio").c_str(),"w");
    if (!compact_audio_timer || !compact_audio_commands) abort();
    fputs("SIMANT_AUDIO_COMMANDS 1\n",compact_audio_commands);
    DOSBOX_AcceptanceIOWatchArmed=true;
    while (fgets(line,sizeof(line),spec)) {
        CompactView v;
        if(!strncmp(line,"AUDIO ",6)) {
            if(sscanf(line,"AUDIO %x %u",&v.address,&v.bytes)!=2) abort();
            compact_audio_views.push_back(v);continue;
        }
        if(line[0]=='Z') {
            if(sscanf(line,"Z %x %x",&compact_channels,&compact_volume)!=2) abort();continue;
        }
        if (line[0]=='J') {
            uint32_t ms;if (sscanf(line,"J %u",&ms)!=1) abort();
            compact_frame_times.push_back(ms);continue;
        }
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
        if (p.kind=='s') {
            char hex[1800];uint32_t start;
            if (!p.after || p.after>255 || sscanf(line,"s %*x %*x %x %1799s",&start,hex)!=2 || strlen(hex)%2) abort();
            compact_sound_start[p.after]=start;
            unsigned offset,value;
            if (sscanf(line,"s %*x %*x %*x %*s %x %x",&offset,&value)==2) {
                if (!offset || offset>64 || value>65535) abort();
                compact_sound_guard_offset[p.after]=offset;compact_sound_guard_value[p.after]=value;
            }
            for (size_t j=0;j<strlen(hex);j+=2) {
                unsigned value;if (sscanf(hex+j,"%2x",&value)!=1) abort();
                compact_sound_code[p.after].push_back((uint8_t)value);
            }
            if (compact_sound_code[p.after].empty()) abort();
        }
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
    for (size_t i=0;i<compact_points.size();++i) compact_point_index[compact_points[i].address].push_back(compact_points[i]);
    if (!compact_views.empty()) {
        compact_fingerprints=fopen((compact_output+".hash").c_str(),"wb");
        if (!compact_fingerprints) abort();
    }
    atexit(CompactClose);
    fprintf(compact_file,"# simant-compact-observer-v9 per-site ordinal RLE\n");
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
    const auto found=compact_point_index.find(pc);
    if (found==compact_point_index.end()) return;
    const std::vector<CompactPoint> &matched=found->second;
    for (size_t i=0;i<matched.size();++i) {
        const CompactPoint &p=matched[i];
        if (pc!=p.address) continue;
        if(p.kind=='v' || p.kind=='w') {
            CompactSampleBoundary(p.kind=='w',mem_readw(SegPhys(ss)+reg_bp+p.after));continue;
        }
        if(p.kind=='m') { CompactSampleMix(reg_dl,reg_al);continue; }
        if (p.kind=='s') {
            if (compact_timers.empty()) {
                if (!p.after || p.after>255) abort();
                if (!compact_sound_bound[p.after]) {
                    bool equal=true;const bool old=DOSBOX_AcceptanceSuppressMemoryWatch;
                    DOSBOX_AcceptanceSuppressMemoryWatch=true;
                    for (size_t j=0;j<compact_sound_code[p.after].size();++j)
                        if (mem_readb(compact_sound_start[p.after]+(uint32_t)j)!=compact_sound_code[p.after][j]) { equal=false;break; }
                    DOSBOX_AcceptanceSuppressMemoryWatch=old;
                    if (!equal) {
                        if (!compact_sound_skipped[p.after]) fprintf(compact_file,"X sound_code_absent %u %X\n",p.after,pc);
                        compact_sound_skipped[p.after]=true;continue;
                    }
                    compact_sound_bound[p.after]=true;
                    fprintf(compact_file,"X sound_code_bound %u %X %llu\n",p.after,pc,(unsigned long long)CompactOrdinal());
                }
                if (compact_sound_guard_offset[p.after]) {
                    const bool old=DOSBOX_AcceptanceSuppressMemoryWatch;DOSBOX_AcceptanceSuppressMemoryWatch=true;
                    uint32_t stack=SegPhys(ss)+reg_sp;
                    unsigned type=mem_readw(stack+compact_sound_guard_offset[p.after]);
                    unsigned object=mem_readw(stack+compact_sound_guard_offset[p.after]-2);
                    uint32_t caller=mem_readw(stack)+16u*mem_readw(stack+2);
                    DOSBOX_AcceptanceSuppressMemoryWatch=old;
                    fprintf(compact_sound_calls,"C %llu %llu %u %u %u %X\n",(unsigned long long)CompactOrdinal(),(unsigned long long)compact_step,compact_phase,object,type,caller);
                    if (type!=compact_sound_guard_value[p.after]) continue;
                }
                CompactBoundary(pc);++compact_queries;fputc(245,compact_order);fputc(p.after,compact_sound);
            }
            continue;
        }
        if (p.kind=='t' || p.kind=='u') {
            compact_audio_tick+=p.kind=='t'?1:16;
            CompactTimerEntry entry={p.kind=='t'?1u:0u,SegValue(ss),reg_sp};
            compact_timers.push_back(entry);
            fprintf(compact_audio_timer,"# entry %X %llu %u %u\n",pc,(unsigned long long)CompactOrdinal(),(unsigned)entry.ss,(unsigned)entry.sp);
            continue;
        }
        if (p.kind=='x') {
            if (!compact_timers.empty()) {
                const CompactTimerEntry &entry=compact_timers.back();
                if (entry.ss==SegValue(ss) && entry.sp==reg_sp) {
                    fprintf(compact_audio_timer,"T %llu %u\n",(unsigned long long)CompactOrdinal(),p.after?2u:entry.kind);
                    compact_timers.pop_back();CompactProgress('Q');
                }
            }
            continue;
        }
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
                CompactProgress('C');
                compact_return=mem_readw(SegPhys(ss)+reg_sp)+16u*mem_readw(SegPhys(ss)+reg_sp+2);
            }
            else compact_phase=0;
            fprintf(compact_file,"%c %.6f %llu %llu %u %llu %llu %llu\n",p.kind,
                PIC_FullIndex()-acceptance_start_time,
                (unsigned long long)compact_pump,(unsigned long long)compact_step,
                compact_phase,(unsigned long long)compact_reads,(unsigned long long)compact_hash,(unsigned long long)compact_queries);
            if (p.kind=='S' && compact_fingerprints) {
                FILE *dump=NULL;
                bool extra=false;
                while (!compact_frame_times.empty() && PIC_FullIndex()-acceptance_start_time>=compact_frame_times.front()) {
                    extra=true;compact_frame_times.erase(compact_frame_times.begin());
                }
                if (compact_step==1 || compact_step%compact_interval==0 || compact_step==compact_limit || extra) {
                    char suffix[80];sprintf(suffix,".frame.%llu",(unsigned long long)compact_step);
                    dump=fopen((compact_output+suffix).c_str(),"wb");if (!dump) abort();
                    sprintf(suffix,".screen.%llu",(unsigned long long)compact_step);
                    CompactScreen(compact_output+suffix);
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
        if (p.kind=='h') value=reg_ax;
        if (p.kind=='j') value=reg_al;
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
            if (index>=245) abort();
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
