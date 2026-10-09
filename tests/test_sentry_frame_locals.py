"""Sentry events carry no local variables unless the service asks for them.

Frame locals are where credentials and customer data leak: a database URL in `conn_str`, an auth header in an HTTP
client's `headers`, a document in `text`. The SDK's scrubber only matches exact top-level variable names, and no list
of libraries can cover the service's own frames, so setup_logging turns the locals off. A service that wants them
back opts in with sentry={'include_local_variables': True}.
"""

import logging

import pytest
import sentry_sdk
from sentry_sdk.transport import Transport
from sentry_sdk.utils import iter_event_frames

from turnus_logging import setup_logging

SECRET = 'S3cr3t-value-never-in-sentry'
# Never reached: the test swaps the transport before anything is sent.
INERT_DSN = 'http://public@127.0.0.1:1/0'

service_logger = logging.getLogger('svc')


class _Capture(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.payload = b''  # everything sent, logs included
        self.events = []

    def capture_envelope(self, envelope):
        self.payload += envelope.serialize()
        self.events += [item.get_event() for item in envelope.items if item.get_event()]


@pytest.fixture(autouse=True)
def fresh_sentry():
    sentry_sdk.get_global_scope().set_client(None)
    yield
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)


def _sent_by_service(send, **sentry) -> _Capture:
    """Runs the service setup, then returns what `send` makes the Sentry client send."""
    setup_logging(service_name='test-frame-locals', log_level=logging.INFO, sentry={'dsn': INERT_DSN, **sentry})
    client = sentry_sdk.get_client()
    assert client.is_active()
    client.transport.kill()
    client.transport = _Capture()
    send()
    client.flush()
    return client.transport


def _frames(sent):
    return [frame for event in sent.events for frame in iter_event_frames(event)]


def _connect(conn_str):
    raise ConnectionError('connection refused')


def _log_a_failed_database_login():
    # The shape that leaked: the caller holds the URL in a local, and so does every frame it is passed to.
    conn_str = 'postgresql://svc:' + SECRET + '@db.internal/app'
    try:
        _connect(conn_str)
    except ConnectionError:
        service_logger.exception('database login failed')


def _log_a_stack_without_an_exception():
    conn_str = 'postgresql://svc:' + SECRET + '@db.internal/app'  # noqa: F841
    service_logger.error('connection pool exhausted', stack_info=True)


@pytest.mark.parametrize('log', [_log_a_failed_database_login, _log_a_stack_without_an_exception])
def test_an_event_carries_no_local_variables(log):
    sent = _sent_by_service(log)

    assert _frames(sent)  # the event was sent, with its stack
    assert not [frame for frame in _frames(sent) if 'vars' in frame]
    assert SECRET.encode() not in sent.payload


def test_a_service_can_opt_in_to_local_variables():
    sent = _sent_by_service(_log_a_failed_database_login, include_local_variables=True)

    assert any('conn_str' in (frame.get('vars') or {}) for frame in _frames(sent))
    assert SECRET.encode() in sent.payload  # the control for the tests above: with locals on, this is what leaks


def test_only_true_opts_in(capsys):
    # A truthy string from a config file or an env var must not switch the locals on, and the service is told.
    sent = _sent_by_service(_log_a_failed_database_login, include_local_variables='false')

    assert _frames(sent)
    assert not [frame for frame in _frames(sent) if 'vars' in frame]
    assert "sentry.include_local_variables='false'" in capsys.readouterr().out
