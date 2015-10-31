"""
A simple command line tool that connects to an SMTP server, sends a
mail message with an attachment and then exits.

In order to make it work, you need to fill in the SMTP backend
arguments (connector, username, password) and the .

The program requires one command line argument, the path to the
attachment file.
"""

import asyncio
import logging
import os.path
import sys

from asphalt.core.component import ContainerComponent
from asphalt.core.context import Context
from asphalt.core.runner import run_application


class MailSenderComponent(ContainerComponent):
    def __init__(self, attachment):
        super().__init__()
        self.attachment = attachment

    @asyncio.coroutine
    def start(self, ctx: Context):
        self.add_component('mailer', backend='smtp', connector='tcp+ssl://smtp.example.org:465',
                           username='myusername', password='secret')
        yield from super().start(ctx)

        message = ctx.mailer.create_message(
            subject='Test email with attachment', sender='Sender <sender@example.org>',
            to='Recipient <person@example.org>', plain_body='Take a look at this file!')
        yield from ctx.mailer.add_file_attachment(message, self.attachment)
        yield from ctx.mailer.deliver(message)
        asyncio.get_event_loop().stop()


if len(sys.argv) < 2:
    print('Specify the path to the attachment as the argument to this script!', file=sys.stderr)
    sys.exit(1)

if not os.path.isfile(sys.argv[1]):
    print('The attachment ({}) does not exist or is not a regular file', file=sys.stderr)
    sys.exit(2)

run_application(MailSenderComponent(sys.argv[1]), logging=logging.DEBUG)
