import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "source", "net.c")
s = open(p, encoding="utf-8").read()

old_sig = """bool net_https_get(const char *host, const char *path,
                   char *response, size_t response_size) {"""
new_sig = """bool net_https_request(const char *host, const char *method, const char *path,
                       const char *content_type, const char *body,
                       size_t body_len, char *response, size_t response_size) {"""
if old_sig not in s:
    raise SystemExit("signature not found")

s = s.replace(old_sig, new_sig, 1)

old_req = """    char request[1024];

    int request_length = snprintf(
        request, sizeof(request),
        "GET %s HTTP/1.0\\r\\n"
        "Host: %s\\r\\n"
        "User-Agent: NX-Stach/1.0\\r\\n"
        "Accept: application/json\\r\\n"
        "Accept-Encoding: identity\\r\\n"
        "Connection: close\\r\\n"
        "\\r\\n",
        path, host
    );

    if (request_length < 0 ||
        (size_t)request_length >= sizeof(request))
        goto cleanup;

    if (!ssl_write_all(&connection, request, (size_t)request_length)) { last_error = "HTTP_SEND"; goto cleanup; }"""

new_req = """    char *request = malloc(1024 + body_len);

    if (!request) { last_error = "OUT_OF_MEMORY"; goto cleanup; }

    int request_length;

    if (body && body_len > 0) {
        request_length = snprintf(
            request, 1024 + body_len,
            "%s %s HTTP/1.0\\r\\n"
            "Host: %s\\r\\n"
            "User-Agent: NX-Stach/1.0\\r\\n"
            "Accept: application/json\\r\\n"
            "Content-Type: %s\\r\\n"
            "Content-Length: %u\\r\\n"
            "Accept-Encoding: identity\\r\\n"
            "Connection: close\\r\\n"
            "\\r\\n",
            method, path, host,
            content_type ? content_type : "application/json",
            (unsigned)body_len);

        if (request_length <= 0 || (size_t)request_length + body_len >= 1024 + body_len) {
            free(request);
            goto cleanup;
        }

        memcpy(request + request_length, body, body_len);
        request_length += (int)body_len;
    } else {
        request_length = snprintf(
            request, 1024,
            "%s %s HTTP/1.0\\r\\n"
            "Host: %s\\r\\n"
            "User-Agent: NX-Stach/1.0\\r\\n"
            "Accept: application/json\\r\\n"
            "Accept-Encoding: identity\\r\\n"
            "Connection: close\\r\\n"
            "\\r\\n",
            method, path, host);
    }

    if (request_length <= 0) {
        free(request);
        goto cleanup;
    }

    bool sent = ssl_write_all(&connection, request, (size_t)request_length);

    free(request);

    if (!sent) { last_error = "HTTP_SEND"; goto cleanup; }"""

if old_req not in s:
    raise SystemExit("request block not found")

s = s.replace(old_req, new_req, 1)
s = s.rstrip() + """

bool net_https_get(const char *host, const char *path,
                   char *response, size_t response_size)
{
    return net_https_request(host, "GET", path, NULL, NULL, 0,
                             response, response_size);
}
"""

open(p, "w", encoding="utf-8").write(s)
print("ok")
