from __future__ import annotations

import logging

import pytest
from asphalt.core import qualified_name
from asphalt.core.context import Context
from asphalt.mailer.api import Mailer
from asphalt.mailer.component import MailerComponent
from pytest import LogCaptureFixture

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("backend", ["smtp", "sendmail", "mock"])
async def test_component(caplog: LogCaptureFixture, backend: str) -> None:
    caplog.set_level(logging.INFO, logger="asphalt.mailer.component")
    component = MailerComponent(backend=backend)
    async with Context() as ctx:
        await component.start(ctx)
        mailer = ctx.require_resource(Mailer)  # type: ignore[type-abstract]

    records = [
        record for record in caplog.records if record.name == "asphalt.mailer.component"
    ]
    records.sort(key=lambda r: r.message)
    assert len(records) == 1
    assert records[0].message == (
        f"Configured mailer (default; class={qualified_name(mailer)})"
    )
