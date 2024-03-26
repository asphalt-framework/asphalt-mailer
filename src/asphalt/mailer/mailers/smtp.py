from __future__ import annotations

import logging
from collections.abc import Iterable
from email.message import EmailMessage
from ssl import SSLContext
from typing import Any

from aiosmtplib import SMTP, SMTPTimeoutError
from asphalt.core import add_teardown_callback, get_resource_nowait

from .._api import DeliveryError, Mailer

logger = logging.getLogger(__name__)


class SMTPMailer(Mailer):
    """
    A mailer that uses `aiosmtplib`_ to send mails.

    The default port is chosen as follows:

    * 587: if ``username`` and ``password`` have been defined and ``tls`` is ``True``
    * 25: in all other cases

    :param host: host name of the SMTP server
    :param port: override the default port (see above)
    :param tls: whether to initiate TLS using STARTTLS once connected (defaults to
        ``True`` if ``username`` and ``password`` have been defined)
    :param tls_context: either an :class:`~ssl.SSLContext` instance or the resource name
        of one
    :param username: username to authenticate as
    :param password: password to authenticate with
    :param timeout: timeout (in seconds) for all network operations
    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.api.Mailer.create_message`

    .. _aiosmtplib: https://github.com/cole/aiosmtplib
    """

    _smtp: SMTP

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int | None = None,
        tls: bool | None = None,
        tls_context: str | SSLContext | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 10,
        message_defaults: dict[str, Any] | None = None,
    ):
        super().__init__(message_defaults or {})
        self.host = host
        self.tls = tls if tls is not None else bool(username and password)
        self.port = port or (587 if username and password and self.tls else 25)
        self.tls_context = tls_context
        self.username = username
        self.password = password
        self.timeout = timeout

    async def start(self) -> None:
        if isinstance(self.tls_context, str):
            tls_context: SSLContext | None = get_resource_nowait(
                SSLContext, self.tls_context
            )
        else:
            tls_context = self.tls_context

        self._smtp = SMTP(
            hostname=self.host,
            port=self.port,
            tls_context=tls_context,
            timeout=self.timeout,
        )
        add_teardown_callback(self._smtp.close)

    async def deliver(self, messages: EmailMessage | Iterable[EmailMessage]) -> None:
        if isinstance(messages, EmailMessage):
            messages = [messages]

        try:
            try:
                await self._smtp.connect()

                # Authenticate if needed
                if self.username is not None and self.password is not None:
                    await self._smtp.login(self.username, self.password)
            except Exception as e:
                raise DeliveryError(str(e)) from e

            for message in messages:
                try:
                    await self._smtp.send_message(message)
                except Exception as e:
                    raise DeliveryError(str(e), message) from e
        finally:
            if self._smtp.is_connected:
                try:
                    await self._smtp.quit()
                except (ConnectionError, SMTPTimeoutError):  # pragma: nocover
                    self._smtp.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(host={self.host!r}, port={self.port})"
