/* A host-boundary test fixture, not a game or a substitute for game startup. */
#include "platform/host.h"
#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int next_event(Host *host, HostEvent *event)
{
    int i,result;
    for(i=0;i<100;i++) {
        result=host_poll_event(host,event);
        if(result!=0) return result;
        host_wait_ms(1);
    }
    return 0;
}

int main(int argc, char **argv)
{
    Host *host;
    HostPalette palette;
    uint8_t *pixels;
    uint64_t start;
    int x,y,i,okay;
    SDL_Event injected;
    HostEvent translated;
    if (argc != 2) { fprintf(stderr,"usage: host-smoke output.bmp\n"); return 2; }
    for (i=0;i<16;i++) {
        palette.rgb[i][0]=(uint8_t)(i*17);
        palette.rgb[i][1]=(uint8_t)((15-i)*17);
        palette.rgb[i][2]=(uint8_t)((i&3)*85);
    }
    pixels=malloc(HOST_LOGICAL_WIDTH*HOST_LOGICAL_HEIGHT);
    if (!pixels) return 2;
    for (y=0;y<HOST_LOGICAL_HEIGHT;y++) for(x=0;x<HOST_LOGICAL_WIDTH;x++)
        pixels[y*HOST_LOGICAL_WIDTH+x]=(uint8_t)(((x/40)^(y/35))&15);
    host=host_create("SimAnt SDL3 host boundary test",1);
    if (!host) { fprintf(stderr,"%s\n",host_error()); free(pixels); return 1; }
    start=host_time_ns();
    /* Drain OS startup events, then verify the logical input adapter using
     * SDL's real event queue. Native keys must retain DOS scan/ASCII semantics. */
    while (host_poll_event(host,&translated)>0) {}
    memset(&injected,0,sizeof(injected));
    injected.type=SDL_EVENT_KEY_DOWN;
    injected.key.key=SDLK_A;
    injected.key.mod=SDL_KMOD_LSHIFT;
    if (!SDL_PushEvent(&injected) || next_event(host,&translated)!=1 ||
        translated.kind!=HOST_EVENT_KEY_DOWN || translated.key!=0x1e41 ||
        translated.modifiers!=2) { fprintf(stderr,"keyboard translation failed\n");
        host_destroy(host); free(pixels); return 1; }
    memset(&injected,0,sizeof(injected));
    injected.type=SDL_EVENT_QUIT;
    if (!SDL_PushEvent(&injected) || next_event(host,&translated)!=1 ||
        translated.kind!=HOST_EVENT_QUIT) { fprintf(stderr,"quit translation failed\n");
        host_destroy(host); free(pixels); return 1; }
    okay=host_present(host,pixels,HOST_LOGICAL_WIDTH,&palette) &&
         host_save_frame(host,argv[1]);
    host_wait_ms(20);
    if (host_time_ns() <= start) okay=0;
    if (!okay) fprintf(stderr,"%s\n",host_error());
    host_destroy(host);
    free(pixels);
    return okay ? 0:1;
}
