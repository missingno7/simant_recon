#include "platform/host.h"
#include "render/palette.h"
#include "ui_model/windows/render.h"
#include "ui_model/windows/registry.h"
#include "ui_model/windows/titles.h"
#include "game/resources/fonts.h"
#include "game/resources/bios_fonts.h"
#include "game/session.h"
#include "ui_model/windows/game_view.h"
#ifdef SIMANT_ENABLE_RECOVERED_CORE
#include "platform/sdl3/live_game.h"
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Development integration modes execute actual resources and NewGame. An
 * explicit recovered-core build additionally runs the source simulation;
 * unsupported host services stop with a named diagnostic. */
static int start_game_view(SimSession *session,PortableWindowRegistry *registry,
                          PortableWindowRenderer *renderer,int scenario,
                          const PortableWindowTitlesStringSet *titles,
                          PortableWindowTitleProjection *title_projection)
{
    PortableFramebuffer *framebuffer=renderer->framebuffer;
    const SimNewGameConfig config={(int16_t)scenario,0,11,8};
    PortableGameViewState state;
    PortableGameView view;
    PortableGameViewRenderResult rendered;
    SimSessionStatus started=sim_session_new_game(session,&config);
    PortableGameViewStatus status;
    if(started!=SIM_SESSION_OK) {
        fprintf(stderr,"NewGame: %s\n",sim_session_status_string(started));return 0;
    }
    {
        const PortableWindowTitleScene scene={session->world.scenario,
            session->world.selected_map_plane,session->world.yard_mode,1,1,0};
        PortableWindowTitlesStatus title_status=
            portable_window_titles_update(titles,&scene,title_projection);
        if(title_status!=PORTABLE_WINDOW_TITLES_OK) {
            fprintf(stderr,"window titles: %s\n",
                    portable_window_titles_status_string(title_status));return 0;
        }
        renderer->resolve_text=portable_window_titles_resolve_text;
        renderer->text_context=title_projection;
    }
    if(portable_window_registry_recalculate(registry,0,NULL)!=PORTABLE_WINDOW_REGISTRY_OK) {
        fprintf(stderr,"edit window geometry unavailable\n");return 0;
    }
    state.ega_profile=registry->profile_id;
    state.pheromone_mode=session->world.source_state_07be;
    state.animation_base=session->world.source_state_049a;
    state.queen_frame=session->world.me_direction;
    /* Cold-start 50F6:0502 is zero. NewGame selects caste 0x10, so the
     * source renderer uses direction rather than this young-caste field. */
    state.young_frame=0;
    state.caste_frame=session->world.me_type;
    status=portable_game_view_resolve(registry,&session->world,&state,&view);
    if(status==PORTABLE_GAME_VIEW_OK) {
        /* SetDefaultWindows ends with CenterEdit after loading the viewport.
         * Persist that source camera before constructing the live core. */
        session->world.map_view_x=view.map.camera_x;
        session->world.map_view_y=view.map.camera_y;
        /* SetDefaultWindows opens caste, mode and map before the edit window.
         * These resource frames are static until their live controls are wired. */
        const int frame_windows[]={19,18,1,0};
        size_t frame_index;
        memset(framebuffer->pixels,0,(size_t)framebuffer->stride*framebuffer->height);
        for(frame_index=0;frame_index<sizeof(frame_windows)/sizeof(frame_windows[0]);frame_index++) {
            int window_id=frame_windows[frame_index];
            if(portable_window_registry_recalculate(registry,(int16_t)window_id,NULL)!=
               PORTABLE_WINDOW_REGISTRY_OK ||
               portable_window_draw_native(&registry->slots[window_id].window,renderer)!=
               PORTABLE_RENDER_OK) {
                fprintf(stderr,"window %d rendering unavailable\n",window_id);return 0;
            }
        }
        status=portable_game_view_render(&session->world,&view,&session->tileset,
                                        framebuffer,&rendered);
    }
    if(status!=PORTABLE_GAME_VIEW_OK) {
        fprintf(stderr,"game viewport: %s\n",portable_game_view_status_string(status));return 0;
    }
    printf("Native NewGame scenario=%d player=(%d,%d) plane=%d camera=(%d,%d) cells=%zu life=%zu\n",
           scenario,session->world.me_x,session->world.me_y,view.map.plane,
           view.map.camera_x,view.map.camera_y,rendered.cells_drawn,rendered.cells_with_life);
    fflush(stdout);
    return 1;
}

