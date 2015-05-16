Mailer extension for Asphalt
============================

This extension provides an interface for sending email to the Asphalt framework.
The mailer extension uses `marrow.mailer`_ as the backing implementation. It supports a number of
transports, including SMTP, Sendmail, Google App Engine, Amazon SES and a mock transport for
testing purposes.

Configuration options
---------------------

================== =============================================== ===============================
Option             Description                                     Default value
================== =============================================== ===============================
mailer_property    Name of the mailer property on the application  mailer
                   context
(anything else)    Keyword arguments passed to the ``Mailer``
                   constructor
================== =============================================== ===============================

Configuration
-------------


Example configuration for SMTP:

.. code:: yaml

    extensions:
      - type: mailer
        transport:
          use: smtp
          host: your.smtp.server
          tls: required
          username: myusername
          password: mypassword
        message:
          author: "Me <me@example.org>"

This sets up an SMTP transport, using ``your.smtp.server`` as the host, using explicit TLS with
login credentials. Additionally, it sets a default value for the ``author`` field in all new
messages.

Sending mail
------------

To send an email with both HTML content and a plain text alternative:

.. code:: python

    def request_handler(ctx):
        msg = ctx.mailer.new(subject='Test message', to='someone@example.org')
        msg.rich = '<body><h1>Hello!</h1>This is a test.</body>'
        msg.plain = 'Hello!\nThis is a test.'
        msg.send()

The same in asynchronous mode:

.. code:: python

    @coroutine
    def request_handler(ctx):
        msg = ctx.mailer.new(subject='Test message', to='someone@example.org')
        msg.rich = '<body><h1>Hello!</h1>This is a test.</body>'
        msg.plain = 'Hello!\nThis is a test.'
        yield from msg.send()

Sending mail to multiple recipients:

.. code:: python

   def request_handler(ctx):
        recipients = [
            'Mom <mom@example.org>',
            'Dad <dad@example.org>'
        ]
        msg = ctx.mailer.new(subject='Hi folks', to=recipients)
        msg.rich = '<h1>Hello!</h1>This is a test.'
        msg.plain = 'Hello! This is a test.'
        msg.send()

Sending an attachment from the file system:

.. code:: python

   def request_handler(ctx):
       msg = ctx.mailer.new(subject='Test message', to='someone@example.org')
       msg.plain = 'Hello! Take a look at the attached file.'
       msg.attach('/some/path/important_files.zip')  # the MIME type is automatically guessed
       msg.send()

Embedding an image for an HTML email:

.. code:: python

   def request_handler(ctx):
       msg = ctx.mailer.new(subject='Test message', to='someone@example.org')
       msg.rich = 'Hey, look at this pretty picture! <img src="pretty_picture.jpg">'
       msg.plain = 'Sorry, no pics for you!'
       msg.embed('/some/path/pretty_picture.jpg')
       msg.send()

.. _marrow.mailer: https://github.com/marrow/marrow.mailer/blob/develop/README.textile
