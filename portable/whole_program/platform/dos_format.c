#include "dos_format.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct DosFmtSpec {
    char flags[8];
    int width;
    int precision;
    int has_precision;
    int width_from_arg;
    int precision_from_arg;
    int long_value;
    char conversion;
} DosFmtSpec;

static int parse_spec(const char **cursor, DosFmtSpec *out)
{
    const char *p = *cursor;
    size_t flags = 0;
    memset(out, 0, sizeof(*out));
    out->precision = 0;
    while (*p == '-' || *p == '+' || *p == ' ' || *p == '#' || *p == '0') {
        if (flags + 1 >= sizeof(out->flags)) return 0;
        out->flags[flags++] = *p++;
    }
    out->flags[flags] = '\0';
    if (*p == '*') { out->width_from_arg = 1; ++p; }
    else {
        while (*p >= '0' && *p <= '9') {
            if (out->width > DOS_FORMAT_FIELD_LIMIT / 10) return 0;
            out->width = out->width * 10 + (*p++ - '0');
            if (out->width > DOS_FORMAT_FIELD_LIMIT) return 0;
        }
    }
    if (*p == '.') {
        out->has_precision = 1;
        ++p;
        if (*p == '*') { out->precision_from_arg = 1; ++p; }
        else {
            while (*p >= '0' && *p <= '9') {
                if (out->precision > DOS_FORMAT_FIELD_LIMIT / 10) return 0;
                out->precision = out->precision * 10 + (*p++ - '0');
                if (out->precision > DOS_FORMAT_FIELD_LIMIT) return 0;
            }
        }
    }
    if (*p == 'l') { out->long_value = 1; ++p; }
    if (*p == '\0') return 0;
    out->conversion = *p++;
    if (strchr("diuoxX", out->conversion)) {
        /* Both the source's 16-bit and 32-bit integer domains are supported. */
    } else if (!out->long_value && strchr("sc p", out->conversion) && out->conversion != ' ') {
        /* Host pointers are deliberately a distinct native diagnostic domain. */
    } else if (out->conversion == '%') {
        if (out->long_value || out->width_from_arg || out->precision_from_arg ||
            out->width != 0 || out->has_precision || flags != 0) return 0;
    } else {
        return 0;
    }
    if (out->long_value && !strchr("diuoxX", out->conversion)) return 0;
    *cursor = p;
    return 1;
}

static int preflight(const char *format)
{
    const char *p = format;
    if (p == NULL) return 0;
    while (*p) {
        if (*p++ != '%') continue;
        if (*p == '%') { ++p; continue; }
        DosFmtSpec spec;
        if (!parse_spec(&p, &spec)) return 0;
    }
    return 1;
}

static int emit_bytes(char *dst, size_t capacity, size_t *produced,
                      const char *bytes, size_t count)
{
    size_t i;
    if (count > SIZE_MAX - *produced) return 0;
    if (dst != NULL && capacity != 0) {
        for (i = 0; i < count && *produced + i < capacity - 1; ++i)
            dst[*produced + i] = bytes[i];
    }
    *produced += count;
    return 1;
}

static int format_field(char **result, size_t *length, const DosFmtSpec *spec,
                        const char *text, int signed_word, unsigned int unsigned_word,
                        long long signed_long, unsigned long long unsigned_long,
                        int character, const void *pointer)
{
    char native_spec[64];
    int n = 0;
    char *field;
    size_t need;
    const char *conv = &spec->conversion;

    n += snprintf(native_spec + n, sizeof(native_spec) - (size_t)n, "%%%s", spec->flags);
    if (spec->width != 0)
        n += snprintf(native_spec + n, sizeof(native_spec) - (size_t)n, "%d", spec->width);
    if (spec->has_precision)
        n += snprintf(native_spec + n, sizeof(native_spec) - (size_t)n, ".%d", spec->precision);
    if (strchr("diuoxX", *conv)) n += snprintf(native_spec + n, sizeof(native_spec) - (size_t)n, "ll%c", *conv);
    else n += snprintf(native_spec + n, sizeof(native_spec) - (size_t)n, "%c", *conv);
    if (n < 0 || (size_t)n >= sizeof(native_spec)) return 0;

    switch (*conv) {
    case 'd': case 'i':
        need = (size_t)snprintf(NULL, 0, native_spec,
                 spec->long_value ? signed_long : (long long)(int16_t)signed_word);
        field = (char *)malloc(need + 1);
        if (!field) return 0;
        (void)snprintf(field, need + 1, native_spec,
                 spec->long_value ? signed_long : (long long)(int16_t)signed_word);
        break;
    case 'u': case 'o': case 'x': case 'X':
        need = (size_t)snprintf(NULL, 0, native_spec,
                 spec->long_value ? unsigned_long : (unsigned long long)(uint16_t)unsigned_word);
        field = (char *)malloc(need + 1);
        if (!field) return 0;
        (void)snprintf(field, need + 1, native_spec,
                 spec->long_value ? unsigned_long : (unsigned long long)(uint16_t)unsigned_word);
        break;
    case 's':
        if (text == NULL) text = "(null)";
        need = (size_t)snprintf(NULL, 0, native_spec, text);
        field = (char *)malloc(need + 1);
        if (!field) return 0;
        (void)snprintf(field, need + 1, native_spec, text);
        break;
    case 'c':
        need = (size_t)snprintf(NULL, 0, native_spec, character);
        field = (char *)malloc(need + 1);
        if (!field) return 0;
        (void)snprintf(field, need + 1, native_spec, character);
        break;
    case 'p':
        need = (size_t)snprintf(NULL, 0, native_spec, pointer);
        field = (char *)malloc(need + 1);
        if (!field) return 0;
        (void)snprintf(field, need + 1, native_spec, pointer);
        break;
    default:
        return 0;
    }
    *result = field;
    *length = need;
    return 1;
}

