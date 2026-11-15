#include "native_renderer.h"
#include "ymfm/ymfm_opl.h"
#include <algorithm>
#include <array>
#include <deque>
#include <vector>
#include <cstdio>
#include <cstdlib>

namespace {
constexpr uint64_t crystal=14318180, second=1000000000;
enum Kind { Opl, Start, Stop, Positions, Commit, Enable };
struct Event {
    uint64_t ns=0;
    Kind kind=Opl;
    unsigned channel=0, value=0, mask=0;
    SimAudioVoice voice{};
    std::array<uint16_t,4> positions{};
    std::array<uint8_t,4> volumes{};
    std::vector<uint8_t> payload;
};
[[noreturn]] void invalid(const char *why) { std::fprintf(stderr,"Native audio: %s\n",why);std::exit(70); }
class Renderer : public ymfm::ymfm_interface {
public:
    ymfm::ymf262 opl{*this}; // OPL2 compatibility; same pinned FM core/clock as before.
    ymfm::ymf262::output_data fm{};
    uint64_t clock=0, fm_frames=0, timers[2]={}, generated=0, last_event=0;
    std::deque<Event> events;
    std::array<std::vector<uint8_t>,4> payload;
    std::array<uint16_t,4> positions{};
    std::array<uint8_t,4> volumes{};
    std::array<uint8_t,2048> tables;
    unsigned channels=2, active=0;
    int sample=0;
    bool enabled=false;
    Renderer(const uint8_t *v) { std::copy(v,v+2048,tables.begin());opl.reset(); }
    void ymfm_set_timer(uint32_t i,int32_t duration) override { timers[i]=duration<0?0:clock+uint32_t(duration); }
    void advance(uint64_t ns) {
        uint64_t target=(ns/second)*crystal+(ns%second)*crystal/second;
        while(true) {
            unsigned i=timers[0] && (!timers[1] || timers[0]<=timers[1])?0:1;
            uint64_t frame=(fm_frames+1)*288, timer=timers[i]?timers[i]:UINT64_MAX;
            uint64_t next=std::min(frame,timer);
            if(next>target) break;
            clock=next;
            if(timer<=frame) { timers[i]=0;m_engine->engine_timer_expired(i); }
            else { opl.generate(&fm);++fm_frames; }
        }
        clock=target;
    }
    void push(Event e) {
        if(e.ns<last_event) invalid("events go backwards");
        last_event=e.ns;events.push_back(std::move(e));
    }
    void apply(Event &e) {
        switch(e.kind) {
        case Opl: opl.write_address(uint8_t(e.channel));opl.write_data(uint8_t(e.value));break;
        case Start: payload[e.channel]=std::move(e.payload);break;
        case Stop: payload[e.channel].clear();active&=~(1u<<e.channel);break;
        case Positions: channels=e.channel;positions=e.positions;volumes=e.volumes;active=e.mask;break;
        case Commit: {
            unsigned sum=0;
            for(unsigned ch=0;ch<channels;++ch) {
                unsigned v=128;
                if(active&(1u<<ch)) {
                    if(positions[ch]>=payload[ch].size() || volumes[ch]>7) invalid("sample position/volume outside payload");
                    v=tables[volumes[ch]*256+payload[ch][positions[ch]]];
                }
                sum+=v;
            }
            sample=(int(sum/channels)-128)*256;break;
        }
        case Enable: enabled=e.value!=0;break;
        }
    }
    void render(int16_t *out,size_t count,uint64_t first) {
        for(size_t n=0;n<count;++n) {
            uint64_t frame=first+n,ns=(frame/48000)*second+(frame%48000)*second/48000;
            while(!events.empty() && events.front().ns<=ns) {
                advance(events.front().ns);apply(events.front());events.pop_front();
            }
            advance(ns);
            for(unsigned c=0;c<2;++c) out[n*2+c]=int16_t(std::clamp(fm.data[c]+fm.data[c+2]+(enabled?sample:0),-32768,32767));
        }
        generated+=count;
    }
};
Renderer *r(void *p) { return static_cast<Renderer *>(p); }
}
extern "C" {
void *sim_audio_create(const uint8_t *v) { return new Renderer(v); }
void sim_audio_destroy(void *p) { delete r(p); }
void sim_audio_opl(void *p,uint64_t ns,uint8_t reg,uint8_t v) { Event e;e.kind=Opl;e.ns=ns;e.channel=reg;e.value=v;r(p)->push(std::move(e)); }
void sim_audio_voice_start(void *p,uint64_t ns,unsigned ch,const SimAudioVoice *v) {
    if(ch>=4 || !v || !v->payload || !v->length || v->volume>7) invalid("invalid sample start");
    Event e;e.kind=Start;e.ns=ns;e.channel=ch;e.voice=*v;e.voice.payload=nullptr;
    e.payload.assign(v->payload,v->payload+v->length);r(p)->push(std::move(e));
}
void sim_audio_voice_stop(void *p,uint64_t ns,unsigned ch) {
    if(ch>=4) invalid("invalid sample channel");
    Event e;e.kind=Stop;e.ns=ns;e.channel=ch;r(p)->push(std::move(e));
}
void sim_audio_positions(void *p,uint64_t ns,unsigned channels,const uint16_t *positions,const uint8_t *volumes,unsigned mask) {
    if(channels!=2 && channels!=4) invalid("invalid channel count");
    Event e;e.kind=Positions;e.ns=ns;e.channel=channels;e.mask=mask;
    std::copy(positions,positions+4,e.positions.begin());std::copy(volumes,volumes+4,e.volumes.begin());r(p)->push(std::move(e));
}
void sim_audio_commit(void *p,uint64_t ns) { Event e;e.kind=Commit;e.ns=ns;r(p)->push(std::move(e)); }
void sim_audio_enable(void *p,uint64_t ns,int enabled) { Event e;e.kind=Enable;e.ns=ns;e.value=enabled;r(p)->push(std::move(e)); }
void sim_audio_render(void *p,int16_t *s,size_t frames,uint64_t first) { r(p)->render(s,frames,first); }
uint64_t sim_audio_generated_frames(void *p) { return p?r(p)->generated:0; }
}
