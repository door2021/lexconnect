import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()
PASSWORD = "a-Strong-pass-123"


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="Farid@Example.COM", password=PASSWORD, handle="Farid_Law", name="Farid Khan"
    )


def test_email_and_handle_are_stored_lowercase(user):
    assert user.email == "farid@example.com"
    assert user.handle == "farid_law"
    assert str(user) == "@farid_law"


def test_login_is_case_insensitive(user):
    assert authenticate(username="FARID@example.com", password=PASSWORD) == user


def test_handle_unique_regardless_of_case(user):
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            email="other@example.com", password=PASSWORD, handle="FARID_LAW", name="Other"
        )


def test_database_rejects_uppercase_that_bypasses_save(user):
    with pytest.raises(IntegrityError):
        User.objects.filter(pk=user.pk).update(handle="Farid_Law")


@pytest.mark.parametrize("handle", ["ab", "has space", "dash-ed", "x" * 31, "Admin"])
def test_invalid_or_reserved_handles_fail_validation(db, handle):
    candidate = User(email="new@example.com", handle=handle, name="New Lawyer")
    candidate.set_password(PASSWORD)
    with pytest.raises(ValidationError) as exc:
        candidate.full_clean()
    assert "handle" in exc.value.message_dict


def test_create_superuser_sets_flags(db):
    admin = User.objects.create_superuser(
        email="admin@example.com", password=PASSWORD, handle="site_owner", name="Owner"
    )
    assert admin.is_staff and admin.is_superuser
