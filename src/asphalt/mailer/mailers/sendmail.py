from __future__ import annotations

import subprocess
import sys
from asyncio import create_subprocess_exec
from collections.abc import Iterable
from email.message import EmailMessage
from pathlib import Path
from typing import Any

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
            args = [self.path, "-i", "-B", "8BITMIME"] + get_recipients(message)
            try:
                process = await create_subprocess_exec(
                    *args, stdin=subprocess.PIPE, stderr=subprocess.PIPE
                )
            except Exception as e:
                raise DeliveryError(str(e), message) from e

            del message["Bcc"]
            stdout, stderr = await process.communicate(message.as_bytes())
            if process.returncode:
                error = stderr.decode(sys.stderr.encoding).rstrip()
                raise DeliveryError(error, message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r})"
