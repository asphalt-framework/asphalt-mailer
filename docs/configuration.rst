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
        connector: tcp+ssl://primary-smtp.company.com:465
        username: foo
        password: bar

This configuration uses ``primary-smtp.company.com`` as the server hostname and uses implicit TLS_
to encrypt the connection. It authenticates with the server using the username ``foo`` and the
password ``bar``.

.. _TLS: https://en.wikipedia.org/wiki/Transport_Layer_Security

The above configuration can be done directly in Python code as follows:

.. code-block:: python

    class MyComponent(ContainerComponent):
        @coroutine
        def start(ctx: Context):
            self.add_component(
                'mailer', backend='smtp', connector='tcp+ssl://primary-smtp.company.com:465',
                username='foo', password='bar')
            yield from super().start()


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
            connector: tcp+ssl://primary-smtp.company.com:465
            username: foo
            password: bar
          smtp_b:
            backend: smtp
            context_attr: mailer2
            connector: isp-smtp.provider.com
          sendmail:
            backend: sendmail
            context_attr: mailer3

This configures three mailer resources, named ``smtp_a``, ``smtp_b`` and ``sendmail``.
Their corresponding context attributes are ``mailer1``, ``mailer2`` and ``mailer3``.
If you omit the ``context_attr`` option for a mailer, its resource name will be used.
