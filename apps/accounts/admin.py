# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    ordering = ("email",)
    list_display = ("email", "handle", "name", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "handle", "name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Identity"), {"fields": ("handle", "name")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "handle", "name", "usable_password", "password1", "password2"),
            },
        ),
    )
