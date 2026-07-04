import urllib.error
import urllib.request

import pytest

from uebot import health


@pytest.fixture
def server():
    health.set_ready(False)
    srv = health.start_monitoring_server(0)  # port 0 = ephemeral
    port = srv.server_address[1]
    yield port
    srv.shutdown()


def _get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as resp:
        return resp.status, resp.read().decode()


def test_healthz_always_ok(server):
    status, _ = _get(server, "/healthz")
    assert status == 200


def test_readyz_reflects_state(server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(server, "/readyz")
    assert exc.value.code == 503
    health.set_ready(True)
    status, _ = _get(server, "/readyz")
    assert status == 200


def test_metrics_endpoint(server):
    status, body = _get(server, "/metrics")
    assert status == 200
    assert "uebot_build_info" in body