int main(int argc,char **argv)
{
    const char *asset_dir="assets",*screenshot=NULL,*bios_directory=NULL;
    unsigned frame_limit=0,frames=0;
    unsigned long tick_limit=0;
    int i,scene_mode=0,quit=0,result=1;
    int live_mode=0;
    uint64_t next_presentation=0;
#ifdef SIMANT_ENABLE_RECOVERED_CORE
    PortableLiveGame *live=NULL;
#endif
    char path[1024],ndx[1024],dat[1024];
    Host *host=NULL;
    PortableDatabase db={0};
    PortableDbRecord colors={0},palette_record={0};
    PortableWindowRegistry registry={0};
    PortableWindowResource *window=NULL;
    PortableFramebuffer framebuffer;
    PortablePalette palette;
    HostPalette host_palette;
    PortableWindowRenderer renderer={0};
    PortableFontSet fonts;
    PortableBiosFonts bios_fonts={0};
    PortableWindowTitlesStringSet titles={0};
    PortableWindowTitleProjection title_projection={0};
    SimSession *session=NULL;
    uint8_t *pixels=NULL;
    portable_fonts_init(&fonts);
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--scenario-screen")) scene_mode=1;
        else if(!strcmp(argv[i],"--newgame-view")) scene_mode=2;
        else if(!strcmp(argv[i],"--live-game")) {scene_mode=1;live_mode=1;}
        else if(!strcmp(argv[i],"--live-newgame")) {scene_mode=2;live_mode=1;}
        else if(!strcmp(argv[i],"--assets") && i+1<argc) asset_dir=argv[++i];
        else if(!strcmp(argv[i],"--bios-reference") && i+1<argc) bios_directory=argv[++i];
        else if(!strcmp(argv[i],"--screenshot") && i+1<argc) screenshot=argv[++i];
        else if(!strcmp(argv[i],"--frames") && i+1<argc) {
            char *end; unsigned long parsed=strtoul(argv[++i],&end,10);
            if(*end || parsed>1000000) {fprintf(stderr,"invalid frame limit\n");return 2;}
            frame_limit=(unsigned)parsed;
        } else if(!strcmp(argv[i],"--ticks") && i+1<argc) {
            char *end;tick_limit=strtoul(argv[++i],&end,10);
            if(*end || !tick_limit || tick_limit>1000000) {
                fprintf(stderr,"invalid tick limit\n");return 2;
            }
        } else {fprintf(stderr,"usage: simant-sdl3 (--scenario-screen | --newgame-view | --live-game | --live-newgame) [--assets dir] [--bios-reference dir] [--frames N] [--ticks N] [--screenshot file.bmp]\n");return 2;}
    }
#ifdef SIMANT_ENABLE_RECOVERED_CORE
    if(!scene_mode) {scene_mode=1;live_mode=1;}
#else
    if(live_mode || tick_limit) {
        fprintf(stderr,"Live core requires an explicit --core-profile build.\n");return 2;
    }
