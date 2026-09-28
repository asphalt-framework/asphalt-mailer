from __future__ import annotations

import ssl
from asyncio import get_running_loop
from base64 import b64decode
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from email.message import EmailMessage, Message
from typing import Any

import pytest
from aiosmtpd.handlers import Message as AIOSMTPMessage
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, Session
from asphalt.core.context import Context

from asphalt.mailer.api import DeliveryError
from asphalt.mailer.mailers.smtp import SMTPMailer

pytestmark = pytest.mark.anyio


class MessageHandler(AIOSMTPMessage):
    def __init__(self, message_class: type[Message] | None = None):
        super().__init__(message_class)
        self.messages: list[Any] = []

    def handle_message(self, message: Message) -> None:
        self.messages.append(message)


@asynccontextmanager
async def run_smtp_server(
    port: int, handler: AIOSMTPMessage, server_tls_context: ssl.SSLContext | None = None
) -> AsyncGenerator[SMTP, None]:
    smtp = SMTP(
        handler,
        require_starttls=server_tls_context is not None,
        tls_context=server_tls_context,
    )
    server = await get_running_loop().create_server(lambda: smtp, port=port)
    yield smtp
    server.close()
    await server.wait_closed()


@pytest.fixture
async def mailer(
    free_tcp_port: int, client_tls_context: ssl.SSLContext, tls: bool
) -> AsyncGenerator[SMTPMailer, None]:
    mailer = SMTPMailer(
        port=free_tcp_port, timeout=1, tls=tls, tls_context=client_tls_context
    )
    async with Context():
        await mailer.start()
        yield mailer


@pytest.mark.parametrize(
    "username, password, tls, expected_port",
    [
        pytest.param("foo", "bar", True, 587, id="forcetls"),
        pytest.param("foo", "bar", None, 587, id="autotls"),
        pytest.param("foo", "bar", False, 25, id="disabletls"),
        pytest.param("foo", None, None, 25, id="nopassword"),
    ],
)
def test_port_selection(
    username: str, password: str, tls: bool, expected_port: int
) -> None:
    mailer = SMTPMailer(username=username, password=password, tls=tls)
    assert mailer.port == expected_port


async def test_resources() -> None:
    mailer = SMTPMailer(tls_context="contextresource")
    async with Context() as ctx:
        sslcontext = ssl.create_default_context()
        ctx.add_resource(sslcontext, "contextresource")
        await mailer.start()
        assert mailer.tls_context is sslcontext


async def test_deliver(
    mailer: SMTPMailer, sample_message: EmailMessage, free_tcp_port: int
) -> None:
    handler = MessageHandler()
    async with run_smtp_server(free_tcp_port, handler):
        await mailer.deliver(sample_message)

    assert len(handler.messages) == 1
    received_message = handler.messages[0]

    headers = dict(received_message.items())
    del headers["X-Peer"]
    assert headers == {
        "From": "foo@bar.baz",
        "To": "Test Recipient <test@domain.country>, test2@domain.country",
        "Cc": "Test CC <testcc@domain.country>, testcc2@domain.country",
        "Content-Type": 'text/plain; charset="utf-8"',
        "Content-Transfer-Encoding": "7bit",
        "MIME-Version": "1.0",
        "X-MailFrom": "foo@bar.baz",
        "X-RcptTo": (
            "test@domain.country, test2@domain.country, testcc@domain.country, "
            "testcc2@domain.country, testbcc@domain.country, testbcc2@domain.country"
        ),
    }
    assert received_message.get_payload() == "Test content\r\n"


async def test_deliver_auth(
    mailer: SMTPMailer,
    sample_message: EmailMessage,
    free_tcp_port: int,
    server_tls_context: ssl.SSLContext,
) -> None:
    """Test that authentication works."""

    class AuthHandler(MessageHandler):
        async def auth_PLAIN(self, server: SMTP, args: list[str]) -> AuthResult:
            credentials = b64decode(args[1])
            if credentials == b"\x00foo\x00bar":
                return AuthResult(success=True)
            else:
                return AuthResult(success=False)

    mailer.username = "foo"
    mailer.password = "bar"
    handler = AuthHandler()
    async with run_smtp_server(free_tcp_port, handler, server_tls_context):
        await mailer.deliver(sample_message)

    assert len(handler.messages) == 1


async def test_deliver_connect_error(
    mailer: SMTPMailer, sample_message: EmailMessage, free_tcp_port: int
) -> None:
    mailer._smtp.port = free_tcp_port + 1
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    exc.match(f"Error connecting to localhost on port {mailer._smtp.port}")


async def test_deliver_error(
    mailer: SMTPMailer, sample_message: EmailMessage, free_tcp_port: int
) -> None:
    """
    Test that SMTP errors during message delivery get converted into DeliveryErrors.
    """

    class BadHandler(MessageHandler):
        async def handle_DATA(
            self, server: SMTP, session: Session, envelope: Envelope
        ) -> str:
            return "503 Error: foo"

    async with run_smtp_server(free_tcp_port, BadHandler()):
        with pytest.raises(DeliveryError) as exc:
            await mailer.deliver(sample_message)

    exc.match("Error: foo")


def test_repr(mailer: SMTPMailer, free_tcp_port: int) -> None:
    assert repr(mailer) == f"SMTPMailer(host='localhost', port={free_tcp_port})"
