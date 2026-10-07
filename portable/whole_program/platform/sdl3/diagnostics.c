/* Windows crash reporting follows Stunts' prestarted writer-thread design.
 * The fault handler copies context and signals; it never enters SDL or game code. */
#include "diagnostics.h"
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <stdarg.h>
#include <windows.h>
#include <dbghelp.h>

#ifndef SIMANT_BUILD_REVISION
#define SIMANT_BUILD_REVISION "standalone-diagnostics-probe"
#endif
#define PATH_CAP 2048
#define RECENT 200
#define LINE_CAP 192

typedef BOOL (WINAPI *DumpWriter)(HANDLE,DWORD,HANDLE,MINIDUMP_TYPE,
    PMINIDUMP_EXCEPTION_INFORMATION,PMINIDUMP_USER_STREAM_INFORMATION,
    PMINIDUMP_CALLBACK_INFORMATION);
/* DbgHelp is deliberately loaded by absolute system path, never from the game. */
static HMODULE dbghelp;
static DumpWriter dump_writer;
static BOOL (WINAPI *sym_init)(HANDLE,PCSTR,BOOL);
static BOOL (WINAPI *sym_cleanup)(HANDLE);
static DWORD (WINAPI *sym_options)(DWORD);
static BOOL (WINAPI *stack_walk)(DWORD,HANDLE,HANDLE,LPSTACKFRAME64,PVOID,
    PREAD_PROCESS_MEMORY_ROUTINE64,PFUNCTION_TABLE_ACCESS_ROUTINE64,
    PGET_MODULE_BASE_ROUTINE64,PTRANSLATE_ADDRESS_ROUTINE64);
static BOOL (WINAPI *sym_address)(HANDLE,DWORD64,PDWORD64,PSYMBOL_INFO);
static BOOL (WINAPI *sym_line)(HANDLE,DWORD64,PDWORD,PIMAGEHLP_LINE64);
static PFUNCTION_TABLE_ACCESS_ROUTINE64 sym_table;
static PGET_MODULE_BASE_ROUTINE64 sym_base;
static int symbols_ready;
static char directory[PATH_CAP], executable[PATH_CAP];
static HANDLE log_file = INVALID_HANDLE_VALUE, input_file = INVALID_HANDLE_VALUE;
static HANDLE request, done, worker;
static volatile LONG crashing, shutdown_requested;
static DWORD fault_thread;
static EXCEPTION_RECORD exception;
static CONTEXT fault_context;
static EXCEPTION_POINTERS pointers = {&exception, &fault_context};
static LPTOP_LEVEL_EXCEPTION_FILTER previous_filter;
static void (*previous_abort)(int);
static SDL_LogOutputFunction previous_log;
static void *previous_log_data;
static int debug_mode, capture_pending;
static unsigned capture_number;
static uint64_t start_ns;
/* One producer (the application input thread). Crash writer reads only published
 * slots; it never takes a lock that could have been held by the faulting thread. */
static struct { volatile LONG serial; char text[LINE_CAP]; } recent[RECENT];
static volatile LONG input_count, loop_count, replay_index, boundary_index;
static const char *const boundaries[] = {"startup", "dos_game_main", "application.idle", "replay_input"};