#endif
    if(tick_limit && !live_mode) {
        fprintf(stderr,"--ticks requires a live game mode.\n");return 2;
    }
    if(!scene_mode) {
        fprintf(stderr,"The full native game loop is still being integrated. Use --scenario-screen or --newgame-view to exercise resource-backed startup and world presentation.\n");
        return 2;
    }
    if(snprintf(ndx,sizeof(ndx),"%s/HCEGANT.NDX",asset_dir)>=(int)sizeof(ndx) ||
       snprintf(dat,sizeof(dat),"%s/HCEGANT.DAT",asset_dir)>=(int)sizeof(dat)) return 2;
    if(portable_db_open_files(&db,ndx,dat)!=PORTABLE_DB_OK) {
        fprintf(stderr,"resource open failed: %s\n",portable_db_error(&db));goto done;
    }
    if(portable_window_registry_init(&registry,&db,0)!=PORTABLE_WINDOW_REGISTRY_OK ||
       portable_window_registry_load(&registry,2)!=PORTABLE_WINDOW_REGISTRY_OK ||
       portable_db_load(&db,0x81,0,&colors)!=PORTABLE_DB_OK ||
       portable_db_load(&db,1,15,&palette_record)!=PORTABLE_DB_OK) {
        fprintf(stderr,"required original scenario resources unavailable\n");goto done;
    }
    window=&registry.slots[2].window;
    if(portable_window_registry_recalculate(&registry,2,NULL)!=PORTABLE_WINDOW_REGISTRY_OK ||
       portable_palette_load_ega(&palette,palette_record.data,palette_record.size)!=PORTABLE_RENDER_OK) {
        fprintf(stderr,"scenario resource decode failed\n");goto done;
    }
    memcpy(host_palette.rgb,palette.rgb,sizeof(host_palette.rgb));
    pixels=calloc(HOST_LOGICAL_WIDTH*HOST_LOGICAL_HEIGHT,1);
    if(!pixels || portable_framebuffer_init(&framebuffer,HOST_LOGICAL_WIDTH,
               HOST_LOGICAL_HEIGHT,HOST_LOGICAL_WIDTH,pixels)!=PORTABLE_RENDER_OK) goto done;
    renderer.framebuffer=&framebuffer;renderer.database=&db;
    renderer.colors=colors.data;renderer.colors_size=colors.size;
    renderer.screen_width=HOST_LOGICAL_WIDTH;
    renderer.hardware_profile=0;
    if(portable_fonts_load(&fonts,asset_dir)!=PORTABLE_RENDER_OK) {
        fprintf(stderr,"font resources: %s\n",fonts.error);goto done;
    }
    for(i=0;i<4;i++) renderer.fonts[i]=portable_fonts_get(&fonts,(unsigned)i+2);
    if(portable_bios_fonts_load(&bios_fonts,bios_directory)!=PORTABLE_BIOS_FONTS_OK) {
        fprintf(stderr,"BIOS reference fonts: %s. Run python portable/tests/windows/render/evidence/fetch_bios_reference.py\n",
                portable_bios_fonts_error(&bios_fonts));goto done;
    }
    renderer.bios_fonts=&bios_fonts.provider;
    session=calloc(1,sizeof(*session));
    if(!session || sim_session_init(session,asset_dir,&db,&registry)!=SIM_SESSION_OK ||
       sim_session_seed_startup(session,0x12345678u,0x87654321u)!=SIM_SESSION_OK) {
        fprintf(stderr,"native session startup failed\n");goto done;
    }
    if(portable_window_titles_load(&titles,&session->shared_database)!=
       PORTABLE_WINDOW_TITLES_OK) {
        fprintf(stderr,"required window title resources unavailable\n");goto done;
    }
    /* Fixed logical startup samples make these development modes reproducible.
     * Production timing and gameplay are connected separately. */
    if(scene_mode==2) {
        if(!start_game_view(session,&registry,&renderer,1,&titles,&title_projection)) goto done;
    } else if(portable_window_draw_native(window,&renderer)!=PORTABLE_RENDER_OK) {
        fprintf(stderr,"scenario raster path is not yet fully supported\n");goto done;
    }
    host=host_create("SimAnt — native integration",0);
    if(!host) {fprintf(stderr,"SDL3: %s\n",host_error());goto done;}
#ifdef SIMANT_ENABLE_RECOVERED_CORE
    if(live_mode && scene_mode==2) {
        live=portable_live_game_create(session,&registry,&renderer,&fonts,
            &titles,&title_projection,host,&host_palette,&palette);
        if(!live) {fprintf(stderr,"Live core initialization failed\n");goto done;}
    }
