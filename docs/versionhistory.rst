Version history
===============

This library adheres to `Semantic Versioning <http://semver.org/>`_.

**2.0.0** (2016-05-09)

- **BACKWARD INCOMPATIBLE** Migrated to Asphalt 2.0
- **BACKWARD INCOMPATIBLE** Renamed ``Mailer.defaults`` to ``Mailer.message_defaults``
- Allowed combining ``mailers`` with default parameters
- Fixed default message parameters not being applied in ``Mailer.create_message()``

**1.1.0** (2016-01-02)

- Added typeguard checks to fail early if arguments of wrong types are passed to functions

**1.0.0** (2015-10-31)

- Initial release
