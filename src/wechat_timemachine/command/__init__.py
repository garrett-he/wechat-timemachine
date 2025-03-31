from .extract_contacts import register_commands as _register_extract_contacts
from .extract_messages import register_commands as _register_extract_messages


def register_all_commands(app) -> None:
    _register_extract_contacts(app)
    _register_extract_messages(app)
