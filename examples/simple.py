"""
A simple command line tool that connects to an SMTP server, sends a mail message and then exits.

To run this, you first need to replace the placeholder value for add_component() and
ctx.mailer.create_and_deliver().
"""

import logging

from asphalt.core import CLIApplicationComponent, Context, run_application


class ApplicationComponent(CLIApplicationComponent):
    async def start(self, ctx: Context):
        self.add_component('mailer', backend='smtp', host='smtp.example.org', ssl=True,
                           username='myusername', password='secret')
        await super().start(ctx)

    async def run(self, ctx: Context):
        await ctx.mailer.create_and_deliver(
            subject='Test email', sender='Sender <sender@example.org>',
            to='Recipient <person@example.org>', plain_body='Hello, world!')


run_application(ApplicationComponent(), logging=logging.DEBUG)
