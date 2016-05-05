"""
A simple command line tool that connects to an SMTP server, sends a mail message and then exits.

To run this, you first need to replace the placeholder value for add_component() and
ctx.mailer.create_and_deliver().
"""

import asyncio
import logging

from asphalt.core import ContainerComponent, Context, run_application


class ApplicationComponent(ContainerComponent):
    async def start(self, ctx: Context):
        self.add_component('mailer', backend='smtp', host='smtp.example.org', ssl=True,
                           username='myusername', password='secret')
        await super().start(ctx)

        await ctx.mailer.create_and_deliver(
            subject='Test email', sender='Sender <sender@example.org>',
            to='Recipient <person@example.org>', plain_body='Hello, world!')
        asyncio.get_event_loop().stop()

run_application(ApplicationComponent(), logging=logging.DEBUG)
