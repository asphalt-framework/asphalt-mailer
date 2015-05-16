import logging

from asphalt.interface.core.configurator import IConfigurable, IConfigurator
from asphalt.core.util import typechecked
from marrow.mailer import Mailer

logger = logging.getLogger(__name__)


class MailerExtension(IConfigurable):
    @typechecked
    def __init__(self, mailer_property: str='mailer', **mailer_config):
        self.mailer_property = mailer_property
        self.mailer = Mailer(**mailer_config)

    def setup(self, configurator: IConfigurator):
        configurator.register_resource('mailer')
        cls.register_property(self, self.mailer_property, self.mailer)
        configurator.register_callback(self, 'start', self.application_started)
        configurator.register_callback(self, 'finish', self.application_stopped)

    def application_started(self, ctx):
        self.mailer.start()
        logger.info('Mailer started (transport=%s)', self.mailer.manager.transport)

    def application_stopped(self, ctx):
        self.mailer.stop()
        logger.info('Mailer stopped')
