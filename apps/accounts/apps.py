from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    label = "accounts"

    def ready(self) -> None:
        from django.urls import register_converter

        from .converters import HandleConverter

        # URL converters live in one global registry, so register exactly once.
        register_converter(HandleConverter, "handle")
