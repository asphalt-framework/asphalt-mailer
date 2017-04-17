from asphalt.core.context import Context
import pytest

from asphalt.mailer.api import Mailer
from asphalt.mailer.component import MailerComponent


@pytest.mark.parametrize('backend', ['smtp', 'sendmail'])
@pytest.mark.asyncio
async def test_component_single(caplog, backend):
    component = MailerComponent(backend=backend)
    async with Context() as ctx:
        await component.start(ctx)
        assert isinstance(ctx.mailer, Mailer)

    records = [record for record in caplog.records if record.name == 'asphalt.mailer.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 2
    assert records[0].message.startswith(
        "Configured mailer (default / ctx.mailer; class=%s)" % ctx.mailer.__class__.__name__)
    assert records[1].message.startswith('Mailer (default) stopped')


@pytest.mark.asyncio
async def test_component_multiple(caplog):
    component = MailerComponent(mailers={
        'smtp': {'backend': 'smtp', 'context_attr': 'mailer1'},
        'sendmail': {'backend': 'sendmail', 'context_attr': 'mailer2'}
    })
    async with Context() as ctx:
        await component.start(ctx)
        assert isinstance(ctx.mailer1, Mailer)
        assert isinstance(ctx.mailer2, Mailer)

    records = [record for record in caplog.records if record.name == 'asphalt.mailer.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 4
    assert records[0].message.startswith(
        "Configured mailer (sendmail / ctx.mailer2; class=SendmailMailer)")
    assert records[1].message.startswith(
        "Configured mailer (smtp / ctx.mailer1; class=SMTPMailer)")
    assert records[2].message.startswith('Mailer (sendmail) stopped')
    assert records[3].message.startswith('Mailer (smtp) stopped')
