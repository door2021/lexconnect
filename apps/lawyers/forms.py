from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import validate_handle

from .models import Jurisdiction

User = get_user_model()


class SignupForm(forms.Form):
    name = forms.CharField(label=_("Full name"), max_length=150)
    handle = forms.CharField(
        label=_("Handle"),
        max_length=30,
        validators=[validate_handle],
        help_text=_("Your public @handle. Letters, numbers and underscores."),
    )
    email = forms.EmailField(label=_("Email"))
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    jurisdiction = forms.ModelChoiceField(
        label=_("Bar council"),
        queryset=Jurisdiction.objects.filter(is_active=True),
        required=False,
        empty_label=_("Select your bar council"),
    )
    license_number = forms.CharField(
        label=_("License number"),
        max_length=50,
        required=False,
        help_text=_("Add it now or later. Verified lawyers can message and send referrals."),
    )

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", _("The two passwords don't match."))
        elif password1:
            candidate = User(
                email=cleaned.get("email", ""),
                handle=cleaned.get("handle", ""),
                name=cleaned.get("name", ""),
            )
            try:
                password_validation.validate_password(password1, user=candidate)
            except ValidationError as exc:
                self.add_error("password1", exc)

        jurisdiction = cleaned.get("jurisdiction")
        license_number = cleaned.get("license_number", "").strip()
        if jurisdiction and not license_number:
            self.add_error("license_number", _("Enter the license number for this council."))
        elif license_number and not jurisdiction:
            self.add_error("jurisdiction", _("Select the council that issued this license."))
        return cleaned
