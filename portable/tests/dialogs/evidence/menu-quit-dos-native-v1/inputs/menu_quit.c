#include "menu_quit.h"

#define MENU_QUIT_WINDOW 0x2100
#define MENU_QUIT_TEXT_OBJECT 0x2101
#define MENU_QUIT_RESOURCE_KIND 10
#define MENU_QUIT_RESOURCE_TYPE 1

static const char menu_quit_notice[] =
    "SimAnt was brought to you by the people at MAXIS.  Thank you for playing.";

static PortableMenuQuitStatus service_result(int supported, int accepted)
{
    if (!supported)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    return accepted ? PORTABLE_MENU_QUIT_EXIT_REQUESTED
                    : PORTABLE_MENU_QUIT_HOST_REJECTED;
}

static int translate_key(int16_t code, PortableMenuQuitChoice *choice)
{
    switch ((uint16_t)code) {
    case 0x0d: case 'D': case 'd': *choice = PORTABLE_MENU_QUIT_DISCARD; return 1;
    case 'S': case 's': *choice = PORTABLE_MENU_QUIT_SAVE; return 1;
    case 0x1b: case 'C': case 'c': *choice = PORTABLE_MENU_QUIT_CANCEL; return 1;
    default: return 0;
    }
}

static int translate_event(int16_t code, PortableMenuQuitChoice *choice)
{
    switch ((uint16_t)code) {
    case 0x2103: *choice = PORTABLE_MENU_QUIT_DISCARD; return 1;
    case 0x2104: *choice = PORTABLE_MENU_QUIT_SAVE; return 1;
    case 0x2105: *choice = PORTABLE_MENU_QUIT_CANCEL; return 1;
    default: return 0;
    }
}

static PortableMenuQuitStatus checked(int supported, int accepted)
{
    return service_result(supported, accepted);
}

PortableMenuQuitStatus portable_menu_quit_prompt(
    const PortableMenuQuitHost *host, int16_t which,
    const PortableMenuQuitInput *input, PortableMenuQuitChoice *choice)
{
    uintptr_t handle = 0;
    const char *text = NULL;
    size_t text_length = 0;
    PortableMenuQuitRect rect;
    PortableMenuQuitStatus status;
    uint32_t poll;
    int ready, available;
    int16_t code;
    int16_t resource_object;

    if (host == NULL || input == NULL || choice == NULL || which < 0 ||
        input->max_input_polls == 0)
        return PORTABLE_MENU_QUIT_BAD_ARGUMENT;
    if ((status = checked(host->open_window != NULL,
            host->open_window ? host->open_window(host->context, MENU_QUIT_WINDOW) : 0)) != PORTABLE_MENU_QUIT_EXIT_REQUESTED)
        return status;

    resource_object = (int16_t)((0x41 - which) * 2);
    if (!host->load_resource)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    if (!host->load_resource(host->context, resource_object, MENU_QUIT_RESOURCE_KIND,
                             MENU_QUIT_RESOURCE_TYPE, &handle) || handle == 0)
        return PORTABLE_MENU_QUIT_HOST_REJECTED;
    if (!host->lock_resource)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    if (!host->lock_resource(host->context, handle, &text, &text_length) ||
        text == NULL || text_length == 0)
        return PORTABLE_MENU_QUIT_HOST_REJECTED;

    if (!host->set_font)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    if (!host->set_font(host->context,
                        input->screen_width_metric == 0x140 ? 2 : 4))
        return PORTABLE_MENU_QUIT_HOST_REJECTED;

    if (input->frame_enabled) {
        if (!host->get_object_rect || !host->decorate_rect || !host->frame_rect)
            return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
        if (!host->get_object_rect(host->context, MENU_QUIT_WINDOW, &rect) ||
            !host->decorate_rect(host->context, 0, 0, 0) ||
            !host->frame_rect(host->context, &rect, 2))
            return PORTABLE_MENU_QUIT_HOST_REJECTED;
    }
    if (!host->get_object_rect || !host->set_color_from_object || !host->print_text)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    if (!host->get_object_rect(host->context, MENU_QUIT_TEXT_OBJECT, &rect) ||
        !host->set_color_from_object(host->context, MENU_QUIT_TEXT_OBJECT) ||
        !host->print_text(host->context, 0, text, &rect) ||
        !host->set_font(host->context, 0))
        return PORTABLE_MENU_QUIT_HOST_REJECTED;

    if (!host->key_ready || !host->read_key || !host->get_event)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    for (poll = 0; poll < input->max_input_polls; ++poll) {
        if (!host->key_ready(host->context, &ready))
            return PORTABLE_MENU_QUIT_HOST_REJECTED;
        if (ready) {
            if (!host->read_key(host->context, &code))
                return PORTABLE_MENU_QUIT_HOST_REJECTED;
            if (translate_key(code, choice))
                goto done;
        }
        if (!host->get_event(host->context, &available, &code))
            return PORTABLE_MENU_QUIT_HOST_REJECTED;
        if (available && translate_event(code, choice))
            goto done;
    }
    /* The source stays in its poll loop and retains the open resource until a
     * recognized key or window event arrives. The host must keep polling. */
    return PORTABLE_MENU_QUIT_INPUT_PENDING;

done:
    if (!host->unlock_resource || !host->release_resource || !host->close_window)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    if (!host->unlock_resource(host->context, handle) ||
        !host->release_resource(host->context, handle) ||
        !host->close_window(host->context, MENU_QUIT_WINDOW))
        return PORTABLE_MENU_QUIT_HOST_REJECTED;
    return PORTABLE_MENU_QUIT_EXIT_REQUESTED;
}

PortableMenuQuitStatus portable_menu_quit_run(
    const PortableMenuQuitHost *host, const PortableMenuQuitInput *input)
{
    PortableMenuQuitChoice choice;
    PortableMenuQuitStatus status;
    int saved;

    if (host == NULL || input == NULL)
        return PORTABLE_MENU_QUIT_BAD_ARGUMENT;
    if (input->dirty_word != 0) {
        for (;;) {
            status = portable_menu_quit_prompt(host, 1, input, &choice);
            if (status != PORTABLE_MENU_QUIT_EXIT_REQUESTED)
                return status;
            if (choice == PORTABLE_MENU_QUIT_CANCEL)
                return PORTABLE_MENU_QUIT_CANCELLED;
            if (choice != PORTABLE_MENU_QUIT_SAVE)
                break;
            if (!host->save_game)
                return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
            saved = 0;
            if (!host->save_game(host->context, 0, &saved))
                return PORTABLE_MENU_QUIT_HOST_REJECTED;
            if (saved != 0)
                break;
        }
    }
    if (!host->exit_notice)
        return PORTABLE_MENU_QUIT_UNSUPPORTED_SERVICE;
    if (!host->exit_notice(host->context, menu_quit_notice, 0, 0))
        return PORTABLE_MENU_QUIT_HOST_REJECTED;
    return PORTABLE_MENU_QUIT_EXIT_REQUESTED;
}
