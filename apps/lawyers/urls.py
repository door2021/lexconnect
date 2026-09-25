from django.urls import path, register_converter

from apps.accounts.converters import HandleConverter

from . import views

register_converter(HandleConverter, "handle")

app_name = "lawyers"

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("@<handle:handle>/", views.ProfileDetailView.as_view(), name="profile"),
    path("settings/profile/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("settings/bar/", views.BarAdmissionsView.as_view(), name="bar_admissions"),
    path(
        "settings/bar/<int:pk>/withdraw/",
        views.WithdrawAdmissionView.as_view(),
        name="withdraw_admission",
    ),
]
