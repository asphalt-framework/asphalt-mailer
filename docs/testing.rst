Testing with mailers
====================

.. py:currentmodule:: asphalt.mailer

When you test an application that uses asphalt-mailer, you don't want it to actually
send any emails outside of your testing environment. To that end, it is recommended that
you use :class:`~asphalt.mailer.mailers.mock.MockMailer` as the mailer backend in your
testing configuration. This mailer simply stores the sent messages which you can then
verify in your test function:

.. literalinclude:: snippets/testing1.py
