# forms.py
from django.contrib.auth import forms as auth_forms

from .models import User


class UserAdminCreationForm(auth_forms.AdminUserCreationForm):
    class Meta(auth_forms.AdminUserCreationForm.Meta):
        model = User
        fields = ("email", "handle", "name")


class UserAdminChangeForm(auth_forms.UserChangeForm):
    class Meta(auth_forms.UserChangeForm.Meta):
        model = User
        fields = "__all__"
