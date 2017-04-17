"""
A simple command line tool that connects to an SMTP server, sends a mail message with an attachment
and then exits.
"""

import logging

import click
from asphalt.core import CLIApplicationComponent, Context, run_application


class ApplicationComponent(CLIApplicationComponent):
    def __init__(self, host, username, password, sender, to, subject, attachment):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.sender = sender
        self.to = to
        self.subject = subject
        self.attachment = attachment

    async def start(self, ctx: Context):
        self.add_component('mailer', backend='smtp', host=self.host, username=self.username,
                           password=self.password)
        await super().start(ctx)

    async def run(self, ctx: Context):
        message = ctx.mailer.create_message(
            subject=self.subject, sender=self.sender, to=self.to,
            plain_body='Take a look at this file!')
        await ctx.mailer.add_file_attachment(message, self.attachment)
        await ctx.mailer.deliver(message)


@click.command()
@click.option('-h', '--host', required=True, help='SMTP server host name')
@click.option('-u', '--username', help='username for authenticating with SMTP server')
@click.option('-p', '--password', help='password for authenticating with SMTP server')
@click.option('-f', '--from', 'sender', required=True, help='Sender email address')
@click.option('-t', '--to', required=True, help='Recipient email address')
@click.option('-s', '--subject', default='Test email with attachment')
@click.argument('attachment', type=click.Path(exists=True))
def main(host, username, password, sender, to, subject, attachment):
    component = ApplicationComponent(host, username, password, sender, to, subject, attachment)
    run_application(component, logging=logging.INFO)

main()
