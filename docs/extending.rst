Writing new mailer backends
===========================

.. py:currentmodule:: asphalt.mailer

If you wish to implement an alternate method of sending email, you can do so by
subclassing the :class:`~Mailer` class. There are two methods implementors typically
override:

* :meth:`~Mailer.start` (optional)
* :meth:`~Mailer.deliver`

The ``start`` method is a coroutine that is called by :class:`~MailerComponent` from its
own :meth:`~asphalt.core.Component.start` method. You can handle any necessary resource
related setup there.

The :meth:`~Mailer.deliver` method must be overridden and needs to:

#. handle both a single :class:`~email.message.EmailMessage` and an iterable of them
#. remove any ``Bcc`` header from each message to avoid revealing the hidden recipients

If you want your mailer to be available as a backend for the :class:`~MailerComponent`,
you need to add the corresponding entry point for it. Suppose your mailer class is named
``AwesomeMailer``, lives in the package ``foo.bar.awesome`` and you want to give it the
alias ``awesome``, add this line to your project's ``pyproject.toml`` under the
``project.entry-points`` key in the ``asphalt.mailer.mailers`` namespace:

.. code-block:: toml

    [project.entry-points."asphalt.mailer.mailers"]
    awesome = "foo.bar.awesome:AwesomeMailer"
