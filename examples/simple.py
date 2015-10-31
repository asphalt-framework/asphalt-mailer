"""
A simple command line tool that connects to an SMTP server, sends a
mail message and then exits.

You can experiment by modifying the arguments to add_component()
and/or ctx.mailer.create_and_deliver().
"""

import asyncio
import logging

from asphalt.core.component import ContainerComponent
from asphalt.core.context import Context
from asphalt.core.runner import run_application


class MailSenderComponent(ContainerComponent):
    @asyncio.coroutine
    def start(self, ctx: Context):
        self.add_component('mailer', backend='smtp', connector='tcp+ssl://smtp.example.org:465',
                           username='myusername', password='secret')
        yield from super().start(ctx)

        yield from ctx.mailer.create_and_deliver(
            subject='Test email', sender='Sender <sender@example.org>',
            to='Recipient <person@example.org>', plain_body='Hello, world!')
        asyncio.get_event_loop().stop()

run_application(MailSenderComponent(), logging=logging.DEBUG)
