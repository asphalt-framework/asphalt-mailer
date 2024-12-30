from __future__ import annotations

import ssl
from base64 import b64decode
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import contextmanager
from email.message import EmailMessage, Message
from typing import Any

import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message as AIOSMTPMessage
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, Session
from asphalt.core import Context, add_resource

from asphalt.mailer import DeliveryError
from asphalt.mailer.mailers.smtp import SMTPMailer

pytestmark = pytest.mark.anyio


class MessageHandler(AIOSMTPMessage):
    def __init__(self, message_class: type[Message] | None = None):
        super().__init__(message_class)
        self.messages: list[Any] = []

    def handle_message(self, message: Message) -> None:
        self.messages.append(message)


class StartTLSController(Controller):
    """
    This special controller exists to allow starting aiosmtpd with an SSL context but
    without implicit TLS.
    """

    def __init__(
        self,
        handler: Any,
        factory: Callable[..., SMTP] = SMTP,
        hostname: str | None = None,
        port: int = 0,
        *,
        ready_timeout: float = 1.0,
        ssl_context: ssl.SSLContext | None = None,
    ):
        super().__init__(
            handler,
            hostname=hostname,
            port=port,
            ready_timeout=ready_timeout,
            ssl_context=None,
        )
        self.__factory = factory
        self.__ssl_context = ssl_context

    def factory(self) -> SMTP:
        return self.__factory(
            self.handler,
            hostname=self.hostname,
            tls_context=self.__ssl_context,
            require_starttls=self.__ssl_context is not None,
        )


@contextmanager
def run_smtp_server(
    port: int, handler: AIOSMTPMessage, server_tls_context: ssl.SSLContext | None = None
) -> Generator[None, None, None]:
    controller = StartTLSController(
        handler,
        hostname="localhost",
        port=port,
        ssl_context=server_tls_context,
    )
    controller.start()
    yield
    controller.stop()


@pytest.fixture
async def mailer(
    free_tcp_port: int, client_tls_context: ssl.SSLContext
) -> AsyncGenerator[SMTPMailer, None]:
    mailer = SMTPMailer(port=free_tcp_port, timeout=3, tls_context=client_tls_context)
    async with Context():
        await mailer.start()
        yield mailer


@pytest.mark.parametrize(
    "username, password, expected_port",
    [
        pytest.param("foo", "bar", 587, id="tls"),
        pytest.param("foo", None, 25, id="plain"),
    ],
)
def test_port_selection(username: str, password: str, expected_port: int) -> None:
    mailer = SMTPMailer(username=username, password=password)
    assert mailer.port == expected_port


async def test_resources() -> None:
    mailer = SMTPMailer(tls_context="contextresource")
    async with Context():
        sslcontext = ssl.create_default_context()
        add_resource(sslcontext, "contextresource")
        await mailer.start()
        assert mailer.client.ssl_context is sslcontext


async def test_deliver(
    mailer: SMTPMailer, sample_message: EmailMessage, free_tcp_port: int
) -> None:
    handler = MessageHandler()
    with run_smtp_server(free_tcp_port, handler):
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
    sample_message: EmailMessage,
    free_tcp_port: int,
    server_tls_context: ssl.SSLContext,
    client_tls_context: ssl.SSLContext,
) -> None:
    """Test that authentication works."""

    class AuthHandler(MessageHandler):
        async def auth_PLAIN(self, server: SMTP, args: list[str]) -> AuthResult:
            credentials = b64decode(args[1])
            if credentials == b"\x00foo\x00bar":
                return AuthResult(success=True)
            else:
                return AuthResult(success=False)

    mailer = SMTPMailer(
        port=free_tcp_port,
        username="foo",
        password="bar",
        timeout=3,
        tls_context=client_tls_context,
    )
    handler = AuthHandler()
    with run_smtp_server(free_tcp_port, handler, server_tls_context):
        async with Context():
            await mailer.start()
            await mailer.deliver(sample_message)

    assert len(handler.messages) == 1


async def test_deliver_connect_error(
    mailer: SMTPMailer, sample_message: EmailMessage, free_tcp_port: int
) -> None:
    mailer.client.port = free_tcp_port + 1
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    exc.match(f"Error connecting to localhost on port {mailer.client.port}")


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

    with run_smtp_server(free_tcp_port, BadHandler()):
        with pytest.raises(DeliveryError) as exc:
            await mailer.deliver(sample_message)

    exc.match("Error: foo")


async def test_repr(mailer: SMTPMailer, free_tcp_port: int) -> None:
    assert repr(mailer) == f"SMTPMailer(host='localhost', port={free_tcp_port})"
