from typing import cast

import pytest
from asphalt.core import Context, get_resource_nowait, start_component

from asphalt.mailer import Mailer, MailerComponent
from asphalt.mailer.mailers.mock import MockMailer

pytestmark = pytest.mark.anyio


async def test_foo() -> None:
    async with Context():
        await start_component(MailerComponent, {"backend": "mock"})
        mailer = cast(MockMailer, get_resource_nowait(Mailer))  # type: ignore[type-abstract]
        await mailer.create_and_deliver(to="intended.recipient@example.org")

    # check that exactly one message was sent, to intended.recipient@example.org
    assert len(mailer.messages) == 1
    assert mailer.messages[0]["To"] == "intended.recipient@example.org"
