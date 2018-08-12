#!/usr/bin/env python3
import json
import subprocess
import sys
import threading

import attr


@attr.s
class Request:
    id = attr.ib()      # integer
    method = attr.ib()  # string
    params = attr.ib()  # dict


@attr.s
class Notification:
    method = attr.ib()  # string
    params = attr.ib()  # dict


@attr.s
class Response:
    id = attr.ib()                  # integer
    result = attr.ib(default=None)  # dict
    error = attr.ib(default=None)   # dict


class LSPClient:
    def __init__(self):
        self._stdin = None
        self._stdout = None

        self._next_id = 0

        self._pending_requests = {}

        self._response_handlers = {}
        self._request_handlers = {}
        self._notification_handlers = {}

    def connect_to_process(self, *argv):
        proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        self._stdin = proc.stdin
        self._stdout = proc.stdout
        threading.Thread(target=self._dispatcher).start()

    def _recv_content(self):
        # NB: This code assumes that the 'Content-Length' header is sent.
        headers = {}

        while True:
            line = self._stdout.readline()

            if not line:
                # EOF
                return None

            assert line.endswith(b"\r\n"), repr(line)
            line = line[:-2].decode("ascii")

            if line:
                key, value = line.split(": ", 1)
                headers[key] = value
            else:
                content_length = int(headers["Content-Length"])
                content = self._stdout.read(content_length).decode("utf-8")
                return json.loads(content)

    def _send_content(self, content):
        content = json.dumps(content).encode("utf-8")

        self._stdin.write(
            b"Content-Length: %(content_length)d\r\n"
            b"\r\n"
            b"%(content)s"
            % {b"content_length": len(content), b"content": content}
        )
        self._stdin.flush()

    def _dispatcher(self):
        while True:
            content = self._recv_content()

            if content is None:
                break

            if "method" in content:
                if "id" in content:
                    # Request
                    id = int(content["id"])
                    request = Request(
                        id=id,
                        method=content["method"],
                        params=content["params"],
                    )
                    callback = self._request_handlers[request.method]
                    callback(request)
                else:
                    # Notification
                    notification = Notification(
                        method=content["method"], params=content["params"]
                    )
                    callback = self._notification_handlers[request.method]
                    callback(notification)
            else:
                # Response
                id = int(content["id"])
                request = self._pending_requests.pop(id)
                response = Response(
                    id=id,
                    result=content.get("result"),
                    error=content.get("error"),
                )

                callback = self._response_handlers[request.method]
                callback(request, response)

    def request(self, method, params):
        id = self._next_id
        self._next_id += 1

        self._send_content(
            {"jsonrpc": "2.0", "id": id, "method": method, "params": params}
        )

        request = Request(id=id, method=method, params=params)
        self._pending_requests[id] = request
        return request

    def notify(self, method, params):
        self._send_content(
            {"jsonrpc": "2.0", "method": method, "params": params}
        )

        return Notification(method=method, params=params)

    def response_handler(self, method):
        def decorator(func):
            self._response_handlers[method] = func
            return func

        return decorator

    def request_handler(self, method):
        def decorator(func):
            self._request_handlers[method] = func
            return func

        return decorator

    def notification_handler(self, method):
        def decorator(func):
            self._notification_handlers[method] = func
            return func

        return decorator
