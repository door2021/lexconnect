import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.lawyers.models import Jurisdiction, VerificationLevel

User = get_user_model()
URL = reverse("lawyers:signup")


def payload(**overrides):
    data = {
        "name": "Ayesha Siddiqui",
        "handle": "Ayesha_Adv",
        "email": "Ayesha@Example.com",
        "password1": "Correct-Horse-42",
        "password2": "Correct-Horse-42",
        "jurisdiction": "",
        "license_number": "",
    }
    data.update(overrides)
    return data


def test_signup_page_renders(client, db):
    response = client.get(URL)
    assert response.status_code == 200
    assert b"Bar details" in response.content


def test_signup_creates_unverified_lawyer_and_logs_in(client, db):
    response = client.post(URL, payload())
    assert response.status_code == 302
    user = User.objects.get(email="ayesha@example.com")
    assert user.lawyer_profile.verification_level == VerificationLevel.UNVERIFIED
    assert client.get(reverse("home")).context["user"] == user


def test_signup_with_bar_details_is_pending(client, db):
    kp = Jurisdiction.objects.get(code="pk-kp")
    client.post(URL, payload(jurisdiction=kp.pk, license_number="KP-77"))
    profile = User.objects.get(handle="ayesha_adv").lawyer_profile
    assert profile.verification_level == VerificationLevel.PENDING


def test_duplicate_handle_shows_field_error_not_500(client, db):
    client.post(URL, payload())
    client.post(reverse("accounts:logout"))
    response = client.post(URL, payload(email="other@example.com", handle="AYESHA_ADV"))
    assert response.status_code == 200
    assert "handle" in response.context["form"].errors


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"password2": "Different-Horse-42"}, "password2"),
        ({"password1": "ayesha_adv1", "password2": "ayesha_adv1"}, "password1"),
        ({"license_number": "KP-1"}, "jurisdiction"),
        ({"handle": "admin"}, "handle"),
    ],
)
def test_signup_validation_errors(client, db, overrides, field):
    response = client.post(URL, payload(**overrides))
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert not User.objects.exists()


def test_bar_council_without_number_is_rejected(client, db):
    kp = Jurisdiction.objects.get(code="pk-kp")
    response = client.post(URL, payload(jurisdiction=kp.pk))
    assert "license_number" in response.context["form"].errors
