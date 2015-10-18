from email.message import EmailMessage
from typing import Optional


class DeliveryError(Exception):
    """Raised when there's an error with mail delivery."""

    def __init__(self, error: str, message: EmailMessage=None):
        super().__init__(error, message)

    @property
    def error(self) -> str:
        return self.args[0]

    @property
    def message(self) -> Optional[EmailMessage]:
        return self.args[1]

    def __str__(self):
        return 'Error sending mail message: {}'.format(self.args[0])
