import logging
from typing import Dict, Any

from typeguard import check_argument_types

from asphalt.core.component import Component
from asphalt.core.context import Context
from asphalt.core.util import PluginContainer, merge_config
from asphalt.mailer.api import Mailer

mailer_backends = PluginContainer('asphalt.mailer.mailers', Mailer)

logger = logging.getLogger(__name__)


class MailerComponent(Component):
    """
    Publishes one or more :class:`~asphalt.mailer.api.Mailer` resources.

    If more than one mailer is to be configured, provide a ``mailers`` argument as a dictionary
    where the key is the resource name and the value is a dictionary of keyword arguments to
    :meth:`create_mailer`. Otherwise, directly pass those keyword arguments to the component
    constructor itself.

    If ``mailers`` is defined, any extra keyword arguments are used as default values for
    :meth:`create_mailer` for all mailers (:func:`~asphalt.core.util.merge_config` is used to
    merge the per-mailer arguments with the defaults). Otherwise, a single mailer is created based
    on the provided default arguments, with ``context_attr`` defaulting to ``mailer``.

    :param mailers: a dictionary of resource name ⭢ :meth:`create_mailer` keyword arguments
    :param default_mailer_args: default values for :meth:`create_mailer`
    """

    def __init__(self, mailers: Dict[str, Dict[str, Any]] = None, **default_mailer_args):
        assert check_argument_types()
        mailers = mailers or {}
        if default_mailer_args:
            default_mailer_args.setdefault('context_attr', 'mailer')
            mailers['default'] = default_mailer_args

        self.mailers = []
        for resource_name, config in mailers.items():
            config = merge_config(default_mailer_args, config)
            config.setdefault('context_attr', resource_name)
            context_attr, mailer = self.create_mailer(**config)
            self.mailers.append((resource_name, context_attr, mailer))

    @classmethod
    def create_mailer(cls, context_attr: str, backend: str, **backend_kwargs):
        """
        Configure a Mailer backend with the given parameters.

        :param context_attr: the mailer's attribute name on the context (defaults to the resource
            name)
        :param backend: specifies the type of mailer (declared as entry points in the
            ``asphalt.mailer.mailers`` namespace)
        :param backend_kwargs: keyword arguments passed to the constructor of the backend class

        """
        assert check_argument_types()
        mailer = mailer_backends.create_object(backend, **backend_kwargs)
        return context_attr, mailer

    async def start(self, ctx: Context):
        for resource_name, context_attr, mailer in self.mailers:
            await mailer.start(ctx)
            ctx.publish_resource(mailer, resource_name, context_attr, types=[Mailer])
            logger.info('Configured mailer (%s / ctx.%s)', resource_name, context_attr)
