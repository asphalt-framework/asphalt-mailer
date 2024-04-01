from __future__ import annotations

import logging
from collections.abc import Iterable
from contextlib import AsyncExitStack
from email.message import EmailMessage
from ssl import SSLContext
from typing import Any

from anyio import fail_after
from asphalt.core import get_resource_nowait
from smtpproto.auth import PlainAuthenticator, SMTPAuthenticator
from smtpproto.client import AsyncSMTPClient

from .._api import DeliveryError, Mailer

logger = logging.getLogger(__name__)


class BaseSMTPMailer(Mailer):
    """
    Base class for mailers that use `smtpproto`_ to send mails.

    If ``port`` has not been provided, it is set automatically to 587 if
    ``authenticator`` was provided, otherwise 25.

    :param host: host name of the SMTP server
    :param port: override the default port (see above)
    :param tls_context: either an :class:`~ssl.SSLContext` instance or the resource name
        of one
    :param authenticator: the authenticator to use for authenticating against the SMTP
        server
    :param timeout: timeout (in seconds) for all network operations
    :param max_concurrent_connections: maximum number of allowed concurrent connections
        before calls start to block
    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.Mailer.create_message`

    .. _smtpproto: https://github.com/agronholm/smtpproto

    """

    client: AsyncSMTPClient

    def __init__(
        self,
        *,
        host: str,
        port: int | None,
        tls_context: SSLContext | str | None = None,
        authenticator: SMTPAuthenticator | None = None,
        timeout: float = 30,
        max_concurrent_connections: int = 50,
        message_defaults: dict[str, Any] | None = None,
    ):
        super().__init__(message_defaults)
        self.host = host
        self.port = port or (587 if authenticator else 25)
        self.tls_context = tls_context
        self.authenticator = authenticator
        self.timeout = timeout
        self.max_concurrent_connections = max_concurrent_connections

    async def start(self) -> None:
        if isinstance(self.tls_context, str):
            tls_context: SSLContext | None = get_resource_nowait(
                SSLContext, self.tls_context
            )
        else:
            tls_context = self.tls_context

        self.client = AsyncSMTPClient(
            host=self.host,
            port=self.port,
            connect_timeout=self.timeout,
            timeout=self.timeout,
            ssl_context=tls_context,
            authenticator=self.authenticator,
            max_concurrent_connections=self.max_concurrent_connections,
        )

    async def deliver(self, messages: EmailMessage | Iterable[EmailMessage]) -> None:
        if isinstance(messages, EmailMessage):
            messages = [messages]

        async with AsyncExitStack() as stack:
            try:
                with fail_after(self.timeout):
                    session = await stack.enter_async_context(self.client.connect())
            except OSError as e:
                raise DeliveryError(
                    f"Error connecting to {self.client.host} on port {self.client.port}"
                ) from e

            for message in messages:
                try:
                    with fail_after(self.timeout):
                        await session.send_message(message)
                except TimeoutError:
                    raise
                except Exception as e:
                    raise DeliveryError(str(e), message) from e


class SMTPMailer(BaseSMTPMailer):
    """
    A mailer that uses `smtpproto`_ to send mails.

    The default port is chosen as follows:

    * 587: if ``username`` and ``password`` have been defined and ``tls`` is ``True``
    * 25: in all other cases

    :param host: host name of the SMTP server
    :param port: override the default port (see above)
    :param tls_context: either an :class:`~ssl.SSLContext` instance or the resource name
        of one
    :param username: username to authenticate as
    :param password: password to authenticate with
    :param timeout: timeout (in seconds) for all network operations
    :param max_concurrent_connections: maximum number of allowed concurrent connections
        before calls start to block
    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.Mailer.create_message`

    .. _smtpproto: https://github.com/agronholm/smtpproto
    """

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int | None = None,
        tls_context: str | SSLContext | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 30,
        max_concurrent_connections: int = 50,
        message_defaults: dict[str, Any] | None = None,
    ):
        port = port or (587 if username and password else 25)
        if username is not None and password is not None:
            authenticator = PlainAuthenticator(username=username, password=password)
        else:
            authenticator = None

        super().__init__(
            host=host,
            port=port,
            tls_context=tls_context,
            authenticator=authenticator,
            timeout=timeout,
            max_concurrent_connections=max_concurrent_connections,
            message_defaults=message_defaults,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(host={self.host!r}, port={self.port})"
