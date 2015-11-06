from asphalt.core.context import Context
import pytest

from asphalt.mailer.api import Mailer
from asphalt.mailer.component import MailerComponent


@pytest.mark.parametrize('backend', ['smtp', 'sendmail'])
@pytest.mark.asyncio
def test_component_single(caplog, backend):
    component = MailerComponent(backend=backend)
    context = Context()
    yield from component.start(context)

    assert isinstance(context.mailer, Mailer)
    records = [record for record in caplog.records() if record.name == 'asphalt.mailer.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 1
    assert records[0].message.startswith("Configured mailer (default / ctx.mailer)")


@pytest.mark.asyncio
def test_component_multiple(caplog):
    component = MailerComponent(mailers={
        'smtp': {'backend': 'smtp', 'context_attr': 'mailer1'},
        'sendmail': {'backend': 'sendmail', 'context_attr': 'mailer2'}
    })
    context = Context()
    yield from component.start(context)

    assert isinstance(context.mailer1, Mailer)
    assert isinstance(context.mailer2, Mailer)
    records = [record for record in caplog.records() if record.name == 'asphalt.mailer.component']
    records.sort(key=lambda r: r.message)
    assert len(records) == 2
    assert records[0].message.startswith("Configured mailer (sendmail / ctx.mailer2)")
    assert records[1].message.startswith("Configured mailer (smtp / ctx.mailer1)")


def test_component_conflicting_config():
    exc = pytest.raises(ValueError, MailerComponent, mailers={'default': {}}, backend='smtp')
    assert str(exc.value) == ('specify either a "mailers" dictionary or the default mailer\'s '
                              'options directly, but not both')
