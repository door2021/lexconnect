from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from .managers import UserManager
from .validators import validate_handle


class User(AbstractUser):
    """Authentication identity. Professional data lives on LawyerProfile."""

    username = None
    first_name = None
    last_name = None

    email = models.EmailField(_("email address"), unique=True)
    handle = models.CharField(
        _("handle"),
        max_length=30,
        unique=True,
        validators=[validate_handle],
        help_text=_("Public @handle used in your profile URL."),
    )
    name = models.CharField(_("full name"), max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["handle", "name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email=Lower("email")),
                name="accounts_user_email_lowercase",
            ),
            models.CheckConstraint(
                condition=models.Q(handle=Lower("handle")),
                name="accounts_user_handle_lowercase",
            ),
        ]

    def __str__(self) -> str:
        return f"@{self.handle}"

    def _normalize(self) -> None:
        if self.email:
            self.email = UserManager.normalize_login(self.email)
        if self.handle:
            self.handle = self.handle.lower()

    def clean(self) -> None:
        super().clean()
        self._normalize()

    def save(self, *args, **kwargs) -> None:
        self._normalize()
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.name