#endif
    while(!quit) {
        HostEvent event;
        int polled;
        while((polled=host_poll_event(host,&event))>0) {
            if(event.kind==HOST_EVENT_QUIT || (!live_mode &&
               (event.kind==HOST_EVENT_KEY_DOWN && (event.key&255)==27))) quit=1;
#ifdef SIMANT_ENABLE_RECOVERED_CORE
            if(live && !portable_live_game_event(live,&event)) {
                fprintf(stderr,"live input: %s\n",portable_live_game_error(live));goto done;
            }
#endif
            if(scene_mode==1 && event.kind==HOST_EVENT_MOUSE_UP && event.button==1) {
                int hit=portable_window_hit_test(window,(PortableWindowPoint){event.x,event.y});
                if(hit>=2) {
                    int scenario=-1;
                    int code=0x200+hit;
                    PortableScenarioAction action=portable_newgame_scenario_action(code,&scenario);
                    printf("scenario event=%04x action=%d source_id=%d\n",code,(int)action,scenario);
                    fflush(stdout);
                    if(action==PORTABLE_SCENARIO_CANCEL) quit=1;
                    else if(action==PORTABLE_SCENARIO_CONFIRM_TRANSFER) {
                        fprintf(stderr,"Restore game integration is pending.\n");
                    } else if(scenario>=0 && scenario<=3) {
                        if(!start_game_view(session,&registry,&renderer,scenario,
                                            &titles,&title_projection)) goto done;
                        scene_mode=2;
#ifdef SIMANT_ENABLE_RECOVERED_CORE
                        if(live_mode) {
                            live=portable_live_game_create(session,&registry,&renderer,&fonts,
                                &titles,&title_projection,host,&host_palette,&palette);
                            if(!live) {fprintf(stderr,"Live core initialization failed\n");goto done;}
                        }
#endif
                    }
                }
            }
        }
        if(polled<0) {fprintf(stderr,"SDL3: %s\n",host_error());goto done;}
#ifdef SIMANT_ENABLE_RECOVERED_CORE
        if(live && !quit) {
            if(!portable_live_game_update(live,host_time_ns())) {
                fprintf(stderr,"live core: %s\n",portable_live_game_error(live));goto done;
            }
            if(portable_live_game_quit_requested(live)) quit=1;
            if(tick_limit && portable_live_game_completed_ticks(live)>=tick_limit) quit=1;
        }
#endif
        if(!quit && host_time_ns()<next_presentation) {
            if(!live_mode) host_wait_ms(1);
            continue;
        }
        if(!host_present(host,pixels,HOST_LOGICAL_WIDTH,&host_palette)) {
            fprintf(stderr,"SDL3: %s\n",host_error());goto done;
        }
        frames++;
        next_presentation=host_time_ns()+UINT64_C(16000000);
        if(frame_limit && frames>=frame_limit) quit=1;
        if(!quit && !live_mode) host_wait_ms(1);
    }
    if(screenshot) {
        if(snprintf(path,sizeof(path),"%s",screenshot)>=(int)sizeof(path) ||
           !host_save_frame(host,path)) {fprintf(stderr,"screenshot failed\n");goto done;}
    }
    result=0;
done:
#ifdef SIMANT_ENABLE_RECOVERED_CORE
    if(live) printf("Completed native simulation ticks: %llu\n",
                   (unsigned long long)portable_live_game_completed_ticks(live));
    portable_live_game_destroy(live);
#endif
    host_destroy(host);
    free(pixels);
    portable_fonts_destroy(&fonts);
    portable_bios_fonts_free(&bios_fonts);
    portable_window_titles_free(&titles);
    sim_session_close(session);
    free(session);
    portable_window_registry_destroy(&registry);
    portable_db_record_free(&colors);
    portable_db_record_free(&palette_record);
    portable_db_close(&db);
    return result;
}
