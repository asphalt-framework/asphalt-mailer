import sys

import os
import pytest

from asphalt.mailer.api import DeliveryError
from asphalt.mailer.mailers.sendmail import SendmailMailer

pytestmark = pytest.mark.skipif(os.name == 'nt',
                                reason="subprocesses don't work with WindowsSelectorEventLoop")


@pytest.fixture
def outfile(tmpdir):
    return tmpdir.join('outfile')


@pytest.fixture
def script(tmpdir, recipients, outfile):
    p = tmpdir.join('sendmail')
    p.write("""\
#!{interpreter}
import sys

if sys.argv[1:] != ['-i', '-B', '8BITMIME'] + list({recipients!r}):
    print('Wrong arguments; got {{!r}}'.format(sys.argv), file=sys.stderr)
    sys.exit(1)

with open({outfile!r}, 'w') as f:
    f.write(sys.stdin.read())
""".format(interpreter=sys.executable, recipients=recipients, outfile=str(outfile)))
    p.chmod(0o555)
    return str(p)


@pytest.fixture
def fail_script(tmpdir):
    p = tmpdir.join('sendmail')
    p.write("""\
#!{interpreter}
import sys

print('This is a test error', file=sys.stderr)
sys.exit(1)

""".format(interpreter=sys.executable))
    p.chmod(0o555)
    return str(p)


@pytest.fixture
def mailer():
    return SendmailMailer()


@pytest.mark.parametrize('as_list', [True, False])
@pytest.mark.asyncio
async def test_deliver(mailer, script, outfile, as_list, sample_message, recipients):
    mailer.path = script
    await mailer.deliver([sample_message] if as_list else sample_message)
    assert outfile.read() == """\
From: foo@bar.baz
To: Test Recipient <test@domain.country>, test2@domain.country
Cc: Test CC <testcc@domain.country>, testcc2@domain.country
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit
MIME-Version: 1.0

Test content
"""


@pytest.mark.asyncio
async def test_deliver_launch_error(mailer, sample_message):
    mailer.path = '/bogus/no/way/this/exists'
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    assert exc.match(r"^error sending mail message: \[Errno 2\] No such file or directory: ")


@pytest.mark.asyncio
async def test_deliver_error(mailer, sample_message, fail_script):
    mailer.path = fail_script
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    assert exc.match('^error sending mail message: This is a test error')


def test_repr(mailer):
    assert repr(mailer) == "SendmailMailer('/usr/sbin/sendmail')".format()
