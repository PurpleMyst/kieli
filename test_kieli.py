import io
import threading

import pytest

import kieli

def test_initialization():
    client = kieli.LSPClient()

    client._stdin = io.BytesIO()

    expected_stdin = (
        b"Content-Length: 119\r\n"
        b"\r\n"
        b'{'
        b'"jsonrpc": "2.0", '
        b'"id": 0, '
        b'"method": "initialize", '
        b'"params": {'
        b'"processId": null, '
        b'"rootUri": null, '
        b'"capabilities": {}'
        b'}'
        b'}'
    )

    client.request("initialize", {"processId": None, "rootUri": None, "capabilities": {}})

    client._stdin.seek(0)
    assert client._stdin.read() == expected_stdin

    event = threading.Event()

    @client.response_handler("initialize")
    def initialize(request, response):
        assert request.id == 0
        assert request.method == "initialize"
        assert request.params == {"processId": None, "rootUri": None, "capabilities": {}}

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
