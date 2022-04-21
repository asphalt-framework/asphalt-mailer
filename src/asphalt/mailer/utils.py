from __future__ import annotations

from email.headerregistry import UniqueAddressHeader
from email.message import EmailMessage
from typing import cast


def get_recipients(message: EmailMessage) -> list[str]:
    """
    Return a list of email addresses of all the intended recipients of the given
    message.

    This function is meant to be used by :class:`~asphalt.mailer.api.Mailer`
    implementations.

    :param message: the source email message

    """
    recipients = []
    for header in (message["To"], message["Cc"], message["Bcc"]):
        if header:
            for addr in cast(UniqueAddressHeader, header).addresses:
                recipients.append(addr.addr_spec)

    return recipients
