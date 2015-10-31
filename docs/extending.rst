Writing new mailer backends
===========================

If you wish to implement an alternate method of sending email, you can do so by subclassing the
:class:`~asphalt.mailer.api.Mailer` class. There are two methods implementors typically override:

* :meth:`~asphalt.mailer.api.Mailer.start` (optional)
* :meth:`~asphalt.mailer.api.Mailer.deliver`

The ``start`` method is a coroutine that is called by the component from its own
:meth:`~asphalt.core.component.Component.start` method. You can handle any necessary resource
related setup there.

The ``deliver`` method must be overridden and needs to:

#. handle both a single :class:`~email.message.EmailMessage` and an iterable of them
#. remove any ``Bcc`` header from each message to avoid revealing the hidden recipients

If you want your mailer to be available as a backend for the
:class:`~asphalt.mailer.component.MailerComponent`, you need to add the corresponding entry point
for it. Suppose your mailer class is named ``AwesomeMailer``, lives in the package
``foo.bar.awesome`` and you want to give it the alias ``awesome``, add this line to your project's
``setup.py`` under the ``entrypoints`` argument in the ``asphalt.mailer.mailers`` namespace:

.. code-block:: python

    setup(
        # (...other arguments...)
        entry_points={
            'asphalt.mailer.mailers': [
                'awesome = foo.bar.awesome:AwesomeMailer'
            ]
        }
    )
