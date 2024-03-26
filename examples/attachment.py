"""
A simple command line tool that connects to an SMTP server, sends a mail message with an
attachment and then exits.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

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
        attachment: Path,
    ):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.sender = sender
        self.to = to
        self.subject = subject
        self.attachment = attachment

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
        message = mailer.create_message(
            subject=self.subject,
            sender=self.sender,
            to=self.to,
            plain_body="Take a look at this file!",
        )
        await mailer.add_file_attachment(message, self.attachment)
        await mailer.deliver(message)


@click.command()
@click.option("-h", "--host", required=True, help="SMTP server host name")
@click.option("-u", "--username", help="username for authenticating with SMTP server")
@click.option("-p", "--password", help="password for authenticating with SMTP server")
@click.option("-f", "--from", "sender", required=True, help="Sender email address")
@click.option("-t", "--to", required=True, help="Recipient email address")
@click.option("-s", "--subject", default="Test email with attachment")
@click.argument("attachment", type=click.Path(exists=True))
def main(
    host: str,
    username: str | None,
    password: str | None,
    sender: str,
    to: str,
    subject: str,
    attachment: Path,
) -> None:
    component = ApplicationComponent(
        host, username, password, sender, to, subject, attachment
    )
    asyncio.run(run_application(component, logging=logging.INFO))


main()
