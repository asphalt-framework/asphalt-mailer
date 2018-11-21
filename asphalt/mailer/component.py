import logging
from typing import Dict, Any, List  # noqa: F401

from asphalt.core import Component, Context, PluginContainer, merge_config, context_teardown
from async_generator import yield_
from typeguard import check_argument_types

from asphalt.mailer.api import Mailer

mailer_backends = PluginContainer('asphalt.mailer.mailers', Mailer)
logger = logging.getLogger(__name__)


class MailerComponent(Component):
    """
    Creates one or more :class:`~asphalt.mailer.api.Mailer` resources.

    Mailers can be configured in two ways:

    #. a single mailer, with configuration supplied directly as keyword arguments to this
        component's constructor (with the resource name being ``default`` and the context attribute
        matching the backend name)
    #. multiple mailers, by providing the ``mailers`` option where each key is the resource
        name and each value is a dictionary containing that mailer's configuration (with the
        context attribute matching the resource name by default)

    Each mailer configuration has two special options that are not passed to the constructor of
    the backend class:

    * backend: entry point name of the mailer backend class (required)
    * context_attr: name of the context attribute of the mailer resource

    :param mailers: a dictionary of resource name ⭢ constructor arguments for the chosen
        backend class
    :param default_mailer_args: default values for constructor keyword arguments
    """

    def __init__(self, mailers: Dict[str, Dict[str, Any]] = None, **default_mailer_args):
        assert check_argument_types()
        mailers = mailers or {}
        if default_mailer_args:
            default_mailer_args.setdefault('context_attr', 'mailer')
            mailers['default'] = default_mailer_args

        self.mailers = []  # type: List[Mailer]
        for resource_name, config in mailers.items():
            config = merge_config(default_mailer_args, config)
            backend = config.pop('backend')
            context_attr = config.pop('context_attr', resource_name)
            mailer = mailer_backends.create_object(backend, **config)
            self.mailers.append((resource_name, context_attr, mailer))

    @context_teardown
    async def start(self, ctx: Context):
        for resource_name, context_attr, mailer in self.mailers:
            await mailer.start(ctx)
            ctx.add_resource(mailer, resource_name, context_attr, [Mailer, type(mailer)])
            logger.info('Configured mailer (%s / ctx.%s; class=%s)', resource_name, context_attr,
                        mailer.__class__.__name__)

        await yield_()

        for resource_name, context_attr, mailer in self.mailers:
            logger.info('Mailer (%s) stopped', resource_name)
