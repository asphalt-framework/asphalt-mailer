.. image:: https://travis-ci.org/asphalt-framework/asphalt-mailer.svg?branch=master
  :target: https://travis-ci.org/asphalt-framework/asphalt-mailer
  :alt: Build Status
.. image:: https://coveralls.io/repos/github/asphalt-framework/asphalt-mailer/badge.svg?branch=master
  :target: https://coveralls.io/github/asphalt-framework/asphalt-mailer?branch=master
  :alt: Code Coverage

This Asphalt framework component provides a means for sending email from Asphalt applications.

Three mechanisms are currently supported:

* `SMTP <https://en.wikipedia.org/wiki/SMTP>`_ (using `aiosmtplib`_)
* `Sendmail <https://en.wikipedia.org/wiki/Sendmail>`_
* Mock (just stores sent mails; useful for testing applications)

Third party libraries may provide additional backends.

.. _aiosmtplib: https://github.com/cole/aiosmtplib

Project links
-------------

* `Documentation <http://asphalt-mailer.readthedocs.org/en/latest/>`_
* `Help and support <https://github.com/asphalt-framework/asphalt/wiki/Help-and-support>`_
* `Source code <https://github.com/asphalt-framework/asphalt-mailer>`_
* `Issue tracker <https://github.com/asphalt-framework/asphalt-mailer/issues>`_
