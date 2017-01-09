import platform
import re
from asyncio.streams import StreamWriter, StreamReader, open_connection
from asyncio.tasks import wait_for
from base64 import b64encode
from email.message import EmailMessage
from email.policy import SMTP
from ssl import SSLContext
from typing import Iterable, Union, Dict, Any

from asyncio_extras.asyncyield import yield_async
from asyncio_extras.contextmanager import async_contextmanager
from typeguard import check_argument_types

from asphalt.core.context import Context
from asphalt.core.util import resolve_reference
from asphalt.mailer.api import Mailer, DeliveryError
from asphalt.mailer.util import get_recipients

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

    @classmethod
    @async_contextmanager
    async def connect(cls, host, port, ssl, timeout):
        reader, writer = await wait_for(open_connection(host, port, ssl=ssl), timeout)
        connection = cls(reader, writer, timeout)
        await yield_async(connection)
        writer.close()

    async def command(self, command: str, *args: str, expect_response: bool=True):
        # Send the command
        data = ' '.join((command,) + args).encode('ascii') + b'\r\n'
        self.write(data)
        if expect_response:
            return await self.get_response()

    async def get_response(self):
        lines = []
        while True:
            read_task = self.reader.readline()
            line = await wait_for(read_task, self.timeout)
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

    Supports only unencrypted or implicit TLS connections. STARTTLS is not supported yet.

    :param host: the host name or IP address of the SMTP server to connect to
    :param port: the port number to connect to (omit to autodetect based on the ``ssl`` parameter)
    :param ssl: one of the following:

        * ``False`` to disable SSL
        * ``True`` to enable SSL using the default context
        * an :class:`ssl.SSLContext` instance
        * a ``module:varname`` reference to an :class:`~ssl.SSLContext` instance
        * name of an :class:`ssl.SSLContext` resource
    :param username: user name to authenticate as
    :param password: password to authenticate with
    :param timeout: timeout (in seconds) for connect and read operations
    :param message_defaults: default values for omitted keyword arguments of
        :meth:`~asphalt.mailer.api.Mailer.create_message`
    """

    __slots__ = 'host', 'port', 'ssl', 'username', 'password', 'timeout'

    period_re = re.compile(b'^\.', re.MULTILINE)

    def __init__(self, *, host: str = '127.0.0.1', port: int = None,
                 ssl: Union[bool, str, SSLContext] = False, username: str = None,
                 password: str = None, timeout: Union[int, float] = 10,
                 message_defaults: Dict[str, Any] = None):
        assert check_argument_types()
        super().__init__(message_defaults)
        self.host = host
        self.ssl = resolve_reference(ssl)
        self.port = port or ('465' if self.ssl else '25')
        self.username = username
        self.password = password
        self.timeout = timeout

    async def start(self, ctx: Context):
        if isinstance(self.ssl, str):
            self.ssl = await ctx.request_resource(SSLContext, self.ssl)

    async def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        assert check_argument_types()
        if isinstance(messages, EmailMessage):
            messages = [messages]

        async with SMTPConnection.connect(self.host, self.port, self.ssl,
                                          self.timeout) as connection:
            await connection.get_response()
            response = await connection.command('EHLO', platform.node())
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
                        await connection.command('AUTH PLAIN', token.decode())
                    elif 'LOGIN' in auth_mechanisms:
                        await connection.command('AUTH LOGIN', self.username, self.password)
                    else:
                        raise DeliveryError('server does not support any of our authentication '
                                            'methods')

                # Send each message in a separate mail transaction
                for message in messages:
                    try:
                        recipients = get_recipients(message)
                        await connection.command(
                            'MAIL FROM: <{}>'.format(message['From'].addresses[0].addr_spec),
                            expect_response=not pipelining)
                        for recipient in recipients:
                            await connection.command('RCPT TO: <{}>'.format(recipient),
                                                     expect_response=not pipelining)

                        await connection.command('DATA', expect_response=not pipelining)

                        # If pipelining was in use, the responses to the MAIL, RCPT and DATA
                        # commands will be sent by the server now
                        if pipelining:
                            for _ in range(2 + len(recipients)):
                                await connection.get_response()

                        envelope = message.as_bytes(policy=policy)
                        envelope = self.period_re.sub(b'..', envelope)
                        connection.write(envelope + b'\r\n')
                        await connection.command('.')
                    except DeliveryError as e:
                        e.message = message
                        raise
            except DeliveryError:
                await connection.command('QUIT', expect_response=False)
                raise
            else:
                await connection.command('QUIT', expect_response=False)

    def __repr__(self):
        return '{self.__class__.__name__}(host={self.host!r}, port={self.port!r})'.\
            format(self=self)
