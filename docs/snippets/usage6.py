from asphalt.core import inject, resource

from asphalt.mailer import DeliveryError, Mailer


@inject
async def handler(*, mailer: Mailer = resource()) -> None:
    try:
        await mailer.create_and_deliver(
            subject="Hi there!",
            sender="Example Person <example@company.com>",
            to="recipient@company.com",
            plain_body="Greetings from Example!",
        )
    except DeliveryError as exc:
        if exc.message:
            print(f"Delivery to {exc.message['To']} failed: {exc}")
        else:
            print(f"Delivery failed: {exc}")
