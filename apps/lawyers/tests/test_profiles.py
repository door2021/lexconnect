import pytest
from django.urls import reverse

from apps.lawyers.models import BarAdmission, Jurisdiction
from apps.lawyers.services import register_lawyer, reject_admission

PASSWORD = "Correct-Horse-42"


def lawyer(n, **bar):
    return register_lawyer(
        email=f"l{n}@example.com",
        password=PASSWORD,
        handle=f"lawyer_{n}",
        name=f"Lawyer {n}",
        **bar,
    )


@pytest.fixture
def kp(db):
    return Jurisdiction.objects.get(code="pk-kp")


@pytest.fixture
def me(client, db):
    profile = lawyer(1)
    client.force_login(profile.user)
    return profile


# --- visibility -------------------------------------------------------------


def test_anonymous_visitor_is_sent_to_login(client, db):
    profile = lawyer(1)
    url = reverse("lawyers:profile", args=[profile.user.handle])
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_member_sees_profile_but_not_license_number(client, me, kp):
    other = lawyer(2, jurisdiction=kp, license_number="SECRET-123")
    response = client.get(reverse("lawyers:profile", args=["lawyer_2"]))
    html = response.content.decode()
    assert response.status_code == 200
    assert other.user.name in html
    assert "Khyber Pakhtunkhwa Bar Council" in html
    assert "SECRET-123" not in html


def test_uppercase_handle_redirects_permanently(client, me):
    response = client.get("/@Lawyer_1/")
    assert response.status_code == 301
    assert response.url == "/@lawyer_1/"


def test_staff_without_profile_and_inactive_users_are_404(client, me, django_user_model):
    django_user_model.objects.create_superuser(
        email="a@example.com", password=PASSWORD, handle="site_owner", name="Owner"
    )
    assert client.get("/@site_owner/").status_code == 404
    gone = lawyer(3)
    gone.user.is_active = False
    gone.user.save()
    assert client.get("/@lawyer_3/").status_code == 404


# --- editing ----------------------------------------------------------------


def test_edit_profile_updates_user_and_profile(client, me):
    response = client.post(
        reverse("lawyers:profile_edit"),
        {"name": "Farid Khan", "headline": "Advocate High Court", "city": "Peshawar", "bio": ""},
    )
    assert response.status_code == 302
    me.refresh_from_db()
    me.user.refresh_from_db()
    assert me.user.name == "Farid Khan"
    assert me.city == "Peshawar"


# --- bar admissions ---------------------------------------------------------


def test_add_bar_admission_after_signup(client, me, kp):
    client.post(
        reverse("lawyers:bar_admissions"), {"jurisdiction": kp.pk, "license_number": " KP-5 "}
    )
    admission = me.admissions.get()
    assert (admission.license_number, admission.status) == ("KP-5", BarAdmission.Status.PENDING)


def test_council_already_used_is_not_offered_again(client, me, kp):
    client.post(
        reverse("lawyers:bar_admissions"), {"jurisdiction": kp.pk, "license_number": "KP-5"}
    )
    form = client.get(reverse("lawyers:bar_admissions")).context["form"]
    assert kp not in form.fields["jurisdiction"].queryset


def test_rejected_admission_can_be_withdrawn_and_resubmitted(client, me, kp, django_user_model):
    client.post(
        reverse("lawyers:bar_admissions"), {"jurisdiction": kp.pk, "license_number": "typo"}
    )
    reviewer = django_user_model.objects.create_superuser(
        email="a@example.com", password=PASSWORD, handle="reviewer", name="R"
    )
    reject_admission(admission=me.admissions.get(), reviewer=reviewer, reason="Not found")

    client.post(reverse("lawyers:withdraw_admission", args=[me.admissions.get().pk]))
    assert not me.admissions.exists()
    client.post(
        reverse("lawyers:bar_admissions"), {"jurisdiction": kp.pk, "license_number": "KP-5"}
    )
    assert me.admissions.get().status == BarAdmission.Status.PENDING


def test_cannot_withdraw_someone_elses_admission(client, me, kp):
    other = lawyer(2, jurisdiction=kp, license_number="KP-9")
    admission = other.admissions.get()
    response = client.post(reverse("lawyers:withdraw_admission", args=[admission.pk]))
    assert response.status_code == 404
    assert BarAdmission.objects.filter(pk=admission.pk).exists()


def test_withdraw_requires_post(client, me, kp):
    client.post(
        reverse("lawyers:bar_admissions"), {"jurisdiction": kp.pk, "license_number": "KP-5"}
    )
    url = reverse("lawyers:withdraw_admission", args=[me.admissions.get().pk])
    assert client.get(url).status_code == 405
