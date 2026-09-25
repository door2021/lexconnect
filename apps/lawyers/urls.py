from django.urls import path

from .views import SignupView

app_name = "lawyers"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
]
