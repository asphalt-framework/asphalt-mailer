from email.headerregistry import Address

from asphalt.core import inject, resource

from asphalt.mailer import Mailer


@inject
async def handler(*, mailer: Mailer = resource()) -> None:
    messages = []
    for recipient in [
        Address("Some Person", "some.person", "company.com"),
        Address("Other Person", "other.person", "company.com"),
    ]:
        message = mailer.create_message(
            subject=f"Hi there, {recipient.display_name}!",
            sender="Example Person <example@company.com>",
            to=recipient,
            plain_body=f"How are you doing, {recipient.display_name}?",
        )
        messages.append(message)

    await mailer.deliver(messages)
