from asyncio import coroutine
from email.message import EmailMessage
from typing import Iterable, Union, Dict, Any

from asphalt.core.util import asynchronous

from ..api import Mailer


class MockMailer(Mailer):
    """
    A mailer that does not send any messages but instead stores them in
    a member variable.

    :param defaults: default values for omitted keyword arguments of
                     :meth:`~asphalt.mailer.api.Mailer.create_message`
    :ivar messages: list of messages that would normally have been sent
    """

    __slots__ = 'messages'

    def __init__(self, *, defaults: Dict[str, Any]=None):
        super().__init__(defaults or {})
        self.messages = []

    @asynchronous
    @coroutine
    def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        if isinstance(messages, EmailMessage):
            messages = [messages]

        self.messages.extend(messages)

    def __repr__(self):
        return '{0.__class__.__name__}()'.format(self)
