from __future__ import annotations

from abc import ABCMeta, abstractmethod
from asyncio import get_running_loop
from collections.abc import Awaitable
from email.headerregistry import Address
from email.message import EmailMessage
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Iterable, Union

AddressListType = Union[str, Address, Iterable[Union[str, Address]]]


class DeliveryError(Exception):
    """
    Raised when there's an error with mail delivery.

    :ivar error: the error message
    :ivar message: the email message related to the failure, if any
    """

    def __init__(self, error: str, message: EmailMessage | None = None):
        super().__init__(error, message)

    def __str__(self) -> str:
        return f"error sending mail message: {self.args[0]}"


class Mailer(metaclass=ABCMeta):
    """
    This is the abstract base class for all mailers.

    :param message_defaults: default values for omitted keyword arguments of
        :meth:`create_message`
    """

    __slots__ = "message_defaults"

    def __init__(self, message_defaults: dict[str, Any] | None = None):
        self.message_defaults = message_defaults or {}
        self.message_defaults.setdefault("charset", "utf-8")

    async def start(self) -> None:
        """
        Perform any necessary setup procedures.

        This method is called by the component on initialization.
        """

    def create_message(
        self,
        *,
        subject: str | None = None,
        sender: str | Address | None = None,
        to: AddressListType | None = None,
        cc: AddressListType | None = None,
        bcc: AddressListType | None = None,
        charset: str | None = None,
        plain_body: str | None = None,
        html_body: str | None = None,
    ) -> EmailMessage:
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
        msg = EmailMessage()
        msg["Subject"] = subject or self.message_defaults.get("subject")

        sender = sender or self.message_defaults.get("sender")
        if sender:
            msg["From"] = sender

        to = to or self.message_defaults.get("to")
        if to:
            msg["To"] = to

        cc = cc or self.message_defaults.get("cc")
        if cc:
            msg["Cc"] = cc

        bcc = bcc or self.message_defaults.get("bcc")
        if bcc:
            msg["Bcc"] = bcc

        charset = charset or self.message_defaults.get("charset")
        if plain_body is not None and html_body is not None:
            msg.set_content(plain_body, charset=charset)
            msg.add_alternative(html_body, charset=charset, subtype="html")
        elif plain_body is not None:
            msg.set_content(plain_body, charset=charset)
        elif html_body is not None:
            msg.set_content(html_body, charset=charset, subtype="html")

        return msg

    @classmethod
    def add_attachment(
        cls,
        msg: EmailMessage,
        content: bytes,
        filename: str,
        mimetype: str | None = None,
    ) -> None:
        """
        Add binary data as an attachment to an :class:`~email.message.EmailMessage`.

        The default value for the ``mimetype`` argument is guessed from the file name.
        If guessing fails, ``application/octet-stream`` is used.

        :param msg: the message
        :param content: the contents of the attachment
        :param filename: the displayed file name in the message
        :param mimetype: the MIME type indicating the type of the file

        """
        if not mimetype:
            mimetype, _encoding = guess_type(filename, False)
            if not mimetype:
                mimetype = "application/octet-stream"

        maintype, subtype = mimetype.split("/", 1)
        if not maintype or not subtype:
            raise ValueError(
                'mimetype must be a string in the "maintype/subtype" format'
            )

        msg.add_attachment(
            content,
            maintype=maintype,
            subtype=subtype,
            filename=filename,
        )

    @classmethod
    async def add_file_attachment(
        cls,
        msg: EmailMessage,
        path: str | Path,
        filename: str | None = None,
        mimetype: str | None = None,
    ) -> None:
        """
        Read the contents of a file and add them as an attachment to the given message.

        Reads the file contents and then passes the result as ``content`` to
        :meth:`add_attachment` along with the rest of the arguments.

        :param msg: the message
        :param path: path to the file to attach
        :param filename: the displayed file name in the message
        :param mimetype: the MIME type indicating the type of the file

        """
        path = Path(path)
        content = await get_running_loop().run_in_executor(None, path.read_bytes)
        cls.add_attachment(msg, content, filename or path.name, mimetype)

    def create_and_deliver(self, **kwargs: Any) -> Awaitable[None]:
        """
        Build a new email message and deliver it.

        This is a shortcut to calling :meth:`create_message` and then passing the result
        to :meth:`deliver`.

        :param kwargs: keyword arguments passed to :meth:`create_message`
        """

        msg = self.create_message(**kwargs)
        return self.deliver(msg)

    @abstractmethod
    async def deliver(self, messages: EmailMessage | Iterable[EmailMessage]) -> None:
        """
        Deliver the given message(s).

        :param messages: the message or iterable of messages to deliver
        """
