"""
A simple command line tool that connects to an SMTP server, sends a mail message and
then exits.
"""

from __future__ import annotations

import logging

# isort: off
import click
from asphalt.core import CLIApplicationComponent, get_resource_nowait, run_application
from asphalt.mailer import Mailer


class ApplicationComponent(CLIApplicationComponent):
    def __init__(
        self,
        host: str,
        username: str | None,
        password: str | None,
        sender: str,
        to: str,
        subject: str,
        body: str,
    ):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.sender = sender
        self.to = to
        self.subject = subject
        self.body = body

    async def start(self) -> None:
        self.add_component(
            "mailer",
            backend="smtp",
            host=self.host,
            username=self.username,
            password=self.password,
        )
        await super().start()

    async def run(self) -> None:
        mailer = get_resource_nowait(Mailer)  # type: ignore[type-abstract]
        await mailer.create_and_deliver(
            subject=self.subject, sender=self.sender, to=self.to, plain_body=self.body
        )


@click.command()
@click.option("-h", "--host", required=True, help="SMTP server host name")
@click.option("-u", "--username", help="username for authenticating with SMTP server")
@click.option("-p", "--password", help="password for authenticating with SMTP server")
@click.option("-f", "--from", "sender", required=True, help="Sender email address")
@click.option("-t", "--to", required=True, help="Recipient email address")
@click.option("-s", "--subject", default="Test email")
@click.argument("body")
def main(
    host: str,
    username: str | None,
    password: str | None,
    sender: str,
    to: str,
    subject: str,
    body: str,
) -> None:
    config = {
        "host": host,
        "username": username,
        "password": password,
        "sender": sender,
        "to": to,
        "subject": subject,
        "body": body,
    }
    run_application(ApplicationComponent, config, logging=logging.INFO)


main()
