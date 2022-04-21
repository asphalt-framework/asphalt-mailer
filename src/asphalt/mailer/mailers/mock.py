from __future__ import annotations

from collections.abc import Iterable
from email.message import EmailMessage
from typing import Any

from ..api import Mailer


class MockMailer(Mailer):
    """
    A mailer that does not send any messages but instead stores them in a member
    variable.

    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.api.Mailer.create_message`

    :ivar messages: list of messages that would normally have been sent
    """

    __slots__ = "messages"

    def __init__(self, *, message_defaults: dict[str, Any] | None = None):
        super().__init__(message_defaults or {})
        self.messages: list[EmailMessage] = []

    async def deliver(self, messages: EmailMessage | Iterable[EmailMessage]) -> None:
        if isinstance(messages, EmailMessage):
            messages = [messages]

        self.messages.extend(messages)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
