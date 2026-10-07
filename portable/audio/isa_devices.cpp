#include "isa_devices.h"
#include "ymfm/ymfm_opl.h"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <algorithm>
#include <array>
#include <deque>

namespace {
constexpr uint64_t opl_clock = 14318180;
class Devices : public ymfm::ymfm_interface {
public:
    ymfm::ymf262 opl;
    uint64_t clock = 0, timers[2] = {0,0}, busy_end = 0;
    uint64_t fm_frames = 0;
    ymfm::ymf262::output_data fm_output{};
    std::array<ymfm::ymf262::output_data,4096> fm_history{};
    struct DacChange { uint64_t ns; uint8_t value; bool enabled; };
    std::deque<DacChange> dac_changes;
    uint8_t rendered_dac = 128;
    bool rendered_enabled = false;
    uint8_t dac = 128, speaker = 0, reset = 0, response = 0;
    bool reset_response = false, direct_data = false, enabled = false;
    FILE *dsp_log = nullptr, *opl_log = nullptr;
    Devices() : opl(*this) { opl.reset(); }
    ~Devices() { if(dsp_log) std::fclose(dsp_log); if(opl_log) std::fclose(opl_log); }
    void ymfm_set_timer(uint32_t timer, int32_t duration) override {
        timers[timer] = duration < 0 ? 0 : clock + uint32_t(duration);
    }
    void ymfm_set_busy_end(uint32_t clocks) override { busy_end = clock + clocks; }
    bool ymfm_is_busy() override { return clock < busy_end; }
    void advance(uint64_t ns) {
        uint64_t target = (ns / 1000000000) * opl_clock +
                          (ns % 1000000000) * opl_clock / 1000000000;
        while (true) {
            unsigned timer = timers[0] && (!timers[1] || timers[0] <= timers[1]) ? 0 : 1;
            uint64_t next_frame = (fm_frames + 1) * 288;
            uint64_t next_timer = timers[timer] ? timers[timer] : UINT64_MAX;
            uint64_t next = std::min(next_frame,next_timer);
            if(next > target) break;
            clock = next;
            if(next_timer <= next_frame) {
                timers[timer] = 0;m_engine->engine_timer_expired(timer);
            } else {
                opl.generate(&fm_output);++fm_frames;
                fm_history[fm_frames % fm_history.size()] = fm_output;
            }
        }
        clock = std::max(clock, target);
    }
    void out(uint16_t port, uint8_t value, uint64_t ns) {
        advance(ns);
        FILE *log = port >= 0x220 && port <= 0x22f ? dsp_log :
                    port >= 0x388 && port <= 0x38b ? opl_log : nullptr;
        if (log) std::fprintf(log, "%.6f out %04X 1 %02X\n", ns / 1000000.0, port, value);
        if (port >= 0x388 && port <= 0x38b) opl.write(port - 0x388, value);
        else if (port == 0x226) {
            if(reset && !value) {
                reset_response = true;dac = 128;direct_data = false;enabled = false;
                dac_changes.push_back({ns,dac,enabled});
            }
            reset = value;
        } else if (port == 0x22c) {
            if (direct_data) { dac = value;direct_data = false;dac_changes.push_back({ns,dac,enabled}); }
            else if (value == 0x10) direct_data = true;
            else if (value == 0xd1) { enabled = true;dac_changes.push_back({ns,dac,enabled}); }
            else if (value == 0xd3) { enabled = false;dac_changes.push_back({ns,dac,enabled}); }
            else {
                std::fprintf(stderr, "Unimplemented SB DSP command %02X (DMA is not used by canonical mode 6)\n", value);
                std::exit(70);
            }
        } else if (port == 0x61) speaker = value;
        else if ((port >= 0x210 && port <= 0x26f) || port == 0x20 || port == 0x40 || port == 0x43) {
            /* Absent candidate SB cards read FF; PIT/PIC scheduling is hosted
             * by the source ISR projection, not by host CPU interrupts. */
        } else { std::fprintf(stderr, "Unimplemented audio ISA OUT %04X\n",port); std::exit(70); }
    }
    uint8_t in(uint16_t port, uint64_t ns) {
        advance(ns);
        if(port >= 0x388 && port <= 0x38b) return opl.read(port - 0x388);
        if(port == 0x22c) return 0; // direct DAC accepts one byte immediately
        if(port == 0x22e) return reset_response ? 0x80 : 0;
        if(port == 0x22a) { uint8_t value=reset_response?0xaa:0xff;reset_response=false;return value; }
        if(port == 0x61) return speaker;
        if(port >= 0x210 && port <= 0x26f) return 0xff;
        std::fprintf(stderr,"Unimplemented audio ISA IN %04X\n",port); std::exit(70);
    }
    void render(int16_t *stereo, uint64_t ns) {
        advance(ns);
        const uint64_t target_clock=(ns/1000000000)*opl_clock+(ns%1000000000)*opl_clock/1000000000;
        const uint64_t target = target_clock / 288;
        if(fm_frames-target >= fm_history.size()) {
            std::fprintf(stderr,"OPL render history exceeded the device boundary\n");std::exit(70);
        }
        const auto &frame=fm_history[target % fm_history.size()];
        while(!dac_changes.empty() && dac_changes.front().ns<=ns) {
            rendered_dac=dac_changes.front().value;rendered_enabled=dac_changes.front().enabled;
            dac_changes.pop_front();
        }
        const int sb = rendered_enabled ? (int(rendered_dac) - 128) * 256 : 0;
        for(unsigned c=0;c<2;++c) {
            int sample = frame.data[c] + frame.data[c+2] + sb;
            stereo[c] = int16_t(std::max(-32768, std::min(32767,sample)));
        }
    }
};
}
extern "C" {
void *sim_isa_audio_create(void) { return new Devices; }
void sim_isa_audio_destroy(void *device) { delete static_cast<Devices *>(device); }
void sim_isa_audio_out(void *d,uint16_t p,uint8_t v,uint64_t ns) { static_cast<Devices *>(d)->out(p,v,ns); }
uint8_t sim_isa_audio_in(void *d,uint16_t p,uint64_t ns) { return static_cast<Devices *>(d)->in(p,ns); }
void sim_isa_audio_render(void *d,int16_t *s,uint64_t ns) { static_cast<Devices *>(d)->render(s,ns); }
int sim_isa_audio_trace(void *d,const char *directory) {
    auto *device = static_cast<Devices *>(d);
    if(!directory) return 1;
    device->dsp_log = std::fopen((std::string(directory)+"/io-sb_dsp").c_str(),"w");
    device->opl_log = std::fopen((std::string(directory)+"/io-opl").c_str(),"w");
    return device->dsp_log && device->opl_log;
}
}
