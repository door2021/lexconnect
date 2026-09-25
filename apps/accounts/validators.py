import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")

RESERVED_HANDLES = frozenset(
    {
        "about",
        "accounts",
        "admin",
        "api",
        "feed",
        "groups",
        "help",
        "lexconnect",
        "login",
        "logout",
        "media",
        "messages",
        "notifications",
        "root",
        "search",
        "settings",
        "signup",
        "static",
        "support",
        "verify",
    }
)


def validate_handle(value: str) -> None:
    if not HANDLE_PATTERN.fullmatch(value):
        raise ValidationError(
            _("Use 3–30 characters: letters, numbers or underscores."),
            code="invalid_handle",
        )
    if value.lower() in RESERVED_HANDLES:
        raise ValidationError(_("This handle is reserved."), code="reserved_handle")
