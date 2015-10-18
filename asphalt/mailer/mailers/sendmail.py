from asyncio import coroutine
from asyncio.events import AbstractEventLoop
from asyncio.subprocess import create_subprocess_exec, PIPE
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Union
import sys

from asphalt.core.util import asynchronous

from .base import BaseMailer
from ..exc import DeliveryError


class SendmailMailer(BaseMailer):
    def __init__(self, event_loop: AbstractEventLoop,
                 sendmail_path: Union[str, Path]='/usr/sbin/sendmail'):
        self.event_loop = event_loop
        self.sendmail_path = Path(sendmail_path)

    @asynchronous
    @coroutine
    def deliver(self, messages: Iterable[EmailMessage]):
        for message in messages:
            args = [str(self.sendmail_path), '-i'] + self._get_recipients(message)
            process = yield from create_subprocess_exec(*args, stdin=PIPE, loop=self.event_loop)
            stdout, stderr = yield from process.communicate(message.as_bytes())
            if process.return_code:
                error = (yield from stderr.read()).decode(sys.stdin.encoding)
                raise DeliveryError(error, message)
