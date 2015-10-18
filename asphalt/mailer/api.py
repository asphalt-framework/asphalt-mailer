from abc import ABCMeta, abstractmethod
import email
from email.header import Header
from email.headerregistry import Address, AddressHeader
from email.message import Message, EmailMessage
from typing import Union, Iterable


class MailerAPI(metaclass=ABCMeta):
    @abstractmethod
    def send(self, subject: str='', author: str=None, to: Union[str, list, tuple]=None,
             cc: Union[str, list, tuple]=None, bcc: Union[str, list, tuple]=None,
             encoding: str='utf-8', plain_body: str=None, html_body: str=None, backend: str=None):
        """
        Builds a new e-mail message and delivers it, using the given backend if any.

        Email addresses should either be of the form "foo@bar.com" (just the address) or
        "Person Name <foo@bar.com>".

        The contents of the message are set using either ``plain_body``, ``html_body`` or both.

        :param subject: subject line for the message
        :param author: sender address displayed in the message
        :param to: primary recipient(s) (displayed in the message)
        :param cc: secondary recipient(s) (displayed in the message)
        :param bcc: secondary recipient(s) (**not** displayed in the message)
        :param plain_body: plaintext body
        :param html_body: HTML body
        """

        msg = EmailMessage()
        if plain_body is not None and html_body is not None:
            msg.set_content(plain_body, 'text', 'plain')
            msg.add_alternative(html_body, 'text', 'html')
        elif plain_body is not None:
            msg.set_content(plain_body)
        elif html_body is not None:
            msg.set_content(html_body)
        else:
            raise ValueError('either plain_body or html_body is required')

    @abstractmethod
    def deliver(self, mail: EmailMessage, *, backend: str=None):
        """Delivers a pre-built :cls:`~EmailMessage`, using the given backend if any."""

# class Address:
#     __slots__ = 'address', 'name'
#
#     @typechecked
#     def __init__(self, address: str, name: str=None):
#         self.address = address
#         self.name = name
#
#     @classmethod
#     def convert(cls, address: 'AddressType'):
#         return cls(address) if type(address) is str else address
#
#     @classmethod
#     def convertlist(cls, addresses: 'AddressType'):
#         if isinstance(addresses, (str, Address)):
#             addresses = (addresses,)
#         return [cls.convert(addr) for addr in addresses]
#
#     def __str__(self):
#         if self.name:
#             return '{0.name} <{0.address}>'.format(self)
#         return self.address
#
#     def __repr__(self):
#         return '<{0} name="{1.name}" address="{1.address}">'.format(self.__class__.__name__, self)


AddressType = Union[str, Address]
AddressListType = Union[Address, Iterable[AddressType]]


def as_address(address: AddressType):
    return Address(address) if type(address) is str else address


def as_addresslist(addresses: AddressType):
    if isinstance(addresses, (str, Address)):
        addresses = (addresses,)
    return [as_address(addr) for addr in addresses]


# class Attachment:
#     __slots__ = 'data', 'filename', 'mimetype', 'inline'
#
#     @typechecked
#     def __init__(self, data: bytes, filename: str, mimetype: str, inline: bool):
#         self.data = data
#         self.filename = filename
#         self.mimetype = mimetype
#         self.inline = inline
#
#     def __repr__(self):
#         return '<{} filename="{}">'.format(self.__class__.__name__, self.filename)


# class Email:
#     @typechecked
#     def __init__(self, subject: str, plaintext: str='', html: str=None,
#                  author: AddressType=None, to: AddressListType=(), cc=AddressListType,
#                  bcc=AddressListType, charset='utf-8'):
#         self.subject = subject
#         self.plaintext = plaintext
#         self.html = html
#         self.author = as_address(author)
#         self.to = as_addresslist(to)
#         self.cc = as_addresslist(cc)
#         self.bcc = as_addresslist(bcc)
#         self.charset = charset
#
#     @typechecked
#     def attach_file(self, path: Union[str, Path], mimetype: str=None, inline: bool=False,
#                     filename: str=None):
#         """
#         Attaches a file to this message.
#
#         :param path: path to the file to attach if data is None, or the name
#                      of the file if the ``data`` argument is given
#         :param mimetype: The MIME type of the file -- will be automatically guessed if not given
#         :param inline: whether to set the Content-Disposition for the file to "inline" (``True``)
#                        or "attachment" (``False``)
#         :param filename: the file name of the attached file as seen by the user's mail
#                          client (overrides the one from ``path`` if given)
#         """
#
#         path = Path(path)
#         with path.open('rb') as f:
#             data = f.read()
#
#         mimetype = guess_type(path.name, False)[0] if mimetype is None else mimetype
#         return self.attach_data(data, path.name, mimetype, inline, filename)
#
#     @typechecked
#     def attach_data(self, data: bytes, filename: str, mimetype: str=None, inline: bool=False):
#         """
#         Attaches the given data to this message as a file.
#
#         :param data: contents (bytes or a file-like object) of the file to attach, or None if the
#                      data is to be read from the file pointed to by the ``name`` argument
#         :param filename: the file name of the attached file as seen by the user's mail client
#         :param mimetype: The MIME type of the file -- will be automatically guessed if not given
#         :param inline: whether to set the Content-Disposition for the file to "inline" (``True``)
#                        or "attachment" (``False``)
#         """
#
#     @typechecked
#     def embed_image(self, path: Union[str, Path], data: bytes=None):
#         """
#         Attach an image file and prepare for HTML embedding.
#         This method should only be used to embed images.
#
#         :param path: Path to the image to embed if data is None, or the name of the file if the
#                      ``data`` argument is given
#         :param data: Contents of the image to embed, or None if the data is to be read from the
#                      file pointed to by the ``name`` argument
#         """
#
#     def envelope(self, supports_8bit: bool) -> bytes:
#         policy = SMTP(cte_type='8bit' if supports_8bit else '7bit')
#         msg = EmailMessage(policy)
#         msg.set_charset(self.charset)
#
#         # Add the headers
#         if self.subject:
#             msg['Subject'] = self.subject
#         if self.author:
#             msg['From'] = self.author
#         if self.to:
#             msg['To'] = AddressHeader(self.to)
#         if self.cc:
#             msg['Cc'] = self.cc
#
#         # Add the body
#         msg.set_content(self.plaintext)
#         if self.html:
#             msg.add_alternative(self.html, subtype='html')
#
#         return bytes(msg)
#
#     @property
#     def recipient_addresses(self):
#         return tuple(address.address for address in self.to + self.cc + self.bcc)


def create_email(subject: str, plaintext: str='', html: str=None,
                 author: AddressType=None, to: AddressListType=(), cc=AddressListType,
                 bcc=AddressListType, *, html_images=(), charset='utf-8'):
    """
    A convenience shortcut for creating a new email message

    :param subject:
    :param plaintext:
    :param html:
    :param author:
    :param to:
    :param cc:
    :param bcc:
    :param html_images:
    :param charset:
    :return:
    """
#    policy = SMTP(cte_type='8bit' if supports8bit else '7bit')
#    msg = EmailMessage(policy)
    msg = EmailMessage()

    # Add the headers
    msg['Subject'] = subject
    if author:
        msg['From'] = as_address(author)
    if to:
        msg['To'] = as_addresslist(to)
    if cc:
        msg['Cc'] = as_addresslist(cc)
    if bcc:
        msg['Bcc'] = as_addresslist(bcc)

    # Add the body
    msg.set_content(plaintext)
    if html:
        msg.add_alternative(html, subtype='html')
        if html_images:
            msg.add_related()
