from asyncio import coroutine
from asyncio.streams import StreamWriter, StreamReader
from asyncio.tasks import wait_for
from typing import Iterable, Union, Dict, Any
from base64 import b64encode
from email.message import EmailMessage
from email.policy import SMTP
import platform
import re

from typeguard import check_argument_types
from asphalt.core.connectors import Connector, create_connector
from asphalt.core.context import Context
from asphalt.core.concurrency import asynchronous

from ..api import Mailer, DeliveryError
from ..util import get_recipients

__all__ = 'SMTPError', 'SMTPMailer'


class SMTPError(DeliveryError):
    """
    Raised when the SMTP server returns a response with a code of 400 or greater.

    :param code: the numeric response code
    :param error: the error message from the server
    """

    def __init__(self, code: int, error: str):
        super().__init__('server returned error: {} {}'.format(code, error))
        self.code = code
        self.error = error


class SMTPConnection:
    __slots__ = 'reader', 'writer', 'timeout'

    response_re = re.compile(r'(\d{3})(-| )(.*)')

    def __init__(self, reader: StreamReader, writer: StreamWriter, timeout: int):
        self.reader = reader
        self.writer = writer
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.writer.close()

    @classmethod
    @coroutine
    def create(cls, connector: Connector, timeout: int):
        reader, writer = yield from connector.connect()
        return cls(reader, writer, timeout)

    @coroutine
    def command(self, command: str, *args: str, expect_response: bool=True):
        # Send the command
        data = ' '.join((command,) + args).encode('ascii') + b'\r\n'
        self.write(data)
        if expect_response:
            return (yield from self.get_response())

    @coroutine
    def get_response(self):
        lines = []
        while True:
            read_task = self.reader.readline()
            line = yield from wait_for(read_task, self.timeout)
            if not line.endswith(b'\r\n'):
                raise DeliveryError('server closed connection')

            line = line.decode(errors='replace').rstrip()
            match = self.response_re.match(line)
            if not match:
                raise DeliveryError('SMTP protocol error: received unexpected response: {}'.
                                    format(line))

            code, separator, message = match.groups()
            lines.append(message)
            if separator == ' ':
                code = int(code)
                response = '\n'.join(lines)
                if code >= 400:
                    raise SMTPError(code, response)
                return response

    def write(self, data: bytes):
        self.writer.write(data)


class SMTPMailer(Mailer):
    """
    A mailer that uses the ESMTP protocol (:rfc:`2821`) to send mails.

    Supports only unencrypted or implicit TLS connections.
    STARTTLS is not supported yet.
    Connects to port 25 on ``127.0.0.1`` by default.

    If you don't know what SMTP server address to use, your Internet
    service provider should have provided you their SMTP server address
    when you signed up.

    :param connector: a connector instance or endpoint for
                      :func:`~asphalt.core.connectors.create_connector`
    :param username: user name to authenticate as
    :param password: password to authenticate with
    :param timeout: timeout (in seconds) for connect and read operations
    :param defaults: default values for omitted keyword arguments of
                     :meth:`~asphalt.mailer.api.Mailer.create_message`
    """

    __slots__ = 'connector', 'username', 'password', 'timeout'

    def __init__(self, *, connector: Union[str, Connector]='tcp://127.0.0.1', username: str=None,
                 password: str=None, timeout: Union[int, float]=10, defaults: Dict[str, Any]=None):
        assert check_argument_types()
        super().__init__(defaults)
        self.connector = connector
        self.username = username
        self.password = password
        self.timeout = timeout

    @coroutine
    def start(self, ctx: Context):
        if not isinstance(self.connector, Connector):
            defaults = {'port': 25, 'timeout': self.timeout}
            self.connector = yield from create_connector(self.connector, defaults, ctx)

    @asynchronous
    def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        assert check_argument_types()
        if isinstance(messages, EmailMessage):
            messages = [messages]

        with (yield from SMTPConnection.create(self.connector, self.timeout)) as connection:
            yield from connection.get_response()
            response = yield from connection.command('EHLO', platform.node())
            features = response.split('\n')[1:]
            policy = SMTP.clone(cte_type='8bit' if '8BITMIME' in features else '7bit')
            pipelining = 'PIPELINING' in features

            try:
                # Authenticate if necessary
                if self.username and self.password:
                    auth_mechanisms = []
                    for feature in features:
                        if feature.startswith('AUTH '):
                            auth_mechanisms = feature[5:].split()
                            break

                    if 'PLAIN' in auth_mechanisms:
                        token = b64encode('\0{}\0{}'.format(self.username, self.password).encode())
                        yield from connection.command('AUTH PLAIN', token.decode())
                    elif 'LOGIN' in auth_mechanisms:
                        yield from connection.command('AUTH LOGIN', self.username, self.password)
                    else:
                        raise DeliveryError('server does not support any of our authentication '
                                            'methods')

                # Send each message in a separate mail transaction
                for message in messages:
                    try:
                        recipients = get_recipients(message)
                        yield from connection.command(
                            'MAIL FROM: <{}>'.format(message['From'].addresses[0].addr_spec),
                            expect_response=not pipelining)
                        for recipient in recipients:
                            yield from connection.command('RCPT TO: <{}>'.format(recipient),
                                                          expect_response=not pipelining)

                        yield from connection.command('DATA', expect_response=not pipelining)

                        # If pipelining was in use, the responses to the MAIL, RCPT and DATA
                        # commands will be sent by the server now
                        if pipelining:
                            for _ in range(2 + len(recipients)):
                                yield from connection.get_response()

                        envelope = message.as_bytes(policy=policy)
                        connection.write(envelope + b'\r\n')
                        yield from connection.command('.')
                    except DeliveryError as e:
                        e.message = message
                        raise
            except DeliveryError:
                yield from connection.command('QUIT', expect_response=False)
                raise
            else:
                yield from connection.command('QUIT', expect_response=False)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, str(self.connector))
