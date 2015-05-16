from abc import ABCMeta, abstractmethod
from concurrent.futures import Future


class IMailer(metaclass=ABCMeta):
    @abstractmethod
    def new(self, subject: str=None, author: str=None, to: (str, list, tuple)=None,
            cc: (str, list, tuple)=None, bcc: (str, list, tuple)=None, encoding: str='utf-8',
            plain_body: str=None, html_body: str=None) -> IMessage:
        """
        Creates a new e-mail message.

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

class IMessage(metaclass=ABCMeta):
    @abstractmethod
    def attach(self, name: str, data=None, maintype: str=None, subtype: str=None,
               inline: bool=False, filename: str=None):
        """
        Attach a file to this message.

        :param name: path to the file to attach if data is None, or the name
                     of the file if the ``data`` argument is given
        :param data: contents (bytes or a file-like object) of the file to attach, or None if the
                     data is to be read from the file pointed to by the ``name`` argument
        :param maintype: First part of the MIME type of the file -- will be automatically guessed if
                         not given
        :param subtype: second part of the MIME type of the file -- will be automatically guessed if
                        not given
        :param inline: whether to set the Content-Disposition for the file to "inline" (``True``) or
                       "attachment" (``False``)
        :param filename: the file name of the attached file as seen by the user in their mail
                         client
        """

    @abstractmethod
    def embed(self, name: str, data: bytes=None):
        """
        Attach an image file and prepare for HTML embedding.
        This method should only be used to embed images.

        :param name: Path to the image to embed if data is None, or the name of the file if the
                     ``data`` argument is given
        :param data: Contents of the image to embed, or None if the data is to be read from the file
                     pointed to by the ``name`` argument
        """

    @abstractmethod
    def send(self) -> (Future, None):
        """
        Sends the message using the mailer it was created with.
        The return type depends on the mailer.

        In synchronous contexts, blocks until the message has been either rejected or accepted
        for delivery by the backend.
        In asynchronous contexts, immediately returns a Future that completes when the message has
        been rejected or accepted for delivery.
        """
