#include <errno.h>
#include <switch.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <stdlib.h>

#include "net.h"

static bool socket_ready = false;
static bool ssl_ready = false;
static const char *last_error = "NOT_STARTED";
static size_t last_body_length = 0;

size_t net_last_body_length(void) { return last_body_length; }
static char last_error_buffer[64];
const char *net_last_error(void) { return last_error; }

bool net_init(void) {
    if (R_FAILED(socketInitializeDefault()))
        return false;

    socket_ready = true;

    if (R_FAILED(sslInitialize(2))) {
        socketExit();
        socket_ready = false;
        return false;
    }

    ssl_ready = true;
    return true;
}

void net_exit(void) {
    if (ssl_ready) {
        sslExit();
        ssl_ready = false;
    }

    if (socket_ready) {
        socketExit();
        socket_ready = false;
    }
}

static bool ssl_write_all(SslConnection *conn,
                          const char *data, size_t size) {
    size_t offset = 0;

    while (offset < size) {
        u32 written = 0;
        u32 amount = (u32)(size - offset);

        if (R_FAILED(sslConnectionWrite(
                conn, data + offset, amount, &written)))
            return false;

        if (written == 0)
            return false;

        offset += written;
    }

    return true;
}

static bool contains_case_insensitive(
    const char *start, const char *end, const char *needle
) {
    size_t length = strlen(needle);

    while (start + length <= end) {
        if (strncasecmp(start, needle, length) == 0)
            return true;
        start++;
    }

    return false;
}

static bool decode_chunked(char *body, size_t *length) {
    char *src = body;
    char *dst = body;
    char *end = body + *length;

    while (src < end) {
        char *line_end = strstr(src, "\r\n");

        if (!line_end || line_end >= end)
            return false;

        *line_end = '\0';

        char *number_end = NULL;
        unsigned long chunk_size = strtoul(src, &number_end, 16);

        if (number_end == src)
            return false;

        src = line_end + 2;

        if (chunk_size == 0) {
            *dst = '\0';
            *length = (size_t)(dst - body);
            return true;
        }

        if ((size_t)(end - src) < chunk_size + 2)
            return false;

        memmove(dst, src, chunk_size);
        dst += chunk_size;
        src += chunk_size;

        if (src[0] != '\r' || src[1] != '\n')
            return false;

        src += 2;
    }

    return false;
}

