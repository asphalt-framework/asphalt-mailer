Version history
===============

This library adheres to `Semantic Versioning <http://semver.org/>`_.

**3.0.1**

- Added compatibility with Asphalt 4.0

**3.0.0** (2017-04-17)

- **BACKWARD INCOMPATIBLE** Migrated to Asphalt 3.0
- **BACKWARD INCOMPATIBLE** Replaced home grown SMTP implementation with aiosmtplib
- **BACKWARD INCOMPATIBLE** Implicit TLS support in SMTPMailer was replaced with STARTTLS support
- **BACKWARD INCOMPATIBLE** The ``ssl`` option in SMTPMailer was replaced with the ``tls`` and
  ``tls_context`` options
- **BACKWARD INCOMPATIBLE** Default port selection in SMTPMailer was changed; see the class
  docstring for details
- **BACKWARD INCOMPATIBLE** Renamed the ``asphalt.mailer.util`` module to ``asphalt.mailer.utils``

**2.0.1** (2017-01-09)

- Fixed occasional missing dots in the messages (due to not quoting leading dots)

**2.0.0** (2016-05-09)

- **BACKWARD INCOMPATIBLE** Migrated to Asphalt 2.0
- **BACKWARD INCOMPATIBLE** Renamed ``Mailer.defaults`` to ``Mailer.message_defaults``
- Allowed combining ``mailers`` with default parameters
- Fixed default message parameters not being applied in ``Mailer.create_message()``

**1.1.0** (2016-01-02)

- Added typeguard checks to fail early if arguments of wrong types are passed to functions

**1.0.0** (2015-10-31)

- Initial release
