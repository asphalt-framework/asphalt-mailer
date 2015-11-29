from asyncio import coroutine
from typing import Dict, Any
import logging

from asphalt.core.component import Component
from asphalt.core.context import Context
from asphalt.core.util import PluginContainer

from .api import Mailer

mailer_backends = PluginContainer('asphalt.mailer.mailers', Mailer)

logger = logging.getLogger(__name__)


class MailerComponent(Component):
    """
    Provides a way for sending email.

    Publishes one or more :class:`Mailer` compatible objects as
    resources and context variables.

    If more than one mailer is to be configured, provide a "mailers"
    argument as a dictionary where the key is the resource name and the
    value is a dictionary of keyword arguments to
    :meth:`create_mailer`. Otherwise, directly pass those keyword
    arguments to the component constructor itself.

    :param mailers: a dictionary of Mailer resource name ->
        :meth:`create_mailer` keyword arguments
    :param default_mailer_args: keyword arguments given to the backend
        class
    """

    def __init__(self, mailers: Dict[str, Dict[str, Any]]=None, **default_mailer_args):
        if mailers and default_mailer_args:
            raise ValueError('specify either a "mailers" dictionary or the default mailer\'s '
                             'options directly, but not both')

        mailers = mailers or {}
        if default_mailer_args:
            default_mailer_args.setdefault('context_attr', 'mailer')
            mailers['default'] = default_mailer_args

        self.mailers = [self.create_mailer(alias, **kwargs) for alias, kwargs in mailers.items()]

    @staticmethod
    def create_mailer(resource_name: str, backend: str, context_attr: str=None, **backend_kwargs):
        """
        Instantiates a Mailer backend with the given parameters.

        :param resource_name: resource name the mailer will be
            published as
        :param backend: specifies the type of mailer
            (declared as entry points in the ``asphalt.mailer.mailers``
            namespace)
        :param context_attr: the mailer's attribute name on the context
            (defaults to the value of ``resource_name``)
        :param backend_kwargs: keyword arguments passed to the
            constructor of the backend class
        """

        context_attr = context_attr or resource_name
        mailer = mailer_backends.create_object(backend, **backend_kwargs)
        return resource_name, context_attr, mailer

    @coroutine
    def start(self, ctx: Context):
        for resource_name, context_attr, mailer in self.mailers:
            yield from mailer.start(ctx)
            yield from ctx.publish_resource(mailer, resource_name, context_attr, types=[Mailer])
            logger.info('Configured mailer (%s / ctx.%s)', resource_name, context_attr)
