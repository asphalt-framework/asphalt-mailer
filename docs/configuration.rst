Configuration
=============

To configure a mailer for your application, you need to choose a backend and then specify
any necessary configuration values for it. The following backends are provided out of the box:

* :mod:`~asphalt.mailer.mailers.smtp` (**recommended**)
* :mod:`~asphalt.mailer.mailers.sendmail`
* :mod:`~asphalt.mailer.mailers.mock` (for testing only)

Other backends may be provided by other components.

Once you've selected a backend, see its specific documentation to find out what configuration
values you need to provide, if any. Configuration values are expressed as constructor arguments
for the backend class:

.. code-block:: yaml

    components:
      mailer:
        backend: smtp
        host: primary-smtp.company.com
        username: foo
        password: bar

This configuration uses ``primary-smtp.company.com`` as the server hostname. Because it has a
user name and password defined, the mailer will automatically use port 587 and STARTTLS_ before
authenticating itself with the server.

The above configuration can be done directly in Python code as follows::

    class ApplicationComponent(ContainerComponent):
        async def start(ctx: Context):
            self.add_component(
                'mailer', backend='smtp', host='primary-smtp.company.com', username='foo',
                password='bar')
            await super().start()

.. _STARTTLS: https://en.wikipedia.org/wiki/Opportunistic_TLS

Multiple mailers
----------------

If you need multiple mailers, you need to specify them via the ``mailers`` argument, which is a
dictionary of resource names to their backend configuration options:

.. code-block:: yaml

    components:
      mailer:
        mailers:
          smtp_a:
            backend: smtp
            context_attr: mailer1
            host: primary-smtp.company.com
            username: foo
            password: bar
          smtp_b:
            backend: smtp
            context_attr: mailer2
            host: isp-smtp.provider.com
          sendmail:
            backend: sendmail
            context_attr: mailer3

This configures three mailer resources, named ``smtp_a``, ``smtp_b`` and ``sendmail``.
Their corresponding context attributes are ``mailer1``, ``mailer2`` and ``mailer3``.
If you omit the ``context_attr`` option for a mailer, its resource name will be used.
