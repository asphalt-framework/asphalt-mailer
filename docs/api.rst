API reference
=============

.. py:currentmodule:: asphalt.mailer

Component
---------

.. autoclass:: MailerComponent

Interfaces
----------

.. autoclass:: Mailer

Exceptions
----------

.. autoexception:: DeliveryError

Utilities
---------

.. autofunction:: get_recipients

Mailer back-ends
----------------

.. autoclass:: asphalt.mailer.mailers.smtp.SMTPMailer
.. autoclass:: asphalt.mailer.mailers.sendmail.SendmailMailer
.. autoclass:: asphalt.mailer.mailers.mock.MockMailer
