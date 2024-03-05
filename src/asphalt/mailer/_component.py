from __future__ import annotations

import logging
from typing import Any

from asphalt.core import Component, PluginContainer, add_resource, qualified_name

from asphalt.mailer._api import Mailer

mailer_backends = PluginContainer("asphalt.mailer.mailers", Mailer)
logger = logging.getLogger("asphalt.mailer")


class MailerComponent(Component):
    """
    Creates a :class:`~asphalt.mailer.api.Mailer` resource.

    :param backend: entry point name of the mailer backend class
    :param resource_name: name of the mailer resource to be published
    :param mailer_args: keyword arguments passed to the mailer backend class
    """

    def __init__(
        self, backend: str, resource_name: str = "default", **mailer_args: Any
    ):
        self.mailer = mailer_backends.create_object(backend, **mailer_args)
        self.resource_name = resource_name

    async def start(self) -> None:
        await self.mailer.start()
        add_resource(self.mailer, self.resource_name, types=[Mailer, type(self.mailer)])
        logger.info(
            "Configured mailer (%s; class=%s)",
            self.resource_name,
            qualified_name(self.mailer),
        )