int dos_vsnprintf(char *dst, size_t capacity, const char *format, va_list args)
{
    const char *p;
    size_t produced = 0;
    va_list ap;
    if (dst != NULL && capacity != 0) dst[0] = '\0';
    if (!preflight(format)) return -1;
    va_copy(ap, args);
    p = format;
    while (*p) {
        const char *literal = p;
        while (*p && *p != '%') ++p;
        if (!emit_bytes(dst, capacity, &produced, literal, (size_t)(p - literal))) goto failed;
        if (!*p) break;
        ++p;
        if (*p == '%') {
            if (!emit_bytes(dst, capacity, &produced, "%", 1)) goto failed;
            ++p;
            continue;
        }
        DosFmtSpec spec;
        if (!parse_spec(&p, &spec)) goto failed;
        if (spec.width_from_arg) {
            int width = (int16_t)va_arg(ap, int);
            if (width < 0) {
                if (!strchr(spec.flags, '-')) {
                    size_t n = strlen(spec.flags);
                    if (n + 1 >= sizeof(spec.flags)) goto failed;
                    spec.flags[n] = '-'; spec.flags[n + 1] = '\0';
                }
                if (width == INT16_MIN) goto failed;
                width = -width;
            }
            if (width > DOS_FORMAT_FIELD_LIMIT) goto failed;
            spec.width = width;
        }
        if (spec.precision_from_arg) {
            int precision = (int16_t)va_arg(ap, int);
            if (precision < 0) spec.has_precision = 0;
            else if (precision > DOS_FORMAT_FIELD_LIMIT) goto failed;
            else spec.precision = precision;
        }
        const char *text = NULL;
        int signed_word = 0;
        unsigned int unsigned_word = 0;
        long long signed_long = 0;
        unsigned long long unsigned_long = 0;
        int character = 0;
        const void *pointer = NULL;
        if (spec.conversion == 'd' || spec.conversion == 'i') {
            if (spec.long_value) signed_long = (long long)va_arg(ap, int32_t);
            else signed_word = (int16_t)va_arg(ap, int);
        } else if (strchr("uoxX", spec.conversion)) {
            if (spec.long_value) unsigned_long = (unsigned long long)va_arg(ap, uint32_t);
            else unsigned_word = (uint16_t)va_arg(ap, int);
        } else if (spec.conversion == 's') {
            text = va_arg(ap, const char *);
        } else if (spec.conversion == 'c') {
            character = (int16_t)va_arg(ap, int);
        } else if (spec.conversion == 'p') {
            pointer = va_arg(ap, const void *);
        }
        char *field = NULL;
        size_t field_length = 0;
        if (!format_field(&field, &field_length, &spec, text, signed_word, unsigned_word,
                          signed_long, unsigned_long, character, pointer)) goto failed;
        if (!emit_bytes(dst, capacity, &produced, field, field_length)) {
            free(field); goto failed;
        }
        free(field);
    }
    va_end(ap);
    if (dst != NULL && capacity != 0) dst[produced < capacity ? produced : capacity - 1] = '\0';
    if (produced > (size_t)INT32_MAX) return -1;
    return (int)produced;
failed:
    va_end(ap);
    if (dst != NULL && capacity != 0) dst[0] = '\0';
    return -1;
}

int16_t dos_vsprintf(char *dst, const char *format, va_list args)
{
    int result = dos_vsnprintf(dst, SIZE_MAX, format, args);
    return result < 0 || result > INT16_MAX ? -1 : (int16_t)result;
}

int16_t dos_sprintf(char *dst, const char *format, ...)
{
    int result;
    va_list args;
    va_start(args, format);
    result = dos_vsprintf(dst, format, args);
    va_end(args);
    return result < 0 || result > INT16_MAX ? -1 : (int16_t)result;
}

int16_t dos_printf(const char *format, ...)
{
    va_list args;
    va_list copy;
    int needed;
    char *buffer;
    int16_t result;
    va_start(args, format);
    va_copy(copy, args);
    needed = dos_vsnprintf(NULL, 0, format, copy);
    va_end(copy);
    if (needed < 0) { va_end(args); return -1; }
    buffer = (char *)malloc((size_t)needed + 1);
    if (buffer == NULL) { va_end(args); return -1; }
    needed = dos_vsnprintf(buffer, (size_t)needed + 1, format, args);
    va_end(args);
    if (needed < 0 || needed > INT16_MAX || fwrite(buffer, 1, (size_t)needed, stdout) != (size_t)needed)
        result = -1;
    else result = (int16_t)needed;
    free(buffer);
    return result;
}
