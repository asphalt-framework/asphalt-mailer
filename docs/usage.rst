Using mailers
=============

.. py:currentmodule:: asphalt.mailer

The primary tools for sending email with asphalt-mailer are the
:class:`~email.message.EmailMessage` class and the :meth:`~Mailer.deliver`
method. The workflow is to first construct one or more messages and then using the
mailer to deliver them.

Two convenience methods are provided to this end: :meth:`~Mailer.create_message`
and :meth:`~Mailer.create_and_deliver`. Both methods take the same arguments,
but the former only creates a message (for further customization), while the latter
creates and delivers a message in one shot, as the name implies.

Email messages can have plain and/or HTML content, along with attachments.
The full power of the new standard library email API is at your disposal.

In addition to the examples below, some runnable examples are also provided in the
``examples`` directory of the source distribution. The same code is also available on
`Github <https://github.com/asphalt-framework/asphalt-mailer/tree/master/examples>`_.

Simple example
--------------

This sends a plaintext message with the body "Greetings from Example!" to
``recipient@company.com``, addressed as coming from
``Example Person <example@company.com>``:

.. literalinclude:: snippets/usage1.py

HTML content
------------

Users may want to send styled emails using HTML. This can be done by passing the HTML
content using the ``html_body`` argument:

.. literalinclude:: snippets/usage2.py

.. note:: It is highly recommended to provide a plaintext fallback message (as in the
    above example) for cases where the recipient cannot display HTML messages for some
    reason.

Attachments
-----------

To add attachments, you can use the handy :meth:`~Mailer.add_file_attachment`
and :meth:`~Mailer.add_attachment` methods.

The following example adds the file ``/path/to/file.zip`` as an attachment to the
message. The file will be displayed as ``file.zip`` with the autodetected MIME type
``application/zip``:

.. literalinclude:: snippets/usage3.py

If you need more fine grained control, you can directly pass the attachment contents as
bytes to :meth:`~Mailer.add_attachment`, but then you will have to explicitly specify
the file name and MIME type:

.. literalinclude:: snippets/usage4.py

.. warning:: Most email servers today have strict limits on the size of the message, so
    it is recommended to keep the size of the attachments small. A maximum size of 20 MB
    is a good rule of thumb.

Multiple messages at once
-------------------------

To send multiple messages in one shot, you can use :meth:`~Mailer.create_message` to
create the messages and then use :meth:`~Mailer.deliver` to send them. This is very
useful when sending personalized emails for multiple recipients:

.. literalinclude:: snippets/usage5.py

Handling errors
---------------

If there is an error, a :class:`~asphalt.mailer.api.DeliveryError` will be raised.
Its ``message`` attribute will contain the problematic
:class:`~email.message.EmailMessage` instance if the error is specific to a single
message:

.. literalinclude:: snippets/usage6.py
