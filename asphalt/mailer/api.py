from abc import abstractmethod, ABCMeta
from asyncio import coroutine
from email.headerregistry import Address
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path

from typing import Iterable, Union, Dict, Any

from asphalt.core.context import Context
from asphalt.core.util import blocking

__all__ = 'DeliveryError', 'Mailer'

AddressListType = Union[str, Address, Iterable[Union[str, Address]]]


class DeliveryError(Exception):
    """
    Raised when there's an error with mail delivery.

    :param error: the error message
    :param message: the email message related to the failure, if any
    """

    def __init__(self, error: str, message: EmailMessage=None):
        super().__init__(error, message)

    def __str__(self):
        return 'error sending mail message: {}'.format(self.args[0])


class Mailer(metaclass=ABCMeta):
    """
    This is the abstract base class for all mailers.

    :param defaults: default values for omitted keyword arguments of :meth:`create_message`
    """

    __slots__ = 'defaults'

    def __init__(self, defaults: Dict[str, Any]=None):
        self.defaults = defaults or {}

    @coroutine
    def start(self, ctx: Context):
        """
        Called by the component to allow the mailer to perform any necessary setup procedures.
        It is a coroutine.

        :param ctx: the component's context
        """

    def create_message(self, *, subject: str=None, sender: Union[str, Address]=None,
                       to: AddressListType=None, cc: AddressListType=None,
                       bcc: AddressListType=None, charset: str='utf-8', plain_body: str=None,
                       html_body: str=None) -> EmailMessage:
        """
        A convenience method for creating an
        :class:`~email.message.EmailMessage` to be sent later using
        :meth:`deliver`.

        :param subject: subject line for the message
        :param sender: sender address displayed in the message
                       (the From: header)
        :param to: primary recipient(s) (displayed in the message)
        :param cc: secondary recipient(s) (displayed in the message)
        :param bcc: secondary recipient(s) (**not** displayed in the message)
        :param charset: character encoding of the message
        :param plain_body: plaintext body
        :param html_body: HTML body
        """

        msg = EmailMessage()
        msg['Subject'] = subject or self.defaults.get('subject')
        if sender:
            msg['From'] = sender or self.defaults.get('sender')
        if to:
            msg['To'] = to or self.defaults.get('to')
        if cc:
            msg['Cc'] = cc or self.defaults.get('cc')
        if bcc:
            msg['Bcc'] = bcc or self.defaults.get('bcc')

        if plain_body is not None and html_body is not None:
            msg.set_content(plain_body, charset=charset)
            msg.add_alternative(html_body, charset=charset, subtype='html')
        elif plain_body is not None:
            msg.set_content(plain_body, charset=charset)
        elif html_body is not None:
            msg.set_content(html_body, charset=charset, subtype='html')

        return msg

    @staticmethod
    def add_attachment(msg: EmailMessage, content: bytes, filename: str,
                       mimetype: str='application/octet-stream'):
        """
        Adds binary data as an attachment to an
        :class:`~email.message.EmailMessage`.

        :param msg: the message
        :param content: the contents of the attachment
        :param mimetype: the MIME type indicating the type of the file
        :param filename: the displayed file name in the message
        """

        maintype, subtype = mimetype.split('/', 1)
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    @classmethod
    @blocking
    def add_file_attachment(cls, msg: EmailMessage, path: Union[str, Path], filename: str=None,
                            mimetype: str=None):
        """
        Creates an attachment on the given
        :class:`~email.message.EmailMessage` from a file on the filesystem.
        This is a coroutine.

        The default value for the ``filename`` argument is the file name
        part of the given path. The default value for the ``mimetype``
        argument is guessed from the file name.

        :param msg: the message
        :param path: path to the file to attach
        :param mimetype: the MIME type indicating the type of the file
        :param filename: the displayed file name in the message
        """

        path = Path(path)
        with path.open('rb') as f:
            content = f.read()
        if not mimetype:
            mimetype = guess_type(str(path))[0] or 'application/octet-stream'
        if filename is None:
            filename = path.name

        cls.add_attachment(msg, content, filename, mimetype)

    def create_and_deliver(self, **kwargs):
        """
        Builds a new email message and delivers it. This is a coroutine.

        This is a shortcut to calling :meth:`create_message` and then passing the result to
        :meth:`deliver`.

        :param kwargs: keyword arguments passed to :meth:`create_message`
        """

        msg = self.create_message(**kwargs)
        return self.deliver(msg)

    @abstractmethod
    def deliver(self, messages: Union[EmailMessage, Iterable[EmailMessage]]):
        """
        Delivers the given message(s). This is a coroutine.

        :param messages: the message or iterable of messages to deliver
        """
