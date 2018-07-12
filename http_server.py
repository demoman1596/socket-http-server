import socket
import sys
import os
import traceback
import mimetypes

def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return b"\r\n".join([
        b"HTTP/1.1 200 OK",
        b"Content-Type: " + mimetype,
        b"",
        body,
    ])


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""
    return b"\r\n".join([
        b"HTTP/1.1 405 Method Not Allowed",
        b"",
        b"You can't do that on this server!",
    ])


def response_not_found():
    """Returns a 404 Not Found response"""
    return b"\r\n".join([
        b"HTTP/1.1 404 Not Found",
        b"",
        b"Requested resource not found on this server.",
    ])


def parse_request(request):
    """
    Given the content of an HTTP request, returns the uri of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """
    method, path, version = request.split("\r\n")[0].split(" ")

    if method != "GET":
        raise NotImplementedError

    return path


def resolve_uri(uri):
    """
    This method should return appropriate content and a mime type.

    If the requested URI is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the URI is a file, it should return the contents of that file
    and its correct mimetype.

    If the URI does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        resolve_uri('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        resolve_uri('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        resolve_uri('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        resolve_uri('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """
    relative_path = "webroot" + uri

    if os.path.isdir(relative_path):
        content = b""
        dirlist = os.listdir(relative_path)
        for item in os.listdir(relative_path):
            content += item.encode() + b"\r\n"
        mime_type = b"text/plain"
    elif os.path.isfile(relative_path):
        content = b""
        with open(relative_path, "rb") as binfile:
            content = binfile.read()
        mime_type = mimetypes.guess_type(uri)[0].encode()
    else:
        raise NameError

    print(mime_type)
    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                try:
                    path = parse_request(request)
                    body, mimetype = resolve_uri(path)
                    response = response_ok(body, mimetype)
                except NotImplementedError:
                    response = response_method_not_allowed()
                except NameError:
                    response = response_not_found()

                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)


