from __future__ import annotations

import os
import sys
from email.message import EmailMessage
from pathlib import Path

import pytest

from asphalt.mailer import DeliveryError, Mailer
from asphalt.mailer.mailers.sendmail import SendmailMailer

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skipif(
        os.name == "nt", reason="subprocesses don't work with WindowsSelectorEventLoop"
    ),
]


@pytest.fixture
def outfile(tmp_path: Path) -> Path:
    return tmp_path / "outfile"


@pytest.fixture
def script(tmp_path: Path, recipients: tuple[str, ...], outfile: Path) -> str:
    p = tmp_path / "sendmail"
    p.write_text(
        f"""\
#!{sys.executable}
import sys

if sys.argv[1:] != ['-i', '-B', '8BITMIME'] + list({recipients!r}):
    print('Wrong arguments; got {{!r}}'.format(sys.argv), file=sys.stderr)
    sys.exit(1)

with open({str(outfile)!r}, 'w') as f:
    f.write(sys.stdin.read())
"""
    )
    p.chmod(0o555)
    return str(p)


@pytest.fixture
def fail_script(tmp_path: Path) -> str:
    p = tmp_path / "sendmail"
    p.write_text(
        f"""\
#!{sys.executable}
import sys

print('This is a test error', file=sys.stderr)
sys.exit(1)

"""
    )
    p.chmod(0o555)
    return str(p)


@pytest.fixture
def mailer() -> SendmailMailer:
    return SendmailMailer()


@pytest.mark.parametrize("as_list", [True, False])
async def test_deliver(
    mailer: SendmailMailer,
    script: str,
    outfile: Path,
    as_list: bool,
    sample_message: EmailMessage,
    recipients: tuple[str, ...],
) -> None:
    mailer.path = script
    await mailer.deliver([sample_message] if as_list else sample_message)
    assert (
        outfile.read_text()
        == """\
From: foo@bar.baz
To: Test Recipient <test@domain.country>, test2@domain.country
Cc: Test CC <testcc@domain.country>, testcc2@domain.country
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit
MIME-Version: 1.0

Test content
"""
    )


async def test_deliver_launch_error(
    mailer: SendmailMailer, sample_message: EmailMessage
) -> None:
    mailer.path = "/bogus/no/way/this/exists"
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    assert exc.match(
        r"^error sending mail message: \[Errno 2\] No such file or directory: "
    )


async def test_deliver_error(
    mailer: SendmailMailer, sample_message: EmailMessage, fail_script: str
) -> None:
    mailer.path = fail_script
    with pytest.raises(DeliveryError) as exc:
        await mailer.deliver(sample_message)

    assert exc.match("^error sending mail message: This is a test error")


def test_repr(mailer: Mailer) -> None:
    assert repr(mailer) == "SendmailMailer('/usr/sbin/sendmail')"
