from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import BarAdmission, Jurisdiction, LawyerProfile

User = get_user_model()


@transaction.atomic
def register_lawyer(
    *,
    email: str,
    password: str,
    handle: str,
    name: str,
    jurisdiction: Jurisdiction | None = None,
    license_number: str = "",
) -> LawyerProfile:
    """Create a user and lawyer profile, plus a pending bar admission if details given."""
    license_number = license_number.strip()
    if bool(jurisdiction) != bool(license_number):
        raise ValidationError(_("Provide both bar council and license number, or neither."))

    user = User(email=email, handle=handle, name=name)
    user.set_password(password)
    user.full_clean()
    user.save()

    profile = LawyerProfile.objects.create(user=user)

    if jurisdiction:
        submit_bar_admission(
            profile=profile, jurisdiction=jurisdiction, license_number=license_number
        )
    return profile


def submit_bar_admission(
    *, profile: LawyerProfile, jurisdiction: Jurisdiction, license_number: str
) -> BarAdmission:
    admission = BarAdmission(
        lawyer=profile,
        jurisdiction=jurisdiction,
        license_number=license_number.strip(),
    )
    admission.full_clean()
    admission.save()
    return admission


@transaction.atomic
def approve_admission(*, admission: BarAdmission, reviewer) -> BarAdmission:
    admission = BarAdmission.objects.select_for_update().get(pk=admission.pk)
    if admission.status != BarAdmission.Status.PENDING:
        raise ValidationError(_("Only pending admissions can be approved."))

    admission.status = BarAdmission.Status.VERIFIED
    admission.reviewed_by = reviewer
    admission.reviewed_at = timezone.now()
    admission.rejection_reason = ""
    try:
        with transaction.atomic():
            admission.save()
    except IntegrityError as exc:
        raise ValidationError(
            _("This license number is already verified for another lawyer.")
        ) from exc
    return admission


@transaction.atomic
def reject_admission(*, admission: BarAdmission, reviewer, reason: str) -> BarAdmission:
    admission = BarAdmission.objects.select_for_update().get(pk=admission.pk)
    if admission.status != BarAdmission.Status.PENDING:
        raise ValidationError(_("Only pending admissions can be rejected."))

    admission.status = BarAdmission.Status.REJECTED
    admission.reviewed_by = reviewer
    admission.reviewed_at = timezone.now()
    admission.rejection_reason = reason
    admission.save()
    return admission