bool net_https_request(const char *host, const char *method, const char *path,
                       const char *content_type, const char *req_body,
                       size_t body_len, char *response, size_t response_size) {
    last_error = "ARGUMENT";
    if (!socket_ready || !ssl_ready ||
        !host || !path || !response || response_size < 256)
        return false;

    response[0] = '\0';

    if (strlen(host) >= 255 || path[0] != '/')
        return false;

    struct addrinfo hints = {0};
    struct addrinfo *addresses = NULL;

    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, "443", &hints, &addresses) != 0) { last_error = "DNS"; return false; }

    int fd = -1;

    for (struct addrinfo *it = addresses; it; it = it->ai_next) {
        fd = socket(it->ai_family, it->ai_socktype, it->ai_protocol);

        if (fd < 0)
            continue;

        if (connect(fd, it->ai_addr, it->ai_addrlen) == 0)
            break;

        close(fd);
        fd = -1;
    }

    freeaddrinfo(addresses);

    if (fd < 0) { last_error = "TCP_CONNECT"; return false; }

    SslContext context = {0};
    SslConnection connection = {0};

    bool context_ready = false;
    bool connection_ready = false;
    bool success = false;

    if (R_FAILED(sslCreateContext(&context, SslVersion_Auto))) { last_error = "SSL_CONTEXT"; goto cleanup; }

    context_ready = true;

    if (R_FAILED(sslContextCreateConnection(&context, &connection))) { last_error = "SSL_CONNECTION"; goto cleanup; }

    connection_ready = true;

    if (R_FAILED(sslConnectionSetOption(
            &connection, SslOptionType_DoNotCloseSocket, true))) { last_error = "SSL_OPTION"; goto cleanup; }

    if (R_FAILED(sslConnectionSetHostName(
            &connection, host, (u32)strlen(host) + 1))) { last_error = "SSL_HOSTNAME"; goto cleanup; }

    if (R_FAILED(sslConnectionSetVerifyOption(
            &connection,
            SslVerifyOption_PeerCa | SslVerifyOption_HostName))) { last_error = "SSL_VERIFY"; goto cleanup; }

    int ssl_fd = socketSslConnectionSetSocketDescriptor(&connection, fd);

    if (ssl_fd < 0 && errno != ENOENT) {
        snprintf(last_error_buffer, sizeof(last_error_buffer),
                 "SSL_SOCKET: errno %d", errno);
        last_error = last_error_buffer;
        goto cleanup;
    }

    if (R_FAILED(sslConnectionDoHandshake(
            &connection, NULL, NULL, NULL, 0))) { last_error = "TLS_HANDSHAKE"; goto cleanup; }

    char *request = malloc(1024 + body_len);

    if (!request) { last_error = "OUT_OF_MEMORY"; goto cleanup; }

    int request_length;

    if (req_body && body_len > 0) {
        request_length = snprintf(
            request, 1024 + body_len,
            "%s %s HTTP/1.0\r\n"
            "Host: %s\r\n"
            "User-Agent: NX-Stach/1.0\r\n"
            "Accept: application/json\r\n"
            "Content-Type: %s\r\n"
            "Content-Length: %u\r\n"
            "Accept-Encoding: identity\r\n"
            "Connection: close\r\n"
            "\r\n",
            method, path, host,
            content_type ? content_type : "application/json",
            (unsigned)body_len);

        if (request_length <= 0 || (size_t)request_length + body_len >= 1024 + body_len) {
            free(request);
            goto cleanup;
        }

        memcpy(request + request_length, req_body, body_len);
        request_length += (int)body_len;
    } else {
        request_length = snprintf(
            request, 1024,
            "%s %s HTTP/1.0\r\n"
            "Host: %s\r\n"
            "User-Agent: NX-Stach/1.0\r\n"
            "Accept: application/json\r\n"
            "Accept-Encoding: identity\r\n"
            "Connection: close\r\n"
            "\r\n",
            method, path, host);
    }

    if (request_length <= 0) {
        free(request);
        goto cleanup;
    }

    bool sent = ssl_write_all(&connection, request, (size_t)request_length);

    free(request);

    if (!sent) { last_error = "HTTP_SEND"; goto cleanup; }

    size_t used = 0;

    while (used < response_size - 1) {
        u32 received = 0;
        size_t remaining = response_size - 1 - used;
        u32 amount = remaining > 2048 ? 2048 : (u32)remaining;

        Result result = sslConnectionRead(
            &connection, response + used, amount, &received);

        if (R_FAILED(result))
            break;

        if (received == 0)
            break;

        used += received;
    }

    if (used == 0 || used >= response_size - 1) { last_error = "HTTP_READ"; goto cleanup; }

    response[used] = '\0';

    char *header_end = strstr(response, "\r\n\r\n");

    if (!header_end) { last_error = "HTTP_HEADERS"; goto cleanup; }

    int status = 0;

    if (sscanf(response, "HTTP/%*u.%*u %d", &status) != 1 ||
        status != 200) { last_error = "HTTP_STATUS"; goto cleanup; }

    bool chunked = false;
    char *line = strstr(response, "\r\n");

    while (line && line < header_end) {
        line += 2;

        if (line >= header_end)
            break;

        if (strncasecmp(line, "Transfer-Encoding:", 18) == 0 &&
            contains_case_insensitive(line, header_end, "chunked")) {
            chunked = true;
            break;
        }

        line = strstr(line, "\r\n");
    }

    char *body = header_end + 4;
    size_t body_length = used - (size_t)(body - response);

    memmove(response, body, body_length);
    response[body_length] = '\0';

    if (chunked && !decode_chunked(response, &body_length)) { last_error = "CHUNK_DECODE"; goto cleanup; }

    response[body_length] = '\0';
    last_body_length = body_length;
    success = body_length > 0;
    last_error = success ? "OK" : "EMPTY_BODY";

cleanup:
    if (connection_ready)
        sslConnectionClose(&connection);

    close(fd);

    if (context_ready)
        sslContextClose(&context);

    if (!success)
        response[0] = '\0';

    return success;
}

bool net_https_get(const char *host, const char *path,
                   char *response, size_t response_size)
{
    return net_https_request(host, "GET", path, NULL, NULL, 0,
                             response, response_size);
}
