import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.lawyers.models import BarAdmission, Jurisdiction, LawyerProfile, VerificationLevel
from apps.lawyers.services import (
    approve_admission,
    register_lawyer,
    reject_admission,
    submit_bar_admission,
)

User = get_user_model()
PASSWORD = "a-Strong-pass-123"


@pytest.fixture
def kp(db):
    return Jurisdiction.objects.get(code="pk-kp")


@pytest.fixture
def reviewer(db):
    return User.objects.create_superuser(
        email="admin@example.com", password=PASSWORD, handle="reviewer", name="Reviewer"
    )


def make_lawyer(n, **bar):
    return register_lawyer(
        email=f"lawyer{n}@example.com",
        password=PASSWORD,
        handle=f"lawyer_{n}",
        name=f"Lawyer {n}",
        **bar,
    )


def test_pakistan_councils_are_seeded(db):
    assert Jurisdiction.objects.filter(country="PK").count() == 6


def test_signup_without_bar_details_is_unverified(db):
    profile = make_lawyer(1)
    assert profile.verification_level == VerificationLevel.UNVERIFIED


def test_signup_with_bar_details_is_pending_not_verified(kp):
    profile = make_lawyer(1, jurisdiction=kp, license_number=" KP-1234 ")
    assert profile.verification_level == VerificationLevel.PENDING
    assert profile.admissions.get().license_number == "KP-1234"


def test_partial_bar_details_rejected_and_nothing_saved(kp):
    with pytest.raises(ValidationError):
        make_lawyer(1, jurisdiction=kp)
    assert not User.objects.filter(email="lawyer1@example.com").exists()


def test_superuser_gets_no_lawyer_profile(reviewer):
    assert not LawyerProfile.objects.filter(user=reviewer).exists()


def test_approval_verifies_profile(kp, reviewer):
    profile = make_lawyer(1, jurisdiction=kp, license_number="KP-1")
    approve_admission(admission=profile.admissions.get(), reviewer=reviewer)
    assert profile.is_verified
    assert LawyerProfile.objects.verified().filter(pk=profile.pk).exists()


def test_two_people_can_claim_but_only_one_can_be_verified(kp, reviewer):
    real = make_lawyer(1, jurisdiction=kp, license_number="KP-1")
    impostor = make_lawyer(2, jurisdiction=kp, license_number="KP-1")
    approve_admission(admission=real.admissions.get(), reviewer=reviewer)
    with pytest.raises(ValidationError, match="already verified"):
        approve_admission(admission=impostor.admissions.get(), reviewer=reviewer)
    assert impostor.admissions.get().status == BarAdmission.Status.PENDING


def test_only_pending_can_be_reviewed(kp, reviewer):
    admission = make_lawyer(1, jurisdiction=kp, license_number="KP-1").admissions.get()
    reject_admission(admission=admission, reviewer=reviewer, reason="Not found")
    with pytest.raises(ValidationError):
        approve_admission(admission=admission, reviewer=reviewer)


def test_rejected_only_profile_is_unverified(kp, reviewer):
    profile = make_lawyer(1, jurisdiction=kp, license_number="KP-1")
    reject_admission(admission=profile.admissions.get(), reviewer=reviewer, reason="No")
    assert profile.verification_level == VerificationLevel.UNVERIFIED


def test_one_admission_per_council(kp):
    profile = make_lawyer(1, jurisdiction=kp, license_number="KP-1")
    with pytest.raises(ValidationError):
        submit_bar_admission(profile=profile, jurisdiction=kp, license_number="KP-2")


def test_db_requires_timestamp_on_reviewed_admission(kp):
    admission = make_lawyer(1, jurisdiction=kp, license_number="KP-1").admissions.get()
    with pytest.raises(IntegrityError):
        BarAdmission.objects.filter(pk=admission.pk).update(status="verified")
