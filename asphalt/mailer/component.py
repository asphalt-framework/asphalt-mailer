import logging

from pkg_resources import iter_entry_points, EntryPoint
from asphalt.core.component import Component
from asphalt.core.context import ApplicationContext

from .mailers import BaseMailerBackend


class MailerComponent(Component):
    def __init__(self, mailer_property: str='mailer', **mailer_config):
        self.backends = {ep.name: ep for ep in iter_entry_points('asphalt.mailer.backends')}
        self.logger = logging.getLogger('asphalt.mailer')
        self.mailer_property = mailer_property
        self.mailer_config = mailer_config

    def create_mailer(self, **config):
        pass

    def start(self, app_ctx: ApplicationContext):
        app_ctx.publish_resource(mailer, name=self.mailer_property, type=BaseMailerBackend)
