#include "menu_quit_probe.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(int argc,char **argv)
{
    char text[MQ_TEXT_CAP]; size_t length=0; MenuQuitProbeInput in;
    MenuQuitProbeResult out; int i;
    assert(argc==2);
    assert(menu_quit_probe_load_resource(argv[1],text,sizeof(text),&length)==0);
    memset(&in,0,sizeof(in)); in.dirty=1; in.screen_width_metric=0x140;
    in.frame_enabled=1; in.prompt_count=1;
    in.window_rect=(PortableMenuQuitRect){1,2,101,52};
    in.text_rect=(PortableMenuQuitRect){3,4,99,48};
    in.save_count=1; in.saves[0]=1;
    for(i=0;i<6;i++) {
        memset(in.keys,0,sizeof(in.keys)); memset(in.events,0,sizeof(in.events));
        in.key_count[0]=1; in.keys[0][0]=(int16_t[]){13,'D','d','S','s',27}[i];
        assert(menu_quit_probe_run(&in,text,length,&out)==0);
        assert(out.status==((i==5)?PORTABLE_MENU_QUIT_CANCELLED:PORTABLE_MENU_QUIT_EXIT_REQUESTED));
        assert(out.dirty_after==((i==3||i==4)?0:1));
        assert(out.events[0].kind==1 && out.events[0].args[0]==0x2100);
        assert(out.events[1].kind==2 && out.events[1].args[0]==0x80 &&
               out.events[1].args[1]==10 && out.events[1].args[2]==1);
        assert(out.events[3].kind==4 && out.events[3].args[0]==2);
        assert(out.events[out.event_count-1].kind==(i==5?15:17));
    }
    memset(&in,0,sizeof(in)); in.dirty=0; in.prompt_count=0;
    assert(menu_quit_probe_run(&in,text,length,&out)==0);
    assert(out.status==PORTABLE_MENU_QUIT_EXIT_REQUESTED);
    assert(out.event_count==1 && out.events[0].kind==17);
    puts("menu_quit_model=PASS"); return 0;
}
