from email.headerregistry import Address
from email.message import EmailMessage
from typing import Union, Iterable

import pytest

from asphalt.mailer.api import Mailer


class DummyMailer(Mailer):
    def __init__(self, **message_defaults):
        super().__init__(message_defaults)
        self.messages = []

    async def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        messages = [messages] if isinstance(messages, EmailMessage) else messages
        self.messages.extend(messages)


@pytest.fixture
def kwargs():
    return {
        'charset': 'iso-8859-1',
        'plain_body': 'Hello åäö',
        'html_body': '<html><body>Hello åäö</body></html>',
        'to': [Address('Test Recipient', 'test', 'domain.country'), 'test2@domain.country'],
        'cc': [Address('Test CC', 'testcc', 'domain.country'), 'testcc2@domain.country'],
        'bcc': [Address('Test BCC', 'testbcc', 'domain.country'), 'testbcc2@domain.country']
    }


@pytest.fixture
def mailer():
    return DummyMailer()


@pytest.mark.parametrize('plain_body, html_body', [
    (True, True), (True, False), (False, True)
], ids=['both', 'plain', 'html'])
def test_create_message(mailer, kwargs, plain_body, html_body):
    if not plain_body:
        del kwargs['plain_body']
    if not html_body:
        del kwargs['html_body']
    msg = mailer.create_message(subject='test subject', sender='foo@bar.baz', **kwargs)

    assert msg['From'] == 'foo@bar.baz'
    assert msg['Subject'] == 'test subject'
    assert msg['To'] == 'Test Recipient <test@domain.country>, test2@domain.country'
    assert msg['Cc'] == 'Test CC <testcc@domain.country>, testcc2@domain.country'
    assert msg['Bcc'] == 'Test BCC <testbcc@domain.country>, testbcc2@domain.country'

    if plain_body and html_body:
        assert msg['Content-Type'] == 'multipart/alternative'
        plain_part, html_part = msg.iter_parts()
    elif plain_body:
        plain_part, html_part = msg, None
    else:
        plain_part, html_part = None, msg

    if plain_part:
        assert plain_part['Content-Type'] == 'text/plain; charset="iso-8859-1"'
        assert plain_part.get_content() == 'Hello åäö\n'
    if html_part:
        assert html_part['Content-Type'] == 'text/html; charset="iso-8859-1"'
        assert html_part.get_content() == '<html><body>Hello åäö</body></html>\n'


def test_message_defaults():
    """
    Test that message defaults are applied when the corresponding arguments have been omitted.

    """
    mailer = DummyMailer(subject='default_subject', sender='default_sender@example.org',
                         to='default_recipient@example.org', cc='default_cc@example.org',
                         bcc='default_bcc@example.org', charset='utf-16')
    msg = mailer.create_message(plain_body='Hello åäö')
    assert msg['Subject'] == 'default_subject'
    assert msg['From'] == 'default_sender@example.org'
    assert msg['To'] == 'default_recipient@example.org'
    assert msg['Cc'] == 'default_cc@example.org'
    assert msg['Bcc'] == 'default_bcc@example.org'
    assert msg.get_charsets() == ['utf-16']


def test_add_attachment(mailer):
    msg = mailer.create_message(subject='foo')
    mailer.add_attachment(msg, b'binary content', filename='test')
    attachments = list(msg.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0]['Content-Type'] == 'application/octet-stream'
    assert attachments[0]['Content-Disposition'] == 'attachment; filename="test"'


@pytest.mark.asyncio
async def test_add_file_attachment(mailer):
    msg = mailer.create_message(subject='foo')
    await mailer.add_file_attachment(msg, __file__)
    attachments = list(msg.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0]['Content-Type'] == 'text/x-python'
    assert attachments[0]['Content-Disposition'] == 'attachment; filename="test_api.py"'


def test_add_attachment_bad_mime_type(mailer):
    msg = mailer.create_message(subject='foo')
    exc = pytest.raises(ValueError, mailer.add_attachment, msg, b'abc', 'file.dat', '/badtype')
    assert str(exc.value) == 'mimetype must be a string in the "maintype/subtype" format'


@pytest.mark.asyncio
async def test_create_and_deliver(mailer, kwargs):
    await mailer.create_and_deliver(subject='test subject', sender='foo@bar.baz', **kwargs)
    assert len(mailer.messages) == 1
    assert isinstance(mailer.messages[0], EmailMessage)
    assert mailer.messages[0]['From'] == 'foo@bar.baz'
