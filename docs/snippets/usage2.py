from asphalt.core import inject, resource

from asphalt.mailer import Mailer


@inject
async def handler(*, mailer: Mailer = resource()) -> None:
    html = "<h1>Greetings</h1>Greetings from <strong>Example Person!</strong>"
    plain = "Greetings!\n\nGreetings from Example Person!"
    await mailer.create_and_deliver(
        subject="Hi there!",
        sender="Example Person <example@company.com>",
        to="recipient@company.com",
        plain_body=plain,
        html_body=html,
    )
