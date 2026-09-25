from django.contrib import admin

from .models import Connection, ConnectionRequest


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "created_at")
    list_select_related = ("sender__user", "recipient__user")
    raw_id_fields = ("sender", "recipient")


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ("lawyer_a", "lawyer_b", "created_at")
    list_select_related = ("lawyer_a__user", "lawyer_b__user")
    raw_id_fields = ("lawyer_a", "lawyer_b")
