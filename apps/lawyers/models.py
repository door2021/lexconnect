from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Jurisdiction(models.Model):
    """A licensing body, e.g. a provincial bar council."""

    code = models.SlugField(_("code"), max_length=30, unique=True)
    name = models.CharField(_("name"), max_length=120)
    country = models.CharField(_("country code"), max_length=2, default="PK")
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("jurisdiction")
        verbose_name_plural = _("jurisdictions")

    def __str__(self) -> str:
        return self.name


class VerificationLevel(models.TextChoices):
    UNVERIFIED = "unverified", _("Unverified")
    PENDING = "pending", _("Pending")
    VERIFIED = "verified", _("Verified")


class LawyerProfileQuerySet(models.QuerySet):
    def verified(self):
        return self.filter(
            Exists(
                BarAdmission.objects.filter(
                    lawyer=OuterRef("pk"), status=BarAdmission.Status.VERIFIED
                )
            )
        )


class LawyerProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lawyer_profile",
    )
    headline = models.CharField(_("headline"), max_length=160, blank=True)
    bio = models.TextField(_("bio"), blank=True)
    city = models.CharField(_("city"), max_length=80, blank=True)

    objects = LawyerProfileQuerySet.as_manager()

    class Meta:
        verbose_name = _("lawyer profile")
        verbose_name_plural = _("lawyer profiles")

    def __str__(self) -> str:
        return f"{self.user.name} ({self.user})"

    @property
    def verification_level(self) -> str:
        statuses = {admission.status for admission in self.admissions.all()}
        if BarAdmission.Status.VERIFIED in statuses:
            return VerificationLevel.VERIFIED
        if BarAdmission.Status.PENDING in statuses:
            return VerificationLevel.PENDING
        return VerificationLevel.UNVERIFIED

    @property
    def is_verified(self) -> bool:
        return self.verification_level == VerificationLevel.VERIFIED


class BarAdmission(TimeStampedModel):
    """One enrollment of a lawyer with one licensing body."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        VERIFIED = "verified", _("Verified")
        REJECTED = "rejected", _("Rejected")

    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name="admissions")
    jurisdiction = models.ForeignKey(Jurisdiction, on_delete=models.PROTECT)
    license_number = models.CharField(_("license number"), max_length=50)
    status = models.CharField(_("status"), max_length=10, choices=Status, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    reviewed_at = models.DateTimeField(_("reviewed at"), null=True, blank=True)
    rejection_reason = models.CharField(_("rejection reason"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("bar admission")
        verbose_name_plural = _("bar admissions")
        constraints = [
            models.UniqueConstraint(
                fields=["lawyer", "jurisdiction"],
                name="lawyers_one_admission_per_jurisdiction",
            ),
            models.UniqueConstraint(
                fields=["jurisdiction", "license_number"],
                condition=models.Q(status="verified"),
                name="lawyers_unique_verified_license",
            ),
            models.CheckConstraint(
                condition=models.Q(status="pending") | models.Q(reviewed_at__isnull=False),
                name="lawyers_reviewed_admission_has_timestamp",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.jurisdiction} #{self.license_number} ({self.get_status_display()})"