static void write_text(HANDLE file, const char *text)
{
    DWORD written;
    if (file != INVALID_HANDLE_VALUE)
        WriteFile(file, text, (DWORD)strlen(text), &written, NULL);
}
static void write_format(HANDLE file, const char *format, ...)
{
    char text[8192];
    va_list args;
    va_start(args, format);
    vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    write_text(file, text);
}
static int child(char *path, const char *parent, const char *name)
{
    int length = snprintf(path, PATH_CAP, "%s/%s", parent, name);
    return length >= 0 && length < PATH_CAP;
}
static HANDLE create_file(const char *name)
{
    char path[PATH_CAP];
    if (!directory[0] || !child(path, directory, name)) return INVALID_HANDLE_VALUE;
    return CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
}
void simant_diagnostics_note(const char *label, const char *value)
{
    write_format(log_file, "%s=%s\r\n", label, value ? value : "");
}
static void SDLCALL log_output(void *unused, int category, SDL_LogPriority priority,
                              const char *message)
{
    (void)unused;
    if (debug_mode) write_format(log_file, "SDL [%d/%d]: %s\r\n", category, (int)priority, message);
    if (previous_log) previous_log(previous_log_data, category, priority, message);
}
static void write_stack(HANDLE report)
{
    STACKFRAME64 frame = {0};
    CONTEXT context = fault_context;
    HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, fault_thread);
    unsigned index;
    if (!symbols_ready || !thread || !stack_walk || !sym_address || !sym_table || !sym_base) {
        write_text(report, "symbolization=unavailable\r\n");
        if (thread) CloseHandle(thread);
        return;
    }
    frame.AddrPC.Offset = context.Rip;
    frame.AddrStack.Offset = context.Rsp;
    frame.AddrFrame.Offset = context.Rbp;
    frame.AddrPC.Mode = frame.AddrStack.Mode = frame.AddrFrame.Mode = AddrModeFlat;
    write_text(report, "stack_begin\r\n");
    for (index = 0; index < 64 && frame.AddrPC.Offset; ++index) {
        union { SYMBOL_INFO info; char storage[sizeof(SYMBOL_INFO) + MAX_SYM_NAME]; } symbol = {0};
        IMAGEHLP_LINE64 line = {0};
        DWORD64 displacement = 0, prior = frame.AddrPC.Offset;
        DWORD line_displacement = 0;
        symbol.info.SizeOfStruct = sizeof(SYMBOL_INFO);
        symbol.info.MaxNameLen = MAX_SYM_NAME;
        line.SizeOfStruct = sizeof(line);
        write_format(report, "stack_%02u=0x%llx ", index, (unsigned long long)prior);
        if (sym_address(GetCurrentProcess(), prior, &displacement, &symbol.info))
            write_format(report, "%s+0x%llx", symbol.info.Name, (unsigned long long)displacement);
        else write_text(report, "symbol=unavailable");
        if (sym_line && sym_line(GetCurrentProcess(), prior, &line_displacement, &line))
            write_format(report, " source=%s:%lu", line.FileName, (unsigned long)line.LineNumber);
        write_text(report, "\r\n");
        if (!stack_walk(IMAGE_FILE_MACHINE_AMD64, GetCurrentProcess(), thread, &frame,
                &context, NULL, sym_table, sym_base, NULL)) break;
        /* The first StackWalk64 result can be the context's current PC. We
         * already emitted that frame; advance once more before the caller. */
        if (index == 0 && frame.AddrPC.Offset == prior &&
            !stack_walk(IMAGE_FILE_MACHINE_AMD64, GetCurrentProcess(), thread, &frame,
                &context, NULL, sym_table, sym_base, NULL)) break;
        if (frame.AddrPC.Offset == prior) break;
    }
    write_text(report, "stack_end\r\n");
    CloseHandle(thread);
}
static DWORD WINAPI crash_writer(void *unused)
{
    HANDLE report, dump;
    HMODULE module = NULL;
    char path[PATH_CAP], module_path[PATH_CAP] = "";
    uintptr_t address, base;
    MINIDUMP_EXCEPTION_INFORMATION info;
    BOOL dumped = FALSE;
    DWORD error = ERROR_PROC_NOT_FOUND;
    LONG count, first, i;
    (void)unused;
    WaitForSingleObject(request, INFINITE);
    if (InterlockedCompareExchange(&shutdown_requested, 0, 0)) return 0;
    address = (uintptr_t)exception.ExceptionAddress;
    GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)address, &module);
    base = (uintptr_t)module;
    if (module) GetModuleFileNameA(module, module_path, sizeof(module_path));
    report = create_file("crash.txt");
    write_format(report, "SimAnt SDL3 crash\r\nbuild_revision=%s\r\nexception_code=0x%08lx\r\n"
        "thread_id=%lu\r\nexception_address=0x%llx\r\nfaulting_module=%s\r\nmodule_offset=0x%llx\r\n"
        "replay_index=%ld\r\nmain_loop_counter=%ld\r\nlast_source_boundary=%s\r\n",
        SIMANT_BUILD_REVISION, (unsigned long)exception.ExceptionCode, (unsigned long)fault_thread,
        (unsigned long long)address, module_path, (unsigned long long)(base ? address - base : 0),
        (long)InterlockedCompareExchange(&replay_index,0,0),
        (long)InterlockedCompareExchange(&loop_count,0,0),
        boundaries[InterlockedCompareExchange(&boundary_index,0,0)]);
    if (exception.ExceptionCode == EXCEPTION_ACCESS_VIOLATION && exception.NumberParameters >= 2)
        write_format(report, "access_operation=%llu\r\naccess_address=0x%llx\r\n",
            (unsigned long long)exception.ExceptionInformation[0],
            (unsigned long long)exception.ExceptionInformation[1]);
    /* Dump first: symbolization is best effort and must not cost the dump. */
    dump = child(path,directory,"crash.dmp") ?
        CreateFileA(path,GENERIC_WRITE,FILE_SHARE_READ,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL) : INVALID_HANDLE_VALUE;
    if (dump != INVALID_HANDLE_VALUE) {
        if (dump_writer) {
            info.ThreadId = fault_thread; info.ExceptionPointers = &pointers; info.ClientPointers = FALSE;
            dumped = dump_writer(GetCurrentProcess(), GetCurrentProcessId(), dump,
                (MINIDUMP_TYPE)(MiniDumpWithIndirectlyReferencedMemory | MiniDumpWithThreadInfo), &info, NULL, NULL);
            error = dumped ? 0 : GetLastError();
        }
        CloseHandle(dump);
    } else error = GetLastError();
    write_format(report, "minidump_written=%s\r\nminidump_error=%lu\r\n", dumped ? "yes" : "no", (unsigned long)error);
    if (child(path, directory, "simant-crashed.exe"))
        write_format(report, "executable_copy=%s\r\n", CopyFileA(executable,path,TRUE) ? "yes" : "no");
    count = InterlockedCompareExchange(&input_count,0,0);
    first = count > RECENT ? count - RECENT : 0;
    write_text(report, "last_input_events_begin\r\n");
    for (i = first; i < count; ++i) {
        char text[LINE_CAP];
        LONG serial = InterlockedCompareExchange(&recent[i % RECENT].serial,0,0);
        memcpy(text, recent[i % RECENT].text, sizeof(text)); text[LINE_CAP-1] = 0;
        if (serial == i+1 && serial == InterlockedCompareExchange(&recent[i % RECENT].serial,0,0))
            write_format(report, "%s\r\n", text);
    }
    write_text(report, "last_input_events_end\r\n");
    write_stack(report);
    write_format(log_file, "exit_status=0x%08lx\r\nstop_reason=unhandled exception\r\n", (unsigned long)exception.ExceptionCode);
    if (report != INVALID_HANDLE_VALUE) { FlushFileBuffers(report); CloseHandle(report); }
    if (log_file != INVALID_HANDLE_VALUE) FlushFileBuffers(log_file);
    SetEvent(done);
    return 0;
}
static LONG WINAPI crash_filter(EXCEPTION_POINTERS *fault)
{
    if (InterlockedCompareExchange(&crashing,1,0) == 0) {
        fault_thread = GetCurrentThreadId(); exception = *fault->ExceptionRecord;
        exception.ExceptionRecord = NULL; fault_context = *fault->ContextRecord;
        SetEvent(request);
    }
    WaitForSingleObject(done, 15000);
    return EXCEPTION_EXECUTE_HANDLER;
}
static void abort_signal(int unused)
{
    (void)unused;
    RaiseException(0xE0000001u, EXCEPTION_NONCONTINUABLE, 0, NULL);
}
static int make_session(const char *root)
{
    SYSTEMTIME time;
    unsigned attempt;
    char leaf[96];
    if (!root || !root[0] || !SDL_CreateDirectory(root)) return 0;
    GetLocalTime(&time);
    for (attempt=0; attempt<100; ++attempt) {
        snprintf(leaf,sizeof(leaf),"simant-%04u%02u%02u-%02u%02u%02u-%lu",
            time.wYear,time.wMonth,time.wDay,time.wHour,time.wMinute,time.wSecond,
            (unsigned long)GetCurrentProcessId());
        if (attempt) snprintf(leaf+strlen(leaf),sizeof(leaf)-strlen(leaf),"-%u",attempt);
        if (!child(directory,root,leaf)) return 0;
        if (CreateDirectoryA(directory,NULL)) return 1;
        if (GetLastError()!=ERROR_ALREADY_EXISTS) break;
    }
    directory[0]=0;
    return 0;
}
void simant_diagnostics_init(int debug, const char *root_override)
{
    char path[PATH_CAP], root[PATH_CAP], system[MAX_PATH];
    const char *base = SDL_GetBasePath();
    char *pref;
    debug_mode = debug;
    if (root_override) {
        if (!make_session(root_override)) goto unavailable;
    } else if (!base || !child(root,base,"diagnostics") || !make_session(root)) {
        pref = SDL_GetPrefPath("SimAnt","SDL3");
        if (!pref || !make_session(pref)) { SDL_free(pref); goto unavailable; }
        SDL_free(pref);
    }
    GetModuleFileNameA(NULL,executable,sizeof(executable));
    log_file = create_file("session.log");
    write_format(log_file,"SimAnt SDL3 diagnostics\r\nbuild_revision=%s\r\ncommand_line=%s\r\nexecutable=%s\r\ndebug=%d\r\n",
        SIMANT_BUILD_REVISION,GetCommandLineA(),executable,debug);
    /* The final executable's hash cannot be embedded into itself. The builder
     * freezes it in this adjacent identity receipt after linking, without patching. */
    if (base && child(path,base,"simant-build-id.txt")) {
        FILE *file = fopen(path,"r");
        char line[256];
        if (file) { while (fgets(line,sizeof(line),file)) write_text(log_file,line); fclose(file); }
        else write_text(log_file,"executable_sha256=unavailable\r\n");
    }
    fprintf(stderr,"SimAnt diagnostics: %s\n",directory);
    if (debug) {
        input_file=create_file("input.txt");
        write_text(input_file,"# SimAnt SDL3 input replay; use the seed in session.log\r\n");
        if (child(path,directory,"debug.log") && freopen(path,"ab",stderr)) setvbuf(stderr,NULL,_IONBF,0);
        SDL_GetLogOutputFunction(&previous_log,&previous_log_data);
        SDL_SetLogOutputFunction(log_output,NULL);
    }
    if (GetSystemDirectoryA(system,sizeof(system)) && child(path,system,"dbghelp.dll")) dbghelp=LoadLibraryA(path);
#define LOAD(name, export_name) do { FARPROC p = dbghelp ? GetProcAddress(dbghelp,export_name) : NULL; \
    _Static_assert(sizeof(name)==sizeof(p),"Windows function ABI"); memcpy(&name,&p,sizeof(name)); } while(0)
    LOAD(dump_writer,"MiniDumpWriteDump"); LOAD(sym_init,"SymInitialize"); LOAD(sym_cleanup,"SymCleanup");
    LOAD(sym_options,"SymSetOptions"); LOAD(stack_walk,"StackWalk64"); LOAD(sym_address,"SymFromAddr");
    LOAD(sym_line,"SymGetLineFromAddr64"); LOAD(sym_table,"SymFunctionTableAccess64"); LOAD(sym_base,"SymGetModuleBase64");
