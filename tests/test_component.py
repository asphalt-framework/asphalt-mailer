from __future__ import annotations

import logging

import pytest
from asphalt.core import Context, qualified_name, require_resource
from pytest import LogCaptureFixture

from asphalt.mailer import Mailer, MailerComponent

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("backend", ["smtp", "sendmail", "mock"])
async def test_component(caplog: LogCaptureFixture, backend: str) -> None:
    caplog.set_level(logging.INFO, logger="asphalt.mailer")
    component = MailerComponent(backend=backend)
    async with Context():
        await component.start()
        mailer = require_resource(Mailer)  # type: ignore[type-abstract]

    records = [record for record in caplog.records if record.name == "asphalt.mailer"]
    records.sort(key=lambda r: r.message)
    assert len(records) == 1
    assert records[0].message == (
        f"Configured mailer (default; class={qualified_name(mailer)})"
    )
