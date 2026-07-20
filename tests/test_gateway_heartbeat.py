from __future__ import annotations

from io import StringIO

import pytest

from trading_bot.gateway_heartbeat import (
    HEARTBEAT_ENV_NAME,
    HEARTBEAT_ENV_FILE,
    HeartbeatConfigurationError,
    load_heartbeat_url,
    run_gateway_heartbeat,
    save_heartbeat_url,
    validate_heartbeat_url,
)


PRIVATE_URL = "https://hc-ping.invalid/private-uuid"


class FakeResponse:
    status = 200

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_gateway_heartbeat_sends_one_silent_https_request():
    requests = []
    errors = StringIO()

    def opener(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse()

    result = run_gateway_heartbeat(
        environ={HEARTBEAT_ENV_NAME: PRIVATE_URL},
        opener=opener,
        stderr=errors,
    )

    assert result == 0
    assert errors.getvalue() == ""
    assert len(requests) == 1
    assert requests[0][0].full_url == PRIVATE_URL
    assert requests[0][0].method == "GET"
    assert requests[0][1] == 10


def test_gateway_heartbeat_failure_never_prints_private_url():
    errors = StringIO()

    def failing_opener(*_args, **_kwargs):
        raise OSError(f"network failure for {PRIVATE_URL}")

    result = run_gateway_heartbeat(
        environ={HEARTBEAT_ENV_NAME: PRIVATE_URL},
        opener=failing_opener,
        stderr=errors,
    )

    assert result == 1
    assert errors.getvalue() == "gateway_heartbeat=failed\n"
    assert PRIVATE_URL not in errors.getvalue()


def test_gateway_heartbeat_missing_configuration_fails_before_network(tmp_path):
    calls = []
    errors = StringIO()

    result = run_gateway_heartbeat(
        root_dir=tmp_path,
        environ={},
        opener=lambda *_args, **_kwargs: calls.append(True),
        stderr=errors,
    )

    assert result == 2
    assert calls == []
    assert errors.getvalue() == "gateway_heartbeat=configuration_error\n"


@pytest.mark.parametrize(
    "value",
    [
        "http://hc-ping.invalid/example",
        "https://user:password@hc-ping.invalid/example",
        "https://hc-ping.invalid/example#fragment",
        "not-a-url",
        "",
    ],
)
def test_gateway_heartbeat_rejects_unsafe_or_invalid_urls(value):
    with pytest.raises(HeartbeatConfigurationError):
        validate_heartbeat_url(value)


def test_private_heartbeat_file_round_trip_and_environment_precedence(tmp_path):
    path = save_heartbeat_url(PRIVATE_URL, root_dir=tmp_path)

    assert path == tmp_path / HEARTBEAT_ENV_FILE
    assert load_heartbeat_url(root_dir=tmp_path, environ={}) == PRIVATE_URL
    assert (
        load_heartbeat_url(
            root_dir=tmp_path,
            environ={HEARTBEAT_ENV_NAME: "https://example.invalid/environment-check"},
        )
        == "https://example.invalid/environment-check"
    )
