from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.utils.translation import gettext_lazy as _

app_name = "accounts"

FORM_PAGE = "accounts/form_page.html"
MESSAGE_PAGE = "accounts/message_page.html"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Password change (logged-in users)
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name=FORM_PAGE,
            success_url=reverse_lazy("accounts:password_change_done"),
            extra_context={"heading": _("Change password"), "submit_label": _("Change password")},
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name=MESSAGE_PAGE,
            extra_context={
                "heading": _("Password changed"),
                "message": _("Your password has been updated."),
            },
        ),
        name="password_change_done",
    ),
    # Password reset (anonymous users)
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name=FORM_PAGE,
            email_template_name="accounts/email/password_reset.txt",
            subject_template_name="accounts/email/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
            extra_context={"heading": _("Reset password"), "submit_label": _("Send reset link")},
        ),
        name="password_reset",
    ),
    path(
        "password/reset/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name=MESSAGE_PAGE,
            extra_context={
                "heading": _("Check your email"),
                "message": _(
                    "If an account exists for that address, we've sent a link to reset "
                    "the password."
                ),
            },
        ),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name=FORM_PAGE,
            success_url=reverse_lazy("accounts:password_reset_complete"),
            extra_context={"heading": _("Choose a new password"), "submit_label": _("Save")},
        ),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name=MESSAGE_PAGE,
            extra_context={
                "heading": _("Password reset"),
                "message": _("Your password has been set. You can log in now."),
            },
        ),
        name="password_reset_complete",
    ),
]
