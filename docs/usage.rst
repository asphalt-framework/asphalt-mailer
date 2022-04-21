Using mailers
=============

The primary tools for sending email with asphalt-mailer are the
:class:`~email.message.EmailMessage` class and the :meth:`~asphalt.mailer.api.Mailer.deliver`
method. The workflow is to first construct one or more messages and then using the mailer to
deliver them.

Two convenience methods are provided to this end: :meth:`~asphalt.mailer.api.Mailer.create_message`
and :meth:`~asphalt.mailer.api.Mailer.create_and_deliver`. Both methods take the same arguments,
but the former only creates a message (for further customization), while the latter creates and
delivers a message in one shot, as the name implies.

Email messages can have plain and/or HTML content, along with attachments.
The full power of the new standard library email API is at your disposal.

In addition to the examples below, some runnable examples are also provided in the ``examples``
directory of the source distribution. The same code is also available on
`Github <https://github.com/asphalt-framework/asphalt-mailer/tree/master/examples>`_.


Simple example
--------------

This sends a plaintext message with the body "Greetings from Example!" to
``recipient@company.com``, addressed as coming from ``Example Person <example@company.com>``::

    async def handler(ctx):
        await ctx.mailer.create_and_deliver(
            subject='Hi there!', sender='Example Person <example@company.com>',
            to='recipient@company.com', plain_body='Greetings from Example!')


HTML content
------------

Users may want to send styled emails using HTML. This can be done by passing the HTML content
using the ``html_body`` argument::

    async def handler(ctx):
        html = "<h1>Greetings</h1>Greetings from <strong>Example Person!</strong>"
        plain = "Greetings!\n\nGreetings from Example Person!"
        await ctx.mailer.create_and_deliver(
            subject='Hi there!', sender='Example Person <example@company.com>',
            to='recipient@company.com', plain_body=plain, html_body=html)

.. note:: It is highly recommended to provide a plaintext fallback message (as in the above
          example) for cases where the recipient cannot display HTML messages for some reason.


Attachments
-----------

To add attachments, you can use the handy :meth:`~asphalt.mailer.api.Mailer.add_file_attachment`
and :meth:`~asphalt.mailer.api.Mailer.add_attachment` methods.

The following example adds the file ``/path/to/file.zip`` as an attachment to the message.
The file will be displayed as ``file.zip`` with the autodetected MIME type ``application/zip``::

    async def handler(ctx):
        message = ctx.mailer.create_message(
            subject='Hi there!', sender='Example Person <example@company.com>',
            to='recipient@company.com', plain_body='See the attached file.')
        await ctx.mailer.add_file_attachment(message, '/path/to/file.zip')
        await ctx.mailer.deliver(message)

If you need more fine grained control, you can directly pass the attachment contents as bytes
to :meth:`~asphalt.mailer.api.Mailer.add_attachment`, but then you will have to explicitly
specify the file name and MIME type::

    async def handler(ctx):
        message = ctx.mailer.create_message(
            subject='Hi there!', sender='Example Person <example@company.com>',
            to='recipient@company.com', plain_body='See the attached file.')
        ctx.mailer.add_attachment(message, b'file contents', 'attachment.txt')
        await ctx.mailer.deliver(message)

.. warning:: Most email servers today have strict limits on the size of the message, so it is
             recommended to keep the size of the attachments small.
             A maximum size of 2 MB is a good rule of thumb.


Multiple messages at once
-------------------------

To send multiple messages in one shot, you can use
:meth:`~asphalt.mailer.api.Mailer.create_message` to create the messages and then use
:meth:`~asphalt.mailer.api.Mailer.deliver` to send them. This is very useful when sending
personalized emails for multiple recipients::

    from email.headerregistry import Address


    async def handler(ctx):
        messages = []
        for recipient in [Address('Some Person', 'some.person', 'company.com'),
                          Address('Other Person', 'other.person', 'company.com')]:
            message = ctx.mailer.create_message(
                subject='Hi there, %s!' % recipient.display_name,
                sender='Example Person <example@company.com>',
                to=recipient, plain_body='How are you doing, %s?' % recipient.display_name)
            messages.append(message)

        await ctx.mailer.deliver(messages)


Handling errors
---------------

If there is an error, a :class:`~asphalt.mailer.api.DeliveryError` will be raised.
Its ``message`` attribute will contain the problematic :class:`~email.message.EmailMessage`
instance if the error is specific to a single message::

    async def handler(ctx):
        try:
            await ctx.mailer.create_and_deliver(
                subject='Hi there!', sender='Example Person <example@company.com>',
                to='recipient@company.com', plain_body='Greetings from Example!')
        except DeliveryError as e:
            print('Delivery to {} failed: {}'.format(e.message['To'], e.error))
