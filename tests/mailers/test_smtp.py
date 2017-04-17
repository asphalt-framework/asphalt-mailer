import ssl
from asyncio import Task
from base64 import b64decode
from contextlib import suppress
from pathlib import Path
from types import MethodType

import pytest
from aiosmtpd.handlers import Message
from aiosmtpd.smtp import SMTP
from asphalt.core.context import Context

from asphalt.mailer.api import DeliveryError
from asphalt.mailer.mailers.smtp import SMTPMailer


@pytest.fixture
def handler():
    class MessageHandler(Message):
        def __init__(self, message_class=None):
            super().__init__(message_class)
            self.messages = []

        def handle_message(self, message):
            self.messages.append(message)

    return MessageHandler()


@pytest.fixture(scope='module')
def client_tls_context():
    cert_path = Path(__file__).with_name('server.cert')
    return ssl.create_default_context(cafile=str(cert_path))


@pytest.fixture(scope='module')
def server_tls_context():
    key_path = Path(__file__).with_name('server.key')
    cert_path = Path(__file__).with_name('server.cert')
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(str(cert_path), str(key_path))
    return ctx


@pytest.fixture(params=[False, True])
def tls(request):
    return request.param


@pytest.fixture
def smtp_server(event_loop, unused_tcp_port, handler, server_tls_context, tls):
    smtp = SMTP(handler, require_starttls=tls, tls_context=server_tls_context)
    server = event_loop.run_until_complete(
        event_loop.create_server(lambda: smtp, port=unused_tcp_port))
    yield smtp
    server.close()
    event_loop.run_until_complete(server.wait_closed())

    # The server leaves tasks running so wait until they're done
    tasks = Task.all_tasks(event_loop)
    for task in tasks:
        with suppress(Exception):
            event_loop.run_until_complete(task)


@pytest.fixture
def mailer(event_loop, unused_tcp_port, client_tls_context, smtp_server, tls):
    mailer = SMTPMailer(port=unused_tcp_port, timeout=1, tls=tls, tls_context=client_tls_context)
    with Context() as ctx:
        event_loop.run_until_complete(mailer.start(ctx))
        yield mailer


@pytest.mark.parametrize('username, password, tls, expected_port', [
    ('foo', 'bar', True, 587),
    ('foo', 'bar', None, 587),
    ('foo', 'bar', False, 25),
    ('foo', None, None, 25)
], ids=['forcetls', 'autotls', 'disabletls', 'nopassword'])
def test_port_selection(username, password, tls, expected_port):
    mailer = SMTPMailer(username=username, password=password, tls=tls)
    assert mailer.port == expected_port


@pytest.mark.asyncio
async def test_resources():
    mailer = SMTPMailer(tls_context='contextresource')
    context = Context()
    sslcontext = ssl.create_default_context()
    context.add_resource(sslcontext, 'contextresource')
    await mailer.start(context)
    assert mailer.tls_context is sslcontext


@pytest.mark.asyncio
async def test_deliver(mailer, sample_message, handler):
    await mailer.deliver(sample_message)
    assert len(handler.messages) == 1
    received_message = handler.messages[0]

    headers = dict(received_message.items())
    del headers['X-Peer']
    assert headers == {
        'From': 'foo@bar.baz',
        'To': 'Test Recipient <test@domain.country>, test2@domain.country',
        'Cc': 'Test CC <testcc@domain.country>, testcc2@domain.country',
        'Content-Type': 'text/plain; charset="utf-8"',
        'Content-Transfer-Encoding': '7bit',
        'MIME-Version': '1.0',
        'X-MailFrom': 'foo@bar.baz',
        'X-RcptTo': ('test@domain.country, test2@domain.country, testcc@domain.country, '
                     'testcc2@domain.country, testbcc@domain.country, testbcc2@domain.country')
    }
    assert received_message.get_payload() == 'Test content'


@pytest.mark.asyncio
async def test_deliver_auth(mailer, sample_message, smtp_server, handler):
    """Test that authentication works."""
    async def handle_EHLO(self, smtp, session, envelope, hostname):
        session.host_name = hostname
        return '250 AUTH PLAIN'

    async def smtp_AUTH(self, arg):
        method, credentials = arg.split(' ')
        credentials = b64decode(credentials)
        if method == 'PLAIN' and credentials == b'\x00foo\x00bar':
            await self.push('235 2.7.0 Authentication successful')
        else:
            await self.push('535 5.7.8 Authentication credentials invalid')

    handler.handle_EHLO = MethodType(handle_EHLO, handler)
    smtp_server.smtp_AUTH = MethodType(smtp_AUTH, smtp_server)
    mailer.username = 'foo'
    mailer.password = 'bar'
    await mailer.deliver(sample_message)


@pytest.mark.asyncio
async def test_deliver_connect_error(mailer, sample_message, unused_tcp_port):
    mailer._smtp.port = unused_tcp_port + 1
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    exc.match('Error connecting to localhost on port %d' % mailer._smtp.port)


@pytest.mark.asyncio
async def test_deliver_error(mailer, sample_message, smtp_server):
    """Test that SMTP errors during message delivery get converted into DeliveryErrors."""
    async def smtp_DATA(self, arg):
        await self.push('503 Error: foo')

    smtp_server.smtp_DATA = MethodType(smtp_DATA, smtp_server)
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    exc.match('Error: foo')


def test_repr(mailer, unused_tcp_port):
    assert repr(mailer) == "SMTPMailer(host='localhost', port=%d)" % unused_tcp_port
