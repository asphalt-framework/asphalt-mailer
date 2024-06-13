from asphalt.core import inject, resource

from asphalt.mailer import Mailer


@inject
async def handler(*, mailer: Mailer = resource()) -> None:
    message = mailer.create_message(
        subject="Hi there!",
        sender="Example Person <example@company.com>",
        to="recipient@company.com",
        plain_body="See the attached file.",
    )
    mailer.add_attachment(message, b"file contents", "attachment.txt")
    await mailer.deliver(message)
