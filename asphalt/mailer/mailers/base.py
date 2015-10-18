from asyncio import coroutine
from abc import abstractmethod, ABCMeta
from email.message import EmailMessage
from typing import Iterable

from asphalt.core.context import ApplicationContext


class BaseMailer(metaclass=ABCMeta):
    def start(self, ctx: ApplicationContext):
        """
        Called to allow each backend to perform any necessary startup actions.
        It can be a coroutine.
        """

    @abstractmethod
    @coroutine
    def deliver(self, messages: Iterable[EmailMessage]):
        """
        Delivers the given messages.

        :param messages: the message(s) to send
        """

    @staticmethod
    def _get_recipients(message: EmailMessage):
        return [addr.addr_spec for addr in (message['To'], message['Cc'], message['Bcc'])]
