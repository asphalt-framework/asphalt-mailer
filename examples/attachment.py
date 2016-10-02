"""
A simple command line tool that connects to an SMTP server, sends a mail message with an attachment
and then exits.

To run this, you first need to replace the placeholder value for add_component() and
ctx.mailer.create_and_deliver().

The program requires one command line argument, the path to the attachment file.
"""

import logging
import os.path
import sys

from asphalt.core import CLIApplicationComponent, Context, run_application


class ApplicationComponent(CLIApplicationComponent):
    def __init__(self, attachment):
        super().__init__()
        self.attachment = attachment

    async def start(self, ctx: Context):
        self.add_component('mailer', backend='smtp', host='smtp.example.org', ssl=True,
                           username='myusername', password='secret')
        await super().start(ctx)

    async def run(self, ctx: Context):
        message = ctx.mailer.create_message(
            subject='Test email with attachment', sender='Sender <sender@example.org>',
            to='Recipient <person@example.org>', plain_body='Take a look at this file!')
        await ctx.mailer.add_file_attachment(message, self.attachment)
        await ctx.mailer.deliver(message)


if len(sys.argv) < 2:
    print('Specify the path to the attachment as the argument to this script!', file=sys.stderr)
    sys.exit(1)

if not os.path.isfile(sys.argv[1]):
    print('The attachment ({}) does not exist or is not a regular file', file=sys.stderr)
    sys.exit(2)

run_application(ApplicationComponent(sys.argv[1]), logging=logging.DEBUG)