#undef LOAD
    if (sym_options) sym_options(SYMOPT_LOAD_LINES | SYMOPT_UNDNAME | SYMOPT_FAIL_CRITICAL_ERRORS);
    if (sym_init) symbols_ready=sym_init(GetCurrentProcess(),NULL,TRUE);
    write_format(log_file,"symbolization_ready=%d\r\n",symbols_ready);
    request=CreateEventA(NULL,FALSE,FALSE,NULL); done=CreateEventA(NULL,TRUE,FALSE,NULL);
    if (request && done) worker=CreateThread(NULL,0,crash_writer,NULL,0,NULL);
    if (worker) { previous_filter=SetUnhandledExceptionFilter(crash_filter); previous_abort=signal(SIGABRT,abort_signal); }
    else write_text(log_file,"Crash writer unavailable\r\n");
    return;
unavailable:
    directory[0]=0;
    fprintf(stderr,"SimAnt diagnostics directory could not be created: %s\n",SDL_GetError());
}
void simant_diagnostics_launch(const char *assets, uint32_t seed)
{
    char path[PATH_CAP], full[PATH_CAP], data[1024];
    FILE *file;
    size_t amount;
    {
        DWORD length=GetFullPathNameA(assets,sizeof(full),full,NULL);
        if (!length || length>=sizeof(full)) snprintf(full,sizeof(full),"%s",assets);
    }
    write_format(log_file,"assets_dir=%s\r\nseed=%u\r\n",full,(unsigned)seed);
    if (!child(path,full,"SIMANT.CFG")) return;
    write_text(log_file,"SIMANT.CFG contents begin\r\n");
    file=fopen(path,"rb");
    if (file) {
        while ((amount=fread(data,1,sizeof(data),file))!=0) { DWORD written; if (log_file!=INVALID_HANDLE_VALUE) WriteFile(log_file,data,(DWORD)amount,&written,NULL); }
        fclose(file);
    } else write_text(log_file,"unavailable");
    write_text(log_file,"\r\nSIMANT.CFG contents end\r\n");
}
void simant_diagnostics_progress(const char *boundary, size_t replay, long loops)
{
    unsigned i;
    InterlockedExchange(&loop_count,(LONG)loops); InterlockedExchange(&replay_index,(LONG)replay);
    for (i=0;i<sizeof(boundaries)/sizeof(boundaries[0]);++i)
        if (!strcmp(boundary,boundaries[i])) { InterlockedExchange(&boundary_index,(LONG)i); break; }
}
void simant_diagnostics_start(uint64_t now) { start_ns=now; }
int simant_diagnostics_event(void *unused, const SDL_Event *event)
{
    char line[LINE_CAP] = "";
    uint64_t now=host_time_ns(), ms=now>=start_ns ? (now-start_ns)/1000000u : 0;
    LONG sequence;
    int scripted=event->common.timestamp==HOST_REPLAY_EVENT_TIMESTAMP;
    const char *name;
    (void)unused;
    if (event->type==SDL_EVENT_KEY_DOWN || event->type==SDL_EVENT_KEY_UP) {
        name=SDL_GetKeyName(event->key.key);
        if (name && name[0]) snprintf(line,sizeof(line),"%llu %s %s",(unsigned long long)ms,
            event->type==SDL_EVENT_KEY_DOWN ? "down":"up",name);
        else snprintf(line,sizeof(line),"# %llu ignored key scancode %u",(unsigned long long)ms,(unsigned)event->key.scancode);
    } else if (event->type==SDL_EVENT_MOUSE_MOTION) {
        snprintf(line,sizeof(line),"%llu move %d %d",(unsigned long long)ms,(int)event->motion.x,(int)event->motion.y);
    } else if (event->type==SDL_EVENT_MOUSE_BUTTON_DOWN || event->type==SDL_EVENT_MOUSE_BUTTON_UP) {
        name=event->button.button==SDL_BUTTON_LEFT ? "Left" : event->button.button==SDL_BUTTON_RIGHT ? "Right" :
            event->button.button==SDL_BUTTON_MIDDLE ? "Middle" : NULL;
        if (name) snprintf(line,sizeof(line),"%llu mouse-%s %s %d %d",(unsigned long long)ms,
            event->type==SDL_EVENT_MOUSE_BUTTON_DOWN ? "down":"up",name,(int)event->button.x,(int)event->button.y);
        else snprintf(line,sizeof(line),"# %llu ignored mouse button %u",(unsigned long long)ms,event->button.button);
    } else if (event->type==SDL_EVENT_MOUSE_WHEEL)
        snprintf(line,sizeof(line),"# %llu ignored mouse wheel %.3f %.3f",(unsigned long long)ms,(double)event->wheel.x,(double)event->wheel.y);
    else if (event->type==SDL_EVENT_QUIT)
        snprintf(line,sizeof(line),"%llu exit",(unsigned long long)ms);
    if (line[0]) {
        sequence=InterlockedCompareExchange(&input_count,0,0);
        InterlockedExchange(&recent[sequence%RECENT].serial,0);
        snprintf(recent[sequence%RECENT].text,LINE_CAP,"%s",line);
        InterlockedExchange(&recent[sequence%RECENT].serial,sequence+1);
        InterlockedExchange(&input_count,sequence+1);
        if (debug_mode && !scripted) write_format(input_file,"%s\r\n",line);
    }
    if (debug_mode && (event->type==SDL_EVENT_KEY_DOWN || event->type==SDL_EVENT_KEY_UP) && event->key.key==SDLK_F12) {
        if (event->type==SDL_EVENT_KEY_DOWN && !event->key.repeat) capture_pending=1;
        return 1;
    }
    return 0;
}
void simant_diagnostics_capture(Host *host, long loops)
{
    char folder[PATH_CAP], path[PATH_CAP], leaf[64];
    HostPalette palette;
    int width,height,okay=0;
    FILE *file;
    unsigned i;
    if (!capture_pending || !directory[0]) return;
    capture_pending=0;
    if (!host_get_logical_size(host,&width,&height) || !host_presented_palette(host,&palette)) return;
    snprintf(leaf,sizeof(leaf),"capture-%04u",++capture_number);
    if (!child(folder,directory,leaf) || !CreateDirectoryA(folder,NULL)) return;
    if (child(path,folder,"screenshot.bmp")) okay=host_save_frame(host,path);
    if (child(path,folder,"palette.txt") && (file=fopen(path,"w"))) {
        fputs("# index red green blue (RGB8, palette of the saved presented frame)\n",file);
        for (i=0;i<16;++i) fprintf(file,"%u %u %u %u\n",i,palette.rgb[i][0],palette.rgb[i][1],palette.rgb[i][2]);
        fclose(file);
    }
    if (child(path,folder,"frame.txt") && (file=fopen(path,"w"))) {
        fprintf(file,"width=%d\nheight=%d\nmain_loop_counter=%ld\nreplay_index=%ld\n",width,height,loops,(long)replay_index);
        fclose(file);
    }
    write_format(log_file,"capture=%s screenshot_written=%d main_loop_counter=%ld\r\n",folder,okay,loops);
}
void simant_diagnostics_close(int status, const char *reason)
{
    write_format(log_file,"exit_status=%d\r\nstop_reason=%s\r\n",status,reason);
    if (debug_mode && directory[0]) SDL_SetLogOutputFunction(previous_log,previous_log_data);
    if (worker) {
        SetUnhandledExceptionFilter(previous_filter); signal(SIGABRT,previous_abort);
        InterlockedExchange(&shutdown_requested,1); SetEvent(request);
        WaitForSingleObject(worker,INFINITE); CloseHandle(worker); worker=NULL;
    }
    if (request) CloseHandle(request);
    if (done) CloseHandle(done);
    if (symbols_ready && sym_cleanup) sym_cleanup(GetCurrentProcess());
    if (dbghelp) FreeLibrary(dbghelp);
    if (input_file!=INVALID_HANDLE_VALUE) { FlushFileBuffers(input_file); CloseHandle(input_file); input_file=INVALID_HANDLE_VALUE; }
    if (log_file!=INVALID_HANDLE_VALUE) { FlushFileBuffers(log_file); CloseHandle(log_file); log_file=INVALID_HANDLE_VALUE; }
}
__declspec(dllexport) __attribute__((noinline)) void simant_diagnostics_test_crash(void)
{
    /* Only the explicit child-process test switch calls this deliberate fault. */
    volatile unsigned *address=NULL;
    write_format(log_file,"test_fault_thread=%lu\r\n",(unsigned long)GetCurrentThreadId());
    *address=0x51a17;
}
static DWORD WINAPI test_fault_thread(void *unused)
{
    (void)unused;
    simant_diagnostics_test_crash();
    return 0;
}
void simant_diagnostics_test_thread_crash(void)
{
    HANDLE thread=CreateThread(NULL,0,test_fault_thread,NULL,0,NULL);
    if (thread) { WaitForSingleObject(thread,INFINITE); CloseHandle(thread); }
}
