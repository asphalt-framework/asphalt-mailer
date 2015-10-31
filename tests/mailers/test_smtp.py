from asyncio import coroutine, start_server
from asyncio.tasks import Task, gather, wait_for
from functools import partial
import re

from asphalt.core.context import Context
import pytest

from asphalt.mailer.api import DeliveryError
from asphalt.mailer.mailers.smtp import SMTPMailer, SMTPError
from tests.mailers.conftest import recipients


class MockSMTPServer:
    def __init__(self, reader, writer, auth_mechanism, fail_on):
        self.reader = reader
        self.writer = writer
        self.auth_mechanism = auth_mechanism
        self.fail_on = fail_on
        self.features = ['8BITMIME', 'PIPELINING']
        if auth_mechanism:
            self.features.append('AUTH %s FOO BAR BAZ' % auth_mechanism)

    @coroutine
    def readline(self):
        read_task = self.reader.readline()
        line = yield from wait_for(read_task, 1)
        return line.decode().rstrip()

    @coroutine
    def expect(self, pattern: str):
        command = yield from self.readline()
        match = re.match(pattern, command)
        if not match:
            raise ValueError('Unexpected command: "{}" did not match "{}"'.
                             format(command, pattern))
        groups = match.groups()
        return groups[0] if len(groups) == 1 else groups

    def respond(self, code: int, *lines):
        lines = list(lines)
        for i, line in enumerate(lines):
            separator = '-' if i < (len(lines) - 1) else ' '
            lines[i] = str(code) + separator + line

        output = '\r\n'.join(line for line in lines).encode() + b'\r\n'
        self.writer.write(output)

    @classmethod
    def connected(cls, reader, writer, auth_mechanism, fail_on):
        server = cls(reader, writer, auth_mechanism, fail_on)
        return server.protocol()

    @coroutine
    def protocol(self):
        if self.fail_on == 'handshake':
            self.writer.close()
            return
        elif self.fail_on == 'protocol':
            self.writer.write(b'blablabla\r\n')
            yield from self.writer.drain()
            return
        else:
            self.respond(200, 'fake SMTP server')

        yield from self.expect('EHLO \w+')
        self.respond(250, 'fake SMTP server', *self.features)

        if self.auth_mechanism == 'LOGIN':
            login, password = yield from self.expect('AUTH LOGIN (\w+) (\w+)')
            assert login == 'testuser' and password == 'testpass'
        elif self.auth_mechanism == 'PLAIN':
            token = yield from self.expect('AUTH PLAIN (\w+)')
            assert token == 'AHRlc3R1c2VyAHRlc3RwYXNz'
        else:
            yield from self.expect('QUIT')
            return

        if self.fail_on == 'auth':
            self.respond(535, 'Authentication failed')
            yield from self.expect('QUIT')
            return
        else:
            self.respond(235, 'Accepted')

        sender = yield from self.expect('MAIL FROM: <(.+)>')
        assert sender == 'foo@bar.baz'

        for recipient in recipients():
            actual = yield from self.expect('RCPT TO: <(.+)>')
            assert actual == recipient

        yield from self.expect('DATA')
        if self.fail_on == 'delivery':
            self.respond(550, 'Rejected')
            return

        self.respond(250, '2.1.0 MAIL ok')
        for recipient in recipients():
            self.respond(250, '2.1.5 <{}> ok'.format(recipient))
        self.respond(354, 'Enter mail, end with "." on a line by itself')

        message = []
        while True:
            line = yield from self.readline()
            if line == '.':
                break
            else:
                message.append(line)

        self.respond(250, '2.6.0 message received')

        yield from self.expect('QUIT')
        self.respond(221, '2.0.0 goodbye')


@pytest.yield_fixture
def mailer(event_loop, unused_tcp_port, request):
    auth_mechanism, fail_on = request.param
    callback = partial(MockSMTPServer.connected, auth_mechanism=auth_mechanism,
                       fail_on=fail_on)
    task = start_server(callback, '127.0.0.1', unused_tcp_port)
    server = event_loop.run_until_complete(task)
    mailer = SMTPMailer(connector='127.0.0.1:{}'.format(unused_tcp_port), username='testuser',
                        password='testpass', timeout=1)
    event_loop.run_until_complete(mailer.start(Context()))
    yield mailer
    server.close()
    tasks = Task.all_tasks(event_loop)
    event_loop.run_until_complete(gather(*tasks))


@pytest.mark.parametrize('mailer', [('LOGIN', None), ('PLAIN', None)], indirect=True)
@pytest.mark.asyncio
def test_deliver(mailer, sample_message):
    yield from mailer.deliver(sample_message)


@pytest.mark.parametrize('mailer', [(None, None), ('BOGUS', None)], indirect=True)
@pytest.mark.asyncio
def test_deliver_noauth(mailer, sample_message):
    with pytest.raises(DeliveryError) as exc:
        yield from mailer.deliver(sample_message)

    assert str(exc.value) == ('error sending mail message: server does not support any '
                              'of our authentication methods')


@pytest.mark.parametrize('mailer', [('LOGIN', 'auth')], indirect=True)
@pytest.mark.asyncio
def test_deliver_auth_error(mailer, sample_message):
    with pytest.raises(DeliveryError) as exc:
        yield from mailer.deliver(sample_message)

    assert str(exc.value) == ('error sending mail message: server returned error: '
                              '535 Authentication failed')


@pytest.mark.parametrize('mailer', [('LOGIN', 'handshake')], indirect=True)
@pytest.mark.asyncio
def test_deliver_handshake_error(mailer, sample_message):
    with pytest.raises(DeliveryError) as exc:
        yield from mailer.deliver(sample_message)

    assert str(exc.value) == 'error sending mail message: server closed connection'


@pytest.mark.parametrize('mailer', [('LOGIN', 'protocol')], indirect=True)
@pytest.mark.asyncio
def test_deliver_protocol_error(mailer, sample_message):
    with pytest.raises(DeliveryError) as exc:
        yield from mailer.deliver(sample_message)

    assert str(exc.value) == ('error sending mail message: SMTP protocol error: '
                              'received unexpected response: blablabla')


@pytest.mark.parametrize('mailer', [('LOGIN', 'delivery')], indirect=True)
@pytest.mark.asyncio
def test_deliver_delivery_error(mailer, sample_message):
    with pytest.raises(SMTPError) as exc:
        yield from mailer.deliver(sample_message)

    assert exc.value.code == 550
    assert exc.value.message is sample_message
    # assert str(exc.value) == ('error sending mail message: SMTP protocol error: '
    #                           'received unexpected response: blablabla')


@pytest.mark.parametrize('mailer', [('LOGIN', None)], indirect=True)
def test_repr(mailer):
    assert repr(mailer).startswith("SMTPMailer('tcp://127.0.0.1:")
