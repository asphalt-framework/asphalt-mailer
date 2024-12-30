from asphalt.core import Component


class ApplicationComponent(Component):
    def __init__(self) -> None:
        self.add_component(
            "mailer",
            backend="smtp",
            host="primary-smtp.company.com",
            username="foo",
            password="bar",
        )
