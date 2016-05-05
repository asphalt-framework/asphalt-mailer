from abc import abstractmethod, ABCMeta
from collections import Awaitable
from email.headerregistry import Address
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path
from typing import Iterable, Union, Dict, Any

from asyncio_extras.threads import call_in_executor
from typeguard import check_argument_types

from asphalt.core.context import Context

__all__ = ('DeliveryError', 'Mailer')

AddressListType = Union[str, Address, Iterable[Union[str, Address]]]


class DeliveryError(Exception):
    """
    Raised when there's an error with mail delivery.

    :ivar error: the error message
    :ivar message: the email message related to the failure, if any
    """

    def __init__(self, error: str, message: EmailMessage = None):
        super().__init__(error, message)

    def __str__(self):
        return 'error sending mail message: {}'.format(self.args[0])


class Mailer(metaclass=ABCMeta):
    """
    This is the abstract base class for all mailers.

    :param message_defaults: default values for omitted keyword arguments of :meth:`create_message`
    """

    __slots__ = 'message_defaults'

    def __init__(self, message_defaults: Dict[str, Any] = None):
        self.message_defaults = message_defaults or {}
        self.message_defaults.setdefault('charset', 'utf-8')

    async def start(self, ctx: Context):
        """
        Perform any necessary setup procedures.

        This method is called by the component on initialization.

        :param ctx: the mailer component's context
        """

    def create_message(self, *, subject: str = None, sender: Union[str, Address] = None,
                       to: AddressListType = None, cc: AddressListType = None,
                       bcc: AddressListType = None, charset: str = None, plain_body: str = None,
                       html_body: str = None) -> EmailMessage:
        """
        Create an :class:`~email.message.EmailMessage` using to be sent later using
        :meth:`deliver`.

        :param subject: subject line for the message
        :param sender: sender address displayed in the message (the From: header)
        :param to: primary recipient(s) (displayed in the message)
        :param cc: secondary recipient(s) (displayed in the message)
        :param bcc: secondary recipient(s) (**not** displayed in the message)
        :param charset: character encoding of the message
        :param plain_body: plaintext body
        :param html_body: HTML body

        """
        assert check_argument_types()
        msg = EmailMessage()
        msg['Subject'] = subject or self.message_defaults.get('subject')

        sender = sender or self.message_defaults.get('sender')
        if sender:
            msg['From'] = sender

        to = to or self.message_defaults.get('to')
        if to:
            msg['To'] = to

        cc = cc or self.message_defaults.get('cc')
        if cc:
            msg['Cc'] = cc

        bcc = bcc or self.message_defaults.get('bcc')
        if bcc:
            msg['Bcc'] = bcc

        charset = charset or self.message_defaults.get('charset')
        if plain_body is not None and html_body is not None:
            msg.set_content(plain_body, charset=charset)
            msg.add_alternative(html_body, charset=charset, subtype='html')
        elif plain_body is not None:
            msg.set_content(plain_body, charset=charset)
        elif html_body is not None:
            msg.set_content(html_body, charset=charset, subtype='html')

        return msg

    @classmethod
    def add_attachment(cls, msg: EmailMessage, content: bytes, filename: str,
                       mimetype: str = None):
        """
        Add binary data as an attachment to an :class:`~email.message.EmailMessage`.

        The default value for the ``mimetype`` argument is guessed from the file name.
        If guessing fails, ``application/octet-stream`` is used.

        :param msg: the message
        :param content: the contents of the attachment
        :param filename: the displayed file name in the message
        :param mimetype: the MIME type indicating the type of the file

        """
        assert check_argument_types()
        if not mimetype:
            mimetype, _encoding = guess_type(filename, False)
            if not mimetype:
                mimetype = 'application/octet-stream'

        maintype, subtype = mimetype.split('/', 1)
        if not maintype or not subtype:
            raise ValueError('mimetype must be a string in the "maintype/subtype" format')

        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    @classmethod
    async def add_file_attachment(cls, msg: EmailMessage, path: Union[str, Path],
                                  filename: str = None, mimetype: str = None):
        """
        Read the contents of a file and add them as an attachment to the given message.

        Reads the file contents and then passes the result as ``content`` to
        :meth:`add_attachment` along with the rest of the arguments.

        :param msg: the message
        :param path: path to the file to attach
        :param filename: the displayed file name in the message
        :param mimetype: the MIME type indicating the type of the file

        """
        assert check_argument_types()
        path = Path(path)
        content = await call_in_executor(path.read_bytes)
        cls.add_attachment(msg, content, filename or path.name, mimetype)

    def create_and_deliver(self, **kwargs) -> Awaitable:
        """
        Build a new email message and deliver it.

        This is a shortcut to calling :meth:`create_message` and then passing the result to
        :meth:`deliver`.

        :param kwargs: keyword arguments passed to :meth:`create_message`
        """

        msg = self.create_message(**kwargs)
        return self.deliver(msg)

    @abstractmethod
    async def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        """
        Deliver the given message(s).

        :param messages: the message or iterable of messages to deliver
        """
