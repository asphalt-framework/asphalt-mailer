from email.message import EmailMessage
from typing import List

from typeguard import check_argument_types


def get_recipients(message: EmailMessage) -> List[str]:
    """
    Returns a list of email addresses of all the intended
    recipients of the given message.

    This function is meant to be used by
    :class:`~asphalt.mailer.api.Mailer` implementations.

    :param message: the source email message

    """
    assert check_argument_types()
    recipients = []
    for header in (message['To'], message['Cc'], message['Bcc']):
        if header:
            for addr in header.addresses:
                recipients.append(addr.addr_spec)

    return recipients
