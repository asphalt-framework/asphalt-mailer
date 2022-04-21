from __future__ import annotations

import socket
import ssl
from email.message import EmailMessage
from typing import cast

import pytest
import trustme
from _pytest.fixtures import SubRequest


@pytest.fixture
def sample_message() -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = "foo@bar.baz"
    msg["To"] = "Test Recipient <test@domain.country>, test2@domain.country"
    msg["Cc"] = "Test CC <testcc@domain.country>, testcc2@domain.country"
    msg["Bcc"] = "Test BCC <testbcc@domain.country>, testbcc2@domain.country"
    msg.set_content("Test content")
    return msg


@pytest.fixture
def recipients() -> tuple[str, ...]:
    return (
        "test@domain.country",
        "test2@domain.country",
        "testcc@domain.country",
        "testcc2@domain.country",
        "testbcc@domain.country",
        "testbcc2@domain.country",
    )


@pytest.fixture(scope="session")
def ca() -> trustme.CA:
    return trustme.CA()


@pytest.fixture(scope="session")
def server_tls_context(ca: trustme.CA) -> ssl.SSLContext:
    server_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ca.issue_cert("localhost").configure_cert(server_context)
    return server_context


@pytest.fixture(scope="session")
def client_tls_context(ca: trustme.CA) -> ssl.SSLContext:
    client_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ca.configure_trust(client_context)
    return client_context


@pytest.fixture(
    params=[pytest.param(False, id="plaintext"), pytest.param(True, id="tls")]
)
def tls(request: SubRequest) -> bool:
    return cast(bool, request.param)


@pytest.fixture
def free_tcp_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    port = cast(int, sock.getsockname()[1])
    sock.close()
    return port
