from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from .models import BarAdmission, Jurisdiction, LawyerProfile
from .services import approve_admission, reject_admission

DEFAULT_REJECTION_REASON = "Could not be confirmed against bar council records."


@admin.register(Jurisdiction)
class JurisdictionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "country", "is_active")
    list_filter = ("country", "is_active")


class BarAdmissionInline(admin.TabularInline):
    model = BarAdmission
    fk_name = "lawyer"
    extra = 0
    fields = ("jurisdiction", "license_number", "status", "reviewed_at")
    readonly_fields = ("status", "reviewed_at")


@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "created_at")
    search_fields = ("user__name", "user__handle", "user__email")
    list_select_related = ("user",)
    inlines = [BarAdmissionInline]


@admin.register(BarAdmission)
class BarAdmissionAdmin(admin.ModelAdmin):
    list_display = (
        "lawyer",
        "jurisdiction",
        "license_number",
        "status",
        "competing_claims",
        "created_at",
    )
    list_filter = ("status", "jurisdiction")
    search_fields = ("license_number", "lawyer__user__name", "lawyer__user__handle")
    list_select_related = ("lawyer__user", "jurisdiction")
    readonly_fields = ("status", "reviewed_by", "reviewed_at", "created_at", "updated_at")
    actions = ["approve_selected", "reject_selected"]

    def get_queryset(self, request):
        others = (
            BarAdmission.objects.filter(
                jurisdiction=OuterRef("jurisdiction"),
                license_number=OuterRef("license_number"),
            )
            .exclude(pk=OuterRef("pk"))
            .values("jurisdiction")
            .annotate(n=Count("pk"))
            .values("n")
        )
        return super().get_queryset(request).annotate(_competing=Coalesce(Subquery(others), 0))

    @admin.display(description=_("Other claims"), ordering="_competing")
    def competing_claims(self, obj) -> int:
        return obj._competing

    def _run(self, request, queryset, action, done_msg):
        succeeded = 0
        for admission in queryset:
            try:
                action(admission)
                succeeded += 1
            except ValidationError as exc:
                self.message_user(request, f"{admission}: {exc.messages[0]}", messages.ERROR)
        if succeeded:
            self.message_user(request, done_msg % succeeded, messages.SUCCESS)

    @admin.action(description=_("Approve selected admissions"))
    def approve_selected(self, request, queryset):
        self._run(
            request,
            queryset,
            lambda a: approve_admission(admission=a, reviewer=request.user),
            "%d admission(s) approved.",
        )

    @admin.action(description=_("Reject selected admissions"))
    def reject_selected(self, request, queryset):
        self._run(
            request,
            queryset,
            lambda a: reject_admission(
                admission=a, reviewer=request.user, reason=DEFAULT_REJECTION_REASON
            ),
            "%d admission(s) rejected.",
        )
