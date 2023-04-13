from __future__ import annotations

import pytest
from asphalt.mailer.mailers.mock import MockMailer

pytestmark = pytest.mark.anyio


@pytest.fixture
def mailer() -> MockMailer:
    return MockMailer()


async def test_deliver(mailer: MockMailer) -> None:
    for body in ("message 1", "message 2"):
        await mailer.create_and_deliver(
            subject="test",
            sender="foobar@example.org",
            to="bar@example.org",
            plain_body=body,
        )

    assert len(mailer.messages) == 2
    assert mailer.messages[0].get_content() == "message 1\n"
    assert mailer.messages[1].get_content() == "message 2\n"


def test_repr(mailer: MockMailer) -> None:
    assert repr(mailer) == "MockMailer()"
