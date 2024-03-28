from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterable
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from anyio import run_process

from .._api import DeliveryError, Mailer
from .._utils import get_recipients


class SendmailMailer(Mailer):
    """
    A mailer that sends mail by running the ``sendmail`` executable in a subprocess.

    :param path: path to the sendmail executable
    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.api.Mailer.create_message`
    """

    __slots__ = "path"

    def __init__(
        self,
        *,
        path: str | Path = "/usr/sbin/sendmail",
        message_defaults: dict[str, Any] | None = None,
    ):
        super().__init__(message_defaults or {})
        self.path = str(path)

    async def deliver(self, messages: EmailMessage | Iterable[EmailMessage]) -> None:
        if isinstance(messages, EmailMessage):
            messages = [messages]

        for message in messages:
            recipients = get_recipients(message)
            del message["Bcc"]
            command = [self.path, "-i", "-B", "8BITMIME"] + recipients
            try:
                await run_process(
                    command, input=message.as_bytes(), stderr=subprocess.PIPE
                )
            except subprocess.CalledProcessError as e:
                error = e.stderr.decode(sys.stderr.encoding).rstrip()
                raise DeliveryError(error, message) from e
            except Exception as e:
                raise DeliveryError(str(e), message) from e

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r})"
