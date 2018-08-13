import io
import json
import threading

import pytest

import kieli


def test_initialization():
    client = kieli.LSPClient()

    client._stdin = io.BytesIO()

    expected_stdin_prefix = b"Content-Length: 119\r\n\r\n"

    # must not hard-code this as bytes because the order of things in the json
    # is not the same every time on python 3.4, but the length in
    # expected_stdin_prefix should always be same regardless of the order
    expected_stdin_json_part = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {"processId": None, "rootUri": None, "capabilities": {}},
    }

    client.request(
        "initialize", {"processId": None, "rootUri": None, "capabilities": {}}
    )

    client._stdin.seek(0)
    assert (
        client._stdin.read(len(expected_stdin_prefix)) == expected_stdin_prefix
    )
    json_string = client._stdin.read().decode("utf-8")
    assert json.loads(json_string) == expected_stdin_json_part

    event = threading.Event()

    @client.response_handler("initialize")
    def initialize(request, response):
        assert request.id == 0
        assert request.method == "initialize"
        assert request.params == {
            "processId": None,
            "rootUri": None,
            "capabilities": {},
        }

        assert response.id == 0
        assert response.result == {"hoverProvider": True}
        assert response.error is None

        event.set()

    client._stdout = io.BytesIO(
        b"Content-Length: 44\r\n"
        b"\r\n"
        b'{"id": 0, "result": {"hoverProvider": true}}'
    )

    # We only start the dispatcher thread after we write to stdout because
    # else it fails with an AssertionError due to `io.BytesIO.readline`
    # returning `b""` on EOF.
    threading.Thread(target=client._dispatcher).start()

    if not event.wait(timeout=5):
        pytest.fail("Timed out waiting for initialize response.")
