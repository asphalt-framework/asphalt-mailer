Testing with mailers
====================

When you test an application that uses asphalt-mailer, you don't want it to actually send any
emails outside of your testing environment. To that end, it is recommended that you use
:class:`~asphalt.mailer.mailers.mock.MockMailer` as the mailer backend in your testing
configuration. This mailer simply stores the sent messages which you can then verify in your test
function:

.. code-block:: python

    from asphalt.core.component import ContainerComponent
    from asphalt.core.context import Context


    @pytest.fixture(scope='session')
    def container():
        container = ContainerComponent()
        container.add_component('mailer', backend='mock')
        return container


    @pytest.fixture
    def context(container, event_loop):
        context = Context()
        event_loop.run_until_complete(container.start(context))
        return context


    @pytest.mark.asyncio
    def test_foo(context):
        # (do something with the application here that should cause a mail to be sent)

        # check that exactly one message was sent, to intended.recipient@example.org
        assert len(context.mailer.messages) == 1
        assert context.mailers.messages[0]['To'] == 'intended.recipient@example.org'

