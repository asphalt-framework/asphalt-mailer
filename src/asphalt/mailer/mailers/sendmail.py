import subprocess
import sys
from asyncio import create_subprocess_exec
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Union, Dict, Any

from typeguard import check_argument_types

from asphalt.mailer.api import Mailer, DeliveryError
from asphalt.mailer.utils import get_recipients

__all__ = ['SendmailMailer']


class SendmailMailer(Mailer):
    """
    A mailer that sends mail by running the ``sendmail`` executable in a subprocess.

    :param path: path to the sendmail executable
    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.api.Mailer.create_message`
    """

    __slots__ = 'path'

    def __init__(self, *, path: Union[str, Path] = '/usr/sbin/sendmail',
                 message_defaults: Dict[str, Any] = None):
        assert check_argument_types()
        super().__init__(message_defaults or {})
        self.path = str(path)

    async def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        assert check_argument_types()
        if isinstance(messages, EmailMessage):
            messages = [messages]

        for message in messages:
            args = [self.path, '-i', '-B', '8BITMIME'] + get_recipients(message)
            try:
                process = await create_subprocess_exec(*args, stdin=subprocess.PIPE,
                                                       stderr=subprocess.PIPE)
            except Exception as e:
                raise DeliveryError(str(e), message) from e

            del message['Bcc']
            stdout, stderr = await process.communicate(message.as_bytes())
            if process.returncode:
                error = stderr.decode(sys.stderr.encoding).rstrip()
                raise DeliveryError(error, message)

    def __repr__(self):
        return '{0.__class__.__name__}({0.path!r})'.format(self)
