from email.message import EmailMessage
from typing import Iterable, Union, Dict, Any, List  # noqa: F401

from typeguard import check_argument_types

from asphalt.mailer.api import Mailer


class MockMailer(Mailer):
    """
    A mailer that does not send any messages but instead stores them in a member variable.

    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.api.Mailer.create_message`

    :ivar messages: list of messages that would normally have been sent
    """

    __slots__ = 'messages'

    def __init__(self, *, message_defaults: Dict[str, Any] = None):
        assert check_argument_types()
        super().__init__(message_defaults or {})
        self.messages = []  # type: List[EmailMessage]

    async def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        assert check_argument_types()
        if isinstance(messages, EmailMessage):
            messages = [messages]

        self.messages.extend(messages)

    def __repr__(self):
        return '{0.__class__.__name__}()'.format(self)
