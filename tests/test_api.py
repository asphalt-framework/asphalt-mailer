from asyncio import coroutine
from email.headerregistry import Address
from email.message import EmailMessage
from typing import Union, Iterable

import pytest

from asphalt.mailer.api import Mailer


class DummyMailer(Mailer):
    def __init__(self):
        super().__init__({})
        self.messages = []

    @coroutine
    def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        messages = [messages] if isinstance(messages, EmailMessage) else messages
        self.messages.extend(messages)


class TestMailer:
    @pytest.fixture
    def kwargs(self):
        return {
            'charset': 'iso-8859-1',
            'plain_body': 'Hello åäö',
            'html_body': '<html><body>Hello åäö</body></html>',
            'to': [Address('Test Recipient', 'test', 'domain.country'), 'test2@domain.country'],
            'cc': [Address('Test CC', 'testcc', 'domain.country'), 'testcc2@domain.country'],
            'bcc': [Address('Test BCC', 'testbcc', 'domain.country'), 'testbcc2@domain.country']
        }

    @pytest.fixture
    def mailer(self):
        return DummyMailer()

    @pytest.mark.parametrize('plain_body, html_body', [
        (True, True), (True, False), (False, True)
    ], ids=['both', 'plain', 'html'])
    def test_create_message(self, mailer, kwargs, plain_body, html_body):
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

    def test_add_attachment(self, mailer):
        msg = mailer.create_message(subject='foo')
        mailer.add_attachment(msg, b'binary content', filename='test.dat')
        attachments = list(msg.iter_attachments())
        assert len(attachments) == 1
        assert attachments[0]['Content-Type'] == 'application/octet-stream'
        assert attachments[0]['Content-Disposition'] == 'attachment; filename="test.dat"'

    def test_add_file_attachment(self, mailer):
        msg = mailer.create_message(subject='foo')
        mailer.add_file_attachment(msg, __file__)
        attachments = list(msg.iter_attachments())
        assert len(attachments) == 1
        assert attachments[0]['Content-Type'] == 'text/x-python'
        assert attachments[0]['Content-Disposition'] == 'attachment; filename="test_api.py"'

    @pytest.mark.asyncio
    def test_create_and_deliver(self, mailer, kwargs):
        yield from mailer.create_and_deliver(subject='test subject', sender='foo@bar.baz',
                                             **kwargs)
        assert len(mailer.messages) == 1
        assert isinstance(mailer.messages[0], EmailMessage)
        assert mailer.messages[0]['From'] == 'foo@bar.baz'
