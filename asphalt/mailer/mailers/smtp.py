from asyncio import coroutine
from asyncio.events import AbstractEventLoop
from asyncio.locks import BoundedSemaphore
from asyncio.streams import open_connection, StreamWriter, StreamReader
from ssl import SSLContext
from base64 import b64encode
from email.message import EmailMessage
from email.policy import SMTP
from hmac import HMAC
from typing import Iterable, Union, List
import platform

from asphalt.core.util import asynchronous

from .base import BaseMailer
from ..exc import DeliveryError


class SMTPError(DeliveryError):
    def __init__(self, code: int, error: str):
        super().__init__(error)
        self.code = code


class SMTPConnection:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

    @classmethod
    def create(cls, event_loop: AbstractEventLoop, host: str, port: int):
        reader, writer = yield from open_connection(host, port, loop=event_loop)
        return cls(reader, writer)

    @coroutine
    def command(self, command: str):
        # Send the command
        yield from self.write(command)

        # Read the response
        lines = []
        while True:
            line = yield from self.reader.readline()
            line = line.decode()
            lines.append(line[4:])
            if line[3] == ' ':
                code = int(line[:3])
                if code >= 400:
                    raise SMTPError(code, '\n'.join(lines))
                return lines

    @coroutine
    def write(self, data: Union[bytes, str]):
        if type(data) is not str:
            data = data.encode('ascii')

        self.writer.write(data)
        yield from self.writer.drain()

    def close(self):
        self.writer.close()


class SMTPMailer(BaseMailer):
    """
    A mailer that uses the ESMTP protocol to send mails.

    Supports only plaintext or implicit SSL connections. STARTTLS is not supported yet.

    :param host: SMTP server address
    :param port: port to connect to (omit to use a default value based on SSL/no SSL)
    :param username: user name to authenticate as
    :param password: password to authenticate with
    :param max_connections: maximum number of concurrent connections to the server
    :param ssl: ``False`` to disable SSL, ``True`` to enable it; or pass SSLContext
    """

    def __init__(self, host: str, port: int=None, username: str=None, password: str=None,
                 max_connections: int=3, ssl: Union[bool, str, SSLContext]=True):
        if port is None:
            port = 25 if not ssl else 465

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.semaphore = BoundedSemaphore(max_connections)

    @coroutine
    def _authenticate(self, connection: SMTPConnection, auth_mechanisms: List[str]):
        if 'CRAM-MD5' in auth_mechanisms:
            challenge = yield from connection.command('AUTH CRAM-MD5')
            response = HMAC(self.password.encode(), challenge, 'md5').hexdigest()
            yield from connection.command('{} {}'.format(self.username, response))
        elif 'PLAIN' in auth_mechanisms:
            token = b64encode('\0{}\0{}'.format(self.username, self.password).encode())
            yield from connection.command('AUTH PLAIN {}'.format(token.decode()))
        elif 'LOGIN' in auth_mechanisms:
            yield from connection.command('AUTH LOGIN {} {}'.format(self.username, self.password))
        else:
            raise DeliveryError('Server does not support any authentication method we support')

    @asynchronous
    @coroutine
    def deliver(self, messages: Iterable[EmailMessage]):
        with (yield from self.semaphore):
            connection = yield from SMTPConnection.create(self.event_loop, self.host, self.port)
            try:
                features = yield from connection.command('EHLO', format(platform.node()))
                policy = SMTP(cte_type='8bit' if '8BITMIME' in features else '7bit')

                # Authenticate if necessary
                if self.username and self.password:
                    for i, feature in enumerate(features):
                        if feature.startswith('AUTH '):
                            auth_mechanisms = feature.split()[1:]
                            yield from self._authenticate(connection, auth_mechanisms)
                            break
                    else:
                        raise DeliveryError('Server does not support authentication')

                for message in messages:
                    yield from connection.command('MAIL FROM:', message.sender)
                    for recipient in self._get_recipients(message):
                        yield from connection.command('RCPT TO:', recipient)

                    envelope = message.as_bytes(policy=policy)
                    yield from connection.write(envelope)

                yield from connection.command('QUIT')
            finally:
                connection.close()
