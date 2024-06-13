Configuration
=============

.. highlight:: yaml
.. py:currentmodule:: asphalt.mailer

To configure a mailer for your application, you need to choose a backend and then specify
any necessary configuration values for it. The following backends are provided out of the box:

* :mod:`~.mailers.smtp` (**recommended**)
* :mod:`~.mailers.sendmail`
* :mod:`~.mailers.mock` (for testing only)

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

This configuration uses ``primary-smtp.company.com`` as the server hostname. Because it
has a user name and password defined, the mailer will automatically use port 587 and
STARTTLS_ before authenticating itself with the server.

The above configuration can be done directly in Python code as follows:

.. literalinclude:: snippets/configuration1.py
    :language: python

.. _STARTTLS: https://en.wikipedia.org/wiki/Opportunistic_TLS

Multiple mailers
----------------

If you need to configure multiple mailers, you will need to use multiple instances
of the mailer component:

.. code-block:: yaml

    components:
      mailer:
        backend: smtp
        host: primary-smtp.company.com
        username: foo
        password: dummypass
      mailer/alternate:
        resource_name: alternate
        backend: sendmail

The above configuration creates two mailer resources: ``default`` and ``alternate``.
