from email.message import EmailMessage

from asphalt.mailer import get_recipients


def test_get_recipients() -> None:
    msg = EmailMessage()
    msg["To"] = "Foo Example <foo@example.org>"
    msg["Cc"] = "Bar Bar <bar@bar.bar>"
    msg["Bcc"] = "Invisible Recipient <invisible@reci.pient>"

    assert get_recipients(msg) == [
        "foo@example.org",
        "bar@bar.bar",
        "invisible@reci.pient",
    ]
