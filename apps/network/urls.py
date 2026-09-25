from django.urls import path

from . import views
from .views import ACTIONS

app_name = "network"

urlpatterns = [
    path("", views.NetworkView.as_view(), name="index"),
    path("search/", views.SearchView.as_view(), name="search"),
    *[
        path(
            f"@<handle:handle>/{action}/",
            views.ConnectionActionView.as_view(action=action),
            name=action,
        )
        for action in ACTIONS
    ],
]
