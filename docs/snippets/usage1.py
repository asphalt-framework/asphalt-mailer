from asphalt.core import inject, resource

from asphalt.mailer import Mailer


@inject
async def handler(*, mailer: Mailer = resource()) -> None:
    await mailer.create_and_deliver(
        subject="Hi there!",
        sender="Example Person <example@company.com>",
        to="recipient@company.com",
        plain_body="Greetings from Example!",
    )
