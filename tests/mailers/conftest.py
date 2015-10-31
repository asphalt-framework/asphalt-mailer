from email.message import EmailMessage

import pytest


@pytest.fixture
def sample_message():
    msg = EmailMessage()
    msg['From'] = 'foo@bar.baz'
    msg['To'] = 'Test Recipient <test@domain.country>, test2@domain.country'
    msg['Cc'] = 'Test CC <testcc@domain.country>, testcc2@domain.country'
    msg['Bcc'] = 'Test BCC <testbcc@domain.country>, testbcc2@domain.country'
    msg.set_content('Test content')
    return msg


@pytest.fixture
def recipients():
    return ('test@domain.country', 'test2@domain.country',
            'testcc@domain.country', 'testcc2@domain.country',
            'testbcc@domain.country', 'testbcc2@domain.country')
