from typing import Any

from ._api import DeliveryError as DeliveryError
from ._api import Mailer as Mailer
from ._component import MailerComponent as MailerComponent
from ._utils import get_recipients as get_recipients

# Re-export imports, so they look like they live directly in this package
key: str
value: Any
for key, value in list(locals().items()):
    if getattr(value, "__module__", "").startswith(f"{__name__}."):
        value.__module__ = __name__
